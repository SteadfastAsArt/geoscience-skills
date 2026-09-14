#!/usr/bin/env python3
"""
Extract a subset of traces from a SEG-Y file.

Usage:
    # Extract traces by index range
    python extract_subset.py input.sgy output.sgy --traces 0:1000

    # Extract by inline range (3D)
    python extract_subset.py input.sgy output.sgy --inlines 100:200

    # Extract by inline and crossline range (3D)
    python extract_subset.py input.sgy output.sgy --inlines 100:200 --xlines 50:150

    # Extract time window
    python extract_subset.py input.sgy output.sgy --time 500:2000
"""

import argparse
from pathlib import Path
import sys

import numpy as np
import segyio


def parse_range(range_str: str) -> tuple:
    """Parse a range string like '100:200' into (start, end)."""
    parts = range_str.split(':')
    if len(parts) == 1:
        val = int(parts[0])
        return (val, val + 1)
    elif len(parts) == 2:
        start = int(parts[0]) if parts[0] else None
        end = int(parts[1]) if parts[1] else None
        return (start, end)
    else:
        raise ValueError(f"Invalid range format: {range_str}")


def _check_output_path(src_path, dst_path):
    source, destination = Path(src_path), Path(dst_path)
    if source.resolve() == destination.resolve() or (
        destination.exists() and source.samefile(destination)
    ):
        raise ValueError("Input and output must be different files")


def _range_mask(values, bounds, *, inclusive_end=False):
    """Select a bounded interval, allowing either end to be omitted."""
    mask = np.ones(len(values), dtype=bool)
    if bounds is None:
        return mask
    start, end = bounds
    for bound in (start, end):
        if bound is not None and not np.isfinite(bound):
            raise ValueError("Range bounds must be finite")
    if start is not None and end is not None and start > end:
        raise ValueError("Range start must not exceed its end")
    if start is not None:
        mask &= values >= start
    if end is not None:
        mask &= values <= end if inclusive_end else values < end
    return mask


def _write_subset(src, dst_path, trace_indices, time_range):
    """Copy selected traces, preserving their order, headers, and time basis."""
    if not len(trace_indices):
        raise ValueError("The selected range contains no traces")
    sample_mask = _range_mask(src.samples, time_range, inclusive_end=True)
    samples = src.samples[sample_mask]
    if not len(samples):
        raise ValueError("The selected time range contains no samples")

    delays = []
    if time_range is not None:
        interval = segyio.tools.dt(src)
        for index in trace_indices:
            header = src.header[int(index)]
            scalar = header[segyio.TraceField.ScalarTraceHeader]
            scale = 1.0 / abs(scalar) if scalar < 0 else scalar or 1
            start = header[segyio.TraceField.DelayRecordingTime] * scale
            if not np.isclose(start, src.samples[0], rtol=0, atol=1e-7):
                raise ValueError("Time cropping requires a common trace start time")
            if header[segyio.TraceField.TRACE_SAMPLE_INTERVAL] not in (0, interval):
                raise ValueError("Time cropping requires a common sample interval")
            delay = samples[0] / scale
            encoded = int(round(delay))
            if not np.isclose(delay, encoded, rtol=0, atol=1e-7) or not (
                -32768 <= encoded <= 32767
            ):
                raise ValueError(
                    "Cropped start time cannot be represented by the source "
                    "DelayRecordingTime and ScalarTraceHeader"
                )
            delays.append(encoded)

    # An unstructured spec preserves arbitrary trace subsets, including offsets.
    # Geometry is inferred from the copied trace headers when the file is reopened.
    spec = segyio.tools.metadata(src)
    spec.ilines = spec.xlines = spec.offsets = None
    spec.tracecount = len(trace_indices)
    spec.samples = samples
    with segyio.create(dst_path, spec) as dst:
        for index in range(src.ext_headers + 1):
            dst.text[index] = src.text[index]
        dst.bin = src.bin
        dst.bin[segyio.BinField.Samples] = len(samples)
        for output_index, source_index in enumerate(trace_indices):
            source_index = int(source_index)
            dst.trace[output_index] = src.trace[source_index][sample_mask]
            dst.header[output_index] = dict(src.header[source_index])
            dst.header[output_index][segyio.TraceField.TRACE_SAMPLE_COUNT] = len(samples)
            if time_range is not None:
                dst.header[output_index][segyio.TraceField.DelayRecordingTime] = delays[output_index]
    return len(trace_indices)


def extract_by_traces(
    src_path: str,
    dst_path: str,
    trace_range: tuple,
    time_range: tuple = None,
) -> int:
    """
    Extract traces by index range.

    Returns:
        Number of traces written
    """
    _check_output_path(src_path, dst_path)
    if any(bound is not None and bound < 0 for bound in trace_range):
        raise ValueError("Trace indices must be nonnegative")
    with segyio.open(src_path, 'r', ignore_geometry=True) as src:
        indices = np.arange(src.tracecount)
        indices = indices[_range_mask(indices, trace_range)]
        return _write_subset(src, dst_path, indices, time_range)


def extract_by_geometry(
    src_path: str,
    dst_path: str,
    inline_range: tuple = None,
    xline_range: tuple = None,
    time_range: tuple = None,
    iline_byte: int = 189,
    xline_byte: int = 193,
) -> int:
    """
    Extract by half-open inline/crossline header ranges.

    Preserve source trace order and every selected offset. Irregular output
    geometry can be read with ``ignore_geometry=True``.

    Returns:
        Number of traces written
    """
    _check_output_path(src_path, dst_path)
    with segyio.open(src_path, 'r', ignore_geometry=True) as src:
        inlines = src.attributes(iline_byte)[:]
        xlines = src.attributes(xline_byte)[:]
        mask = _range_mask(inlines, inline_range) & _range_mask(xlines, xline_range)
        return _write_subset(src, dst_path, np.flatnonzero(mask), time_range)


def main():
    parser = argparse.ArgumentParser(
        description="Extract subset of SEG-Y file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Extract traces 0-999
    python extract_subset.py input.sgy output.sgy --traces 0:1000

    # Extract inlines 100-199
    python extract_subset.py input.sgy output.sgy --inlines 100:200

    # Extract inline/crossline window with time window
    python extract_subset.py input.sgy output.sgy --inlines 100:200 --xlines 50:150 --time 500:2000

    # Specify non-standard header byte locations
    python extract_subset.py input.sgy output.sgy --inlines 100:200 --iline-byte 9 --xline-byte 21
        """,
    )
    parser.add_argument("input", help="Input SEG-Y file")
    parser.add_argument("output", help="Output SEG-Y file")
    parser.add_argument(
        "--traces", "-t",
        help="Trace index range (e.g., 0:1000)",
    )
    parser.add_argument(
        "--inlines", "-i",
        help="Inline range (e.g., 100:200)",
    )
    parser.add_argument(
        "--xlines", "-x",
        help="Crossline range (e.g., 50:150)",
    )
    parser.add_argument(
        "--time",
        help="Inclusive time range in ms (e.g., 500:2000, 500:, or :2000)",
    )
    parser.add_argument(
        "--iline-byte",
        type=int,
        default=189,
        help="Inline header byte location (default: 189)",
    )
    parser.add_argument(
        "--xline-byte",
        type=int,
        default=193,
        help="Crossline header byte location (default: 193)",
    )
    args = parser.parse_args()

    try:
        trace_range = parse_range(args.traces) if args.traces else None
        inline_range = parse_range(args.inlines) if args.inlines else None
        xline_range = parse_range(args.xlines) if args.xlines else None
        time_range = parse_range(args.time) if args.time else None
        if trace_range is not None and (inline_range is not None or xline_range is not None):
            raise ValueError("Use either --traces or --inlines/--xlines, not both")
        if trace_range is not None or (
            time_range is not None and inline_range is None and xline_range is None
        ):
            # Trace-based extraction
            n_traces = extract_by_traces(
                args.input,
                args.output,
                trace_range if trace_range is not None else (None, None),
                time_range,
            )
        elif inline_range or xline_range:
            # Geometry-based extraction
            n_traces = extract_by_geometry(
                args.input,
                args.output,
                inline_range,
                xline_range,
                time_range,
                args.iline_byte,
                args.xline_byte,
            )
        else:
            print("Error: Specify --traces, --inlines/--xlines, or --time for extraction")
            sys.exit(1)

        print(f"Extracted {n_traces} traces to {args.output}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
