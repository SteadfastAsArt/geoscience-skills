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
    with segyio.open(src_path, 'r', ignore_geometry=True, strict=False) as src:
        start = trace_range[0] or 0
        end = trace_range[1] or src.tracecount
        trace_indices = list(range(start, min(end, src.tracecount)))

        # Determine sample range
        if time_range:
            time_start, time_end = time_range
            sample_mask = (src.samples >= time_start) & (src.samples <= time_end)
            new_samples = src.samples[sample_mask]
        else:
            sample_mask = np.ones(len(src.samples), dtype=bool)
            new_samples = src.samples

        # Create spec
        spec = segyio.spec()
        spec.samples = new_samples
        spec.tracecount = len(trace_indices)
        spec.format = int(src.format)

        with segyio.create(dst_path, spec) as dst:
            # Copy text header
            dst.text[0] = src.text[0]

            # Copy binary header and update
            dst.bin = src.bin
            dst.bin[segyio.BinField.Samples] = len(new_samples)

            # Copy traces
            for i, src_idx in enumerate(trace_indices):
                trace_data = src.trace[src_idx]
                dst.trace[i] = trace_data[sample_mask]
                dst.header[i] = dict(src.header[src_idx])
                dst.header[i][segyio.TraceField.TRACE_SAMPLE_COUNT] = len(new_samples)

        return len(trace_indices)


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
    Extract subset by inline/crossline ranges.

    Returns:
        Number of traces written
    """
    with segyio.open(src_path, 'r', iline=iline_byte, xline=xline_byte, strict=False) as src:
        if src.ilines is None:
            print("Warning: No geometry detected. Falling back to trace-based extraction.")
            return extract_by_traces(src_path, dst_path, (0, src.tracecount), time_range)

        # Determine inline subset
        if inline_range:
            il_start = inline_range[0] or src.ilines[0]
            il_end = inline_range[1] or src.ilines[-1] + 1
            sel_ilines = [il for il in src.ilines if il_start <= il < il_end]
        else:
            sel_ilines = list(src.ilines)

        # Determine crossline subset
        if xline_range:
            xl_start = xline_range[0] or src.xlines[0]
            xl_end = xline_range[1] or src.xlines[-1] + 1
            sel_xlines = [xl for xl in src.xlines if xl_start <= xl < xl_end]
        else:
            sel_xlines = list(src.xlines)

        # Determine sample range
        if time_range:
            time_start, time_end = time_range
            sample_mask = (src.samples >= time_start) & (src.samples <= time_end)
            new_samples = src.samples[sample_mask]
        else:
            sample_mask = np.ones(len(src.samples), dtype=bool)
            new_samples = src.samples

        # Create spec for 3D output
        spec = segyio.spec()
        spec.sorting = 2  # Inline sorting
        spec.format = int(src.format)
        spec.ilines = sel_ilines
        spec.xlines = sel_xlines
        spec.samples = new_samples

        with segyio.create(dst_path, spec) as dst:
            # Copy text header
            dst.text[0] = src.text[0]

            # Copy and update binary header
            dst.bin = src.bin
            dst.bin[segyio.BinField.Samples] = len(new_samples)

            # Copy traces
            trace_idx = 0
            for il in sel_ilines:
                for xl in sel_xlines:
                    # Get source trace index
                    src_idx = src.iline.index(il) * len(src.xlines) + src.xline.index(xl)

                    trace_data = src.trace[src_idx]
                    dst.trace[trace_idx] = trace_data[sample_mask]

                    # Copy header and update geometry
                    dst.header[trace_idx] = dict(src.header[src_idx])
                    dst.header[trace_idx][segyio.TraceField.INLINE_3D] = il
                    dst.header[trace_idx][segyio.TraceField.CROSSLINE_3D] = xl
                    dst.header[trace_idx][segyio.TraceField.TRACE_SAMPLE_COUNT] = len(new_samples)

                    trace_idx += 1

        return trace_idx


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
        help="Time/depth range in ms (e.g., 500:2000)",
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

    # Parse ranges
    trace_range = parse_range(args.traces) if args.traces else None
    inline_range = parse_range(args.inlines) if args.inlines else None
    xline_range = parse_range(args.xlines) if args.xlines else None
    time_range = parse_range(args.time) if args.time else None

    try:
        if trace_range and not (inline_range or xline_range):
            # Trace-based extraction
            n_traces = extract_by_traces(
                args.input,
                args.output,
                trace_range,
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
            print("Error: Specify --traces or --inlines/--xlines for extraction")
            sys.exit(1)

        print(f"Extracted {n_traces} traces to {args.output}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
