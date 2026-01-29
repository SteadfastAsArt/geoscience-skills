#!/usr/bin/env python3
"""
Inspect SEG-Y file structure and geometry.

Usage:
    python inspect_segy.py <file.sgy>
    python inspect_segy.py <file.sgy> --headers 0 1 2  # Inspect specific traces
    python inspect_segy.py <file.sgy> --text  # Print text header only
"""

import argparse
import sys

import numpy as np
import segyio


def inspect_segy(filepath: str, trace_indices: list = None, text_only: bool = False) -> dict:
    """
    Inspect a SEG-Y file and return detailed information.

    Args:
        filepath: Path to SEG-Y file
        trace_indices: Specific trace indices to inspect headers
        text_only: Only return text header

    Returns:
        dict with file information
    """
    info = {}

    try:
        # First try opening with geometry
        with segyio.open(filepath, 'r', strict=False) as f:
            info['geometry_detected'] = f.ilines is not None
    except Exception:
        info['geometry_detected'] = False

    # Open with ignore_geometry for full inspection
    with segyio.open(filepath, 'r', ignore_geometry=True, strict=False) as f:
        # Text header
        info['text_header'] = f.text[0]

        if text_only:
            return info

        # Basic info
        info['tracecount'] = f.tracecount
        info['samples_per_trace'] = len(f.samples)
        info['sample_interval_ms'] = f.samples[1] - f.samples[0] if len(f.samples) > 1 else 0
        info['time_range_ms'] = (f.samples[0], f.samples[-1])
        info['format_code'] = int(f.format)

        # Binary header info
        info['binary_header'] = {
            'interval_us': f.bin[segyio.BinField.Interval],
            'samples': f.bin[segyio.BinField.Samples],
            'format': f.bin[segyio.BinField.Format],
            'traces_per_ensemble': f.bin[segyio.BinField.Traces],
            'sorting_code': f.bin[segyio.BinField.SortingCode],
        }

        # Scan headers for geometry info
        if f.tracecount > 0:
            # Sample a subset of traces for speed
            n_sample = min(f.tracecount, 1000)
            step = max(1, f.tracecount // n_sample)
            sample_indices = list(range(0, f.tracecount, step))[:n_sample]

            ilines = []
            xlines = []
            cdp_x = []
            cdp_y = []
            offsets = []

            for idx in sample_indices:
                h = f.header[idx]
                ilines.append(h[segyio.TraceField.INLINE_3D])
                xlines.append(h[segyio.TraceField.CROSSLINE_3D])
                cdp_x.append(h[segyio.TraceField.CDP_X])
                cdp_y.append(h[segyio.TraceField.CDP_Y])
                offsets.append(h[segyio.TraceField.offset])

            info['geometry'] = {
                'inline_range': (min(ilines), max(ilines)) if any(ilines) else None,
                'xline_range': (min(xlines), max(xlines)) if any(xlines) else None,
                'unique_inlines': len(set(ilines)),
                'unique_xlines': len(set(xlines)),
                'cdp_x_range': (min(cdp_x), max(cdp_x)) if any(cdp_x) else None,
                'cdp_y_range': (min(cdp_y), max(cdp_y)) if any(cdp_y) else None,
                'offset_range': (min(offsets), max(offsets)) if any(offsets) else None,
            }

            # Coordinate scalar
            scalar = f.header[0][segyio.TraceField.SourceGroupScalar]
            info['geometry']['coordinate_scalar'] = scalar

        # Data statistics (sample first and last trace)
        if f.tracecount > 0:
            trace0 = f.trace[0]
            trace_last = f.trace[f.tracecount - 1]
            all_data = np.concatenate([trace0, trace_last])
            info['data_stats'] = {
                'min': float(np.nanmin(all_data)),
                'max': float(np.nanmax(all_data)),
                'mean': float(np.nanmean(all_data)),
                'has_nan': bool(np.any(np.isnan(all_data))),
            }

        # Detailed header inspection for specific traces
        if trace_indices:
            info['trace_headers'] = {}
            for idx in trace_indices:
                if 0 <= idx < f.tracecount:
                    h = f.header[idx]
                    info['trace_headers'][idx] = {
                        field.name: h[field]
                        for field in segyio.TraceField.enums()
                        if h[field] != 0
                    }

    return info


def print_info(info: dict, verbose: bool = False) -> None:
    """Print inspection results."""

    print("\n" + "=" * 60)
    print("SEG-Y FILE INSPECTION")
    print("=" * 60)

    # Text header
    print("\n--- TEXT HEADER ---")
    print(info['text_header'])

    if 'tracecount' not in info:
        return

    # Basic info
    print("\n--- BASIC INFO ---")
    print(f"Traces:              {info['tracecount']}")
    print(f"Samples per trace:   {info['samples_per_trace']}")
    print(f"Sample interval:     {info['sample_interval_ms']} ms")
    print(f"Time range:          {info['time_range_ms'][0]} - {info['time_range_ms'][1]} ms")
    print(f"Data format:         {info['format_code']} ({format_name(info['format_code'])})")
    print(f"Geometry detected:   {info['geometry_detected']}")

    # Binary header
    print("\n--- BINARY HEADER ---")
    for key, val in info['binary_header'].items():
        print(f"{key}: {val}")

    # Geometry
    if 'geometry' in info:
        print("\n--- GEOMETRY (from header scan) ---")
        geom = info['geometry']
        if geom['inline_range']:
            print(f"Inline range:        {geom['inline_range'][0]} - {geom['inline_range'][1]}")
            print(f"Unique inlines:      {geom['unique_inlines']}")
        if geom['xline_range']:
            print(f"Crossline range:     {geom['xline_range'][0]} - {geom['xline_range'][1]}")
            print(f"Unique crosslines:   {geom['unique_xlines']}")
        if geom['cdp_x_range']:
            print(f"CDP X range:         {geom['cdp_x_range'][0]} - {geom['cdp_x_range'][1]}")
        if geom['cdp_y_range']:
            print(f"CDP Y range:         {geom['cdp_y_range'][0]} - {geom['cdp_y_range'][1]}")
        if geom['offset_range']:
            print(f"Offset range:        {geom['offset_range'][0]} - {geom['offset_range'][1]}")
        print(f"Coordinate scalar:   {geom['coordinate_scalar']}")

    # Data statistics
    if 'data_stats' in info:
        print("\n--- DATA STATISTICS ---")
        stats = info['data_stats']
        print(f"Min value:           {stats['min']:.6g}")
        print(f"Max value:           {stats['max']:.6g}")
        print(f"Mean value:          {stats['mean']:.6g}")
        print(f"Contains NaN:        {stats['has_nan']}")

    # Trace headers
    if 'trace_headers' in info:
        print("\n--- TRACE HEADERS ---")
        for idx, headers in info['trace_headers'].items():
            print(f"\nTrace {idx}:")
            for field, val in sorted(headers.items()):
                print(f"  {field}: {val}")


def format_name(code: int) -> str:
    """Return human-readable format name."""
    formats = {
        1: "IBM 4-byte float",
        2: "4-byte signed integer",
        3: "2-byte signed integer",
        5: "IEEE 4-byte float",
        8: "1-byte signed integer",
    }
    return formats.get(code, "Unknown")


def main():
    parser = argparse.ArgumentParser(description="Inspect SEG-Y file")
    parser.add_argument("file", help="SEG-Y file to inspect")
    parser.add_argument(
        "--headers", "-H",
        nargs="+",
        type=int,
        help="Trace indices to inspect headers",
    )
    parser.add_argument(
        "--text", "-t",
        action="store_true",
        help="Print text header only",
    )
    args = parser.parse_args()

    try:
        info = inspect_segy(args.file, args.headers, args.text)
        print_info(info)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
