#!/usr/bin/env python3
"""Selected GPRPy processing with explicit sampling and NPZ/JSON readback.

SEG-Y is read by segyio; GPRPy has no SEG-Y reader/exporter. Physical units
come from a documented sidecar, never inferred from ambiguous vendor headers.
"""
import argparse
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
import sys

import gprpy.gprpy as gp
import numpy as np


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def positive(value, name):
    if not isinstance(value, (int, float)) or not np.isfinite(value) or value <= 0:
        raise ValueError(f'{name} must be positive and finite')
    return float(value)


def load_profile(source, metadata):
    source = Path(source)
    profile, extra, header, sources = gp.gprpyProfile(), {}, {}, [source]
    if source.suffix.lower() in ('.sgy', '.segy'):
        import segyio
        with segyio.open(str(source), 'r', ignore_geometry=True) as handle:
            data = np.asarray(segyio.tools.collect(handle.trace[:])).T.copy()
            header = {'binary_sample_interval_encoded': int(handle.bin[segyio.BinField.Interval]),
                      'sample_format_code': int(handle.bin[segyio.BinField.Format])}
            fields = {'interval_encoded': segyio.TraceField.TRACE_SAMPLE_INTERVAL,
                      'delay_encoded': segyio.TraceField.DelayRecordingTime,
                      'source_x_encoded': segyio.TraceField.SourceX,
                      'source_y_encoded': segyio.TraceField.SourceY,
                      'coordinate_scalar': segyio.TraceField.SourceGroupScalar,
                      'coordinate_units_code': segyio.TraceField.CoordinateUnits,
                      'trace_identification_code': segyio.TraceField.TraceIdentificationCode}
            extra = {key: np.asarray(handle.attributes(field)[:]).copy() for key, field in fields.items()}
            if (np.any(handle.attributes(segyio.TraceField.TRACE_SAMPLE_COUNT)[:] != data.shape[0])
                    or len(np.unique(extra['interval_encoded'])) != 1
                    or len(np.unique(extra['delay_encoded'])) != 1):
                raise ValueError('Variable trace sampling requires an explicit alignment policy')
            if np.any(extra['trace_identification_code'] != 1):
                raise ValueError('Non-live/unknown trace flags require an explicit exclusion policy')
        profile.data, profile.info, profile.antsep = np.asmatrix(data, dtype=float), header.copy(), None
        for name in ('velocity', 'depth', 'maxTopo', 'minTopo', 'threeD', 'data_pretopo', 'twtt_pretopo'):
            setattr(profile, name, None)
        profile.history.append('SEG-Y amplitudes imported through segyio; physical axes supplied separately')
    elif source.suffix.lower() in ('.rad', '.rd3'):
        source = source.with_suffix('.rad')
        sources = [source, source.with_suffix('.rd3')]
        profile.importdata(str(source))
        data = np.asarray(profile.data).copy()
        extra['native_twtt'] = np.asarray(profile.twtt).copy()
        extra['native_profile_positions'] = np.asarray(profile.profilePos).copy()
        header = {str(k): str(v) for k, v in profile.info.items()}
    else:
        raise ValueError('Helper supports paired .rad/.rd3 and .sgy/.segy; other readers need separate validation')
    if data.ndim != 2 or min(data.shape) < 2 or not np.isfinite(data).all():
        raise ValueError('Require at least two finite samples and traces; never fill missing amplitudes')
    if not metadata.get('source_note'):
        raise ValueError('Metadata must explain sampling/coordinate provenance')
    axes = {'sample_index': np.arange(data.shape[0]), 'trace_index': np.arange(data.shape[1])}
    for interval, origin, key, count in (
        ('sample_interval_ns', 'time_origin_ns', 'twtt_ns', data.shape[0]),
        ('trace_spacing_m', 'profile_origin_m', 'position_m', data.shape[1])):
        if metadata.get(interval) is not None:
            step = positive(metadata[interval], interval)
            offset = metadata.get(origin)
            if offset is None or not np.isfinite(offset):
                raise ValueError(f'Known sampling requires finite {origin}')
            axes[key] = float(offset) + np.arange(count) * step
    # Sample/trace operations remain valid when physical axes are unresolved.
    profile.twtt = axes.get('twtt_ns', axes['sample_index']).astype(float)
    profile.profilePos = axes.get('position_m', axes['trace_index']).astype(float)
    profile.data = np.asmatrix(data, dtype=float)
    profile.initPrevious()
    inputs = [{'name': path.name, 'sha256': digest(path)} for path in sources]
    return profile, data, axes, extra, header, inputs


def process_gpr(source, output_dir, metadata_path, *, dewow_samples=None,
                background_traces=None, gain_power=None, velocity_m_ns=None):
    output = Path(output_dir)
    if output.exists():
        raise ValueError('Use a new output directory to avoid mixed/overwritten results')
    metadata = json.loads(Path(metadata_path).read_text(encoding='utf-8'))
    profile, raw, axes, extra, header, inputs = load_profile(source, metadata)
    steps, snapshots = [], {'raw_amplitude': raw.copy()}
    for window, count, name in ((dewow_samples, raw.shape[0], 'dewow_samples'),
                                 (background_traces, raw.shape[1], 'background_traces')):
        if window is not None and (type(window) is not int or not 1 <= window <= count):
            raise ValueError(f'{name} must be an integer from 1 to {count}')
    if dewow_samples is not None:
        profile.dewow(dewow_samples)
        steps.append({'operation': 'GPRPy.dewow', 'window_samples_argument': dewow_samples,
                      'interior_support_samples': min(raw.shape[0], 2 * int(np.ceil(dewow_samples / 2)) + 1),
                      'edge_rule': 'GPRPy 1.0.14 special edge windows; full-trace argument subtracts DC mean'})
        snapshots['after_dewow'] = np.asarray(profile.data).copy()
    if background_traces is not None:
        profile.remMeanTrace(background_traces)
        steps.append({'operation': 'GPRPy.remMeanTrace', 'ntraces_argument': background_traces,
                      'scope': 'May suppress genuine laterally continuous reflections'})
        snapshots['after_background'] = np.asarray(profile.data).copy()
    if gain_power is not None:
        positive(gain_power, 'gain_power')
        if 'twtt_ns' not in axes or np.any(axes['twtt_ns'] < 0):
            raise ValueError('Time-power gain requires known nonnegative two-way time in ns')
        profile.tpowGain(gain_power)
        steps.append({'operation': 'GPRPy.tpowGain', 'power': gain_power, 'time_unit': 'ns',
                      'scope': 'Display scaling, not calibrated attenuation compensation'})
        snapshots['after_gain'] = np.asarray(profile.data).copy()
    if velocity_m_ns is not None:
        velocity = positive(velocity_m_ns, 'velocity_m_ns')
        if velocity > 0.299792458 or 'twtt_ns' not in axes or np.any(axes['twtt_ns'] < 0):
            raise ValueError('Depth scenario requires known nonnegative time and velocity below vacuum light speed')
        profile.setVelocity(velocity)
        axes['scenario_depth_m'] = np.asarray(profile.depth).copy()
        steps.append({'operation': 'GPRPy.setVelocity', 'velocity_m_ns': velocity,
                      'scope': 'Constant-velocity zero-offset scenario, not measured site depth'})
    processed = np.asarray(profile.data).copy()
    if processed.shape != raw.shape or not np.isfinite(processed).all():
        raise ValueError('Processing changed shape or produced nonfinite amplitudes')
    distribution = importlib.metadata.distribution('gprpy')
    direct_source = distribution.read_text('direct_url.json')
    report = {'schema_version': 1, 'library_version': importlib.metadata.version('gprpy'),
              'library_source': json.loads(direct_source) if direct_source else None,
              'inputs': inputs, 'metadata_sha256': digest(metadata_path), 'sampling': metadata,
              'raw_header': header, 'shape_samples_traces': list(raw.shape), 'operations': steps,
              'gprpy_history': profile.history, 'known_time_ns': 'twtt_ns' in axes,
              'known_profile_m': 'position_m' in axes, 'ground_truth': None,
              'amplitude_units': 'Uncalibrated source digital values; processing changes amplitude interpretation',
              'raw_rms': float(np.sqrt(np.mean(raw.astype(float) ** 2))),
              'processed_rms': float(np.sqrt(np.mean(processed ** 2)))}
    output.mkdir(parents=True)
    archive = output / 'profile.npz'
    np.savez_compressed(archive, processed_amplitude=processed, **snapshots, **axes, **extra)
    report['archive_sha256'] = digest(archive)
    (output / 'processing.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    return report


def read_result(output_dir):
    output = Path(output_dir)
    report = json.loads((output / 'processing.json').read_text())
    if digest(output / 'profile.npz') != report['archive_sha256']:
        raise ValueError('Export checksum mismatch')
    with np.load(output / 'profile.npz', allow_pickle=False) as arrays:
        result = {key: arrays[key].copy() for key in arrays.files}
    if list(result['processed_amplitude'].shape) != report['shape_samples_traces']:
        raise ValueError('Export shape disagrees with metadata')
    return result, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('--metadata', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--dewow-samples', type=int)
    parser.add_argument('--background-traces', type=int)
    parser.add_argument('--gain-power', type=float)
    parser.add_argument('--velocity-m-ns', type=float)
    args = parser.parse_args()
    try:
        process_gpr(args.source, args.output, args.metadata, dewow_samples=args.dewow_samples,
                    background_traces=args.background_traces, gain_power=args.gain_power,
                    velocity_m_ns=args.velocity_m_ns)
        read_result(args.output)
        print(f'Created and verified {args.output}')
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
