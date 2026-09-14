#!/usr/bin/env python3
"""Export one explicitly selected DLIS frame's scalar numeric curves to LAS."""

import argparse
from collections import Counter
from pathlib import Path
import sys

from dlisio import dlis
import lasio
import numpy as np


def _select_channel(channels, key):
    matches = [ch for ch in channels if key in (ch.name, ch.fingerprint)]
    if len(matches) != 1:
        raise ValueError(f"Channel {key!r} matches {len(matches)} objects; use an exact fingerprint")
    return matches[0]


def dlis_to_las(dlis_path, las_path=None, frame_index=0, curves=None,
                logical_file_index=0, depth_channel=None, null_value=None):
    """Preserve depth order/units; exclude arrays unless requested (then fail).

    Channel selections accept a unique mnemonic or a complete DLIS fingerprint.
    ``null_value`` is an optional documented vendor sentinel, not an RP66 default.
    """
    source = Path(dlis_path)
    target = Path(las_path) if las_path is not None else source.with_suffix('.las')
    if source.resolve() == target.resolve() or (source.exists() and target.exists() and source.samefile(target)):
        raise ValueError('Output must not overwrite the input DLIS file')
    if null_value is not None and not np.isfinite(null_value):
        raise ValueError('Vendor null value must be finite')
    with dlis.load(str(source)) as files:
        if not isinstance(logical_file_index, int) or not 0 <= logical_file_index < len(files):
            raise ValueError('Logical file index is outside the available files')
        logical = files[logical_file_index]
        if not isinstance(frame_index, int) or not 0 <= frame_index < len(logical.frames):
            raise ValueError('Frame index is outside the available frames')
        frame = logical.frames[frame_index]
        channels = list(frame.channels)
        records = frame.curves()
        if not records.size:
            raise ValueError('Selected frame contains no samples')
        if depth_channel is not None:
            depth = _select_channel(channels, depth_channel)
        elif frame.index_type in ('BOREHOLE-DEPTH', 'VERTICAL-DEPTH') and channels:
            depth = channels[0]
        else:
            raise ValueError('Frame has no depth index; choose --depth-channel explicitly')
        depth_units = {'m': 'M', 'meter': 'M', 'metre': 'M', 'ft': 'FT', 'foot': 'FT', 'feet': 'FT'}
        depth_unit = depth_units.get(str(depth.units).strip().lower())
        if depth_unit is None:
            raise ValueError(f'Unsupported depth unit {depth.units!r}; convert and document it before LAS export')
        depths = records[depth.fingerprint]
        if depths.ndim != 1 or depths.dtype.kind not in 'biuf':
            raise ValueError('Depth must be a scalar numeric channel')
        depths = depths.astype(float)
        if not np.all(np.isfinite(depths)) or (null_value is not None and np.any(depths == null_value)):
            raise ValueError('Depth contains missing or invalid samples')
        steps = np.diff(depths)
        if steps.size and not (np.all(steps > 0) or np.all(steps < 0)):
            raise ValueError('Depth must be strictly monotonic with no repeated samples')

        selected = [_select_channel(channels, key) for key in curves] if curves else channels
        selected = [depth] + [ch for ch in selected if ch.fingerprint != depth.fingerprint]
        seen = set()
        counts = Counter(ch.name for ch in channels)
        las = lasio.LASFile()
        if logical.origins:
            origin = logical.origins[0]
            for key, attribute in [('WELL', 'well_name'), ('FLD', 'field_name'), ('COMP', 'company'), ('RUN', 'run_nr')]:
                value = getattr(origin, attribute, None)
                if value is not None:
                    las.well[key] = lasio.HeaderItem(key, value=str(value))
        for channel in selected:
            if channel.fingerprint in seen:
                continue
            seen.add(channel.fingerprint)
            data = records[channel.fingerprint]
            if data.ndim != 1 or data.dtype.kind not in 'biuf':
                message = f'Cannot represent channel {channel.fingerprint} with shape {data.shape} and dtype {data.dtype} in scalar LAS'
                if curves:
                    raise ValueError(message)
                print(message, file=sys.stderr)
                continue
            values = data.astype(float)
            if null_value is not None:
                values[values == null_value] = np.nan
            values[~np.isfinite(values)] = np.nan
            name = channel.name
            if counts[name] > 1:
                name = f'{name}__O{channel.origin}_C{channel.copynumber}'
            # LAS uses a dot between mnemonic and unit; avoid an ambiguous file.
            name = name.replace('.', '_').replace(' ', '_')
            if name in las.keys():
                raise ValueError(f'LAS mnemonic collision after normalization: {name}')
            unit = depth_unit if channel.fingerprint == depth.fingerprint else str(channel.units or '')
            description = f'DLIS {channel.fingerprint}'
            las.append_curve(name, values, unit=unit, descr=description)
        if len(las.curves) < 1:
            raise ValueError('No numeric curves to export')
        las.well.STRT = lasio.HeaderItem('STRT', unit=depth_unit, value=depths[0])
        las.well.STOP = lasio.HeaderItem('STOP', unit=depth_unit, value=depths[-1])
        step = steps[0] if steps.size and np.allclose(steps, steps[0], rtol=1e-7, atol=1e-9) else 0.0
        las.well.STEP = lasio.HeaderItem('STEP', unit=depth_unit, value=step)
        for sentinel in (-999.25, -9999.25, -1e30):
            if not any(np.any(np.isclose(curve.data, sentinel, rtol=1e-9, atol=1e-10))
                       for curve in las.curves):
                break
        else:
            raise ValueError('No collision-free LAS null sentinel found')
        las.well.NULL = lasio.HeaderItem('NULL', value=sentinel)
        las.other = (f'Selected logical file {logical_file_index}; frame {frame.fingerprint}; '
                     f'depth {depth.fingerprint}; vendor null marker {null_value!r}. '
                     'Array channels require a separate lossless export.')
        las.write(str(target), version=2.0, fmt='%.17g',
                  STRT=depths[0], STOP=depths[-1], STEP=step)
    return str(target)


def list_frames(dlis_path):
    with dlis.load(str(dlis_path)) as files:
        for lf_index, logical in enumerate(files):
            print(f'Logical file {lf_index}:')
            for frame_index, frame in enumerate(logical.frames):
                print(f'  Frame {frame_index}: {frame.fingerprint}, index={frame.index!r}, type={frame.index_type!r}')
                for channel in frame.channels:
                    print(f'    {channel.fingerprint}: units={channel.units!r}, dimension={channel.dimension}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', help='DLIS file or directory')
    parser.add_argument('output', nargs='?', help='Output LAS path for a single input')
    parser.add_argument('--frame', '-f', type=int, default=0)
    parser.add_argument('--logical-file', '-l', type=int, default=0)
    parser.add_argument('--curves', '-c', nargs='+', help='Unique mnemonics or complete fingerprints; depth is always included')
    parser.add_argument('--depth-channel', help='Explicit depth channel for a non-depth-indexed frame')
    parser.add_argument('--null-value', type=float, help='Documented vendor sentinel to convert to NaN')
    parser.add_argument('--output-dir', '-o')
    parser.add_argument('--list', action='store_true')
    args = parser.parse_args()
    source = Path(args.input)
    try:
        if args.list:
            if not source.is_file():
                raise ValueError('--list requires a DLIS file')
            list_frames(source)
            return 0
        if source.is_file():
            if args.output_dir:
                raise ValueError('--output-dir applies only to directory inputs')
            sources = [source]
            targets = [Path(args.output) if args.output else source.with_suffix('.las')]
        elif source.is_dir():
            if args.output:
                raise ValueError('A positional output applies only to a single input file')
            sources = sorted(p for p in source.iterdir() if p.is_file() and p.suffix.lower() == '.dlis')
            if not sources:
                raise ValueError('No DLIS files found in directory')
            output_dir = Path(args.output_dir) if args.output_dir else source
            output_dir.mkdir(parents=True, exist_ok=True)
            targets = [output_dir / p.with_suffix('.las').name for p in sources]
            if len({p.resolve() for p in targets}) != len(targets):
                raise ValueError('Input names map to duplicate LAS output paths')
        else:
            raise ValueError(f'Input does not exist: {source}')
        failed = 0
        for input_path, output_path in zip(sources, targets):
            try:
                result = dlis_to_las(input_path, output_path, args.frame, args.curves,
                                     args.logical_file, args.depth_channel, args.null_value)
                print(f'Created: {result}')
            except (ValueError, RuntimeError, OSError) as error:
                print(f'Error converting {input_path}: {error}', file=sys.stderr)
                failed += 1
        return 1 if failed else 0
    except (ValueError, RuntimeError, OSError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
