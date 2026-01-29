#!/usr/bin/env python3
"""
Convert DLIS files to LAS format.

Usage:
    python dlis_to_las.py input.dlis output.las
    python dlis_to_las.py input.dlis  # outputs to input.las
    python dlis_to_las.py input.dlis --frame 0 --curves GR NPHI RHOB
    python dlis_to_las.py directory/ --output-dir las_output/
"""

import argparse
from pathlib import Path

import dlisio
import lasio
import numpy as np


def dlis_to_las(
    dlis_path: str,
    las_path: str = None,
    frame_index: int = 0,
    curves: list = None,
    logical_file_index: int = 0,
) -> str:
    """
    Convert DLIS file to LAS format.

    Args:
        dlis_path: Path to input DLIS file
        las_path: Path to output LAS file (default: same name with .las)
        frame_index: Which frame to convert (default: 0)
        curves: List of curve names to include (default: all scalar)
        logical_file_index: Which logical file to use (default: 0)

    Returns:
        Path to created LAS file
    """
    with dlisio.dlis.load(dlis_path) as files:
        logical_files = list(files)

        if logical_file_index >= len(logical_files):
            raise ValueError(
                f"Logical file index {logical_file_index} out of range. "
                f"File has {len(logical_files)} logical files."
            )

        f = logical_files[logical_file_index]

        if frame_index >= len(f.frames):
            raise ValueError(
                f"Frame index {frame_index} out of range. "
                f"File has {len(f.frames)} frames."
            )

        frame = f.frames[frame_index]
        dlis_curves = frame.curves()

        # Create LAS file
        las = lasio.LASFile()

        # Set well header from origin
        if f.origins:
            origin = f.origins[0]
            if origin.well_name:
                las.well["WELL"] = lasio.HeaderItem("WELL", value=origin.well_name)
            if origin.field_name:
                las.well["FLD"] = lasio.HeaderItem("FLD", value=origin.field_name)
            if origin.company:
                las.well["COMP"] = lasio.HeaderItem("COMP", value=origin.company)
            if origin.run_nr:
                las.well["RUN"] = lasio.HeaderItem("RUN", value=str(origin.run_nr))

        # Determine which curves to export
        if curves:
            # Filter to requested curves that exist
            available = set(dlis_curves.dtype.names)
            export_names = [c for c in curves if c in available]
            missing = [c for c in curves if c not in available]
            if missing:
                print(f"Warning: Curves not found: {missing}")
        else:
            # Export all scalar curves
            export_names = []
            for ch in frame.channels:
                data = dlis_curves[ch.name]
                if data.ndim == 1:  # Only scalar curves
                    export_names.append(ch.name)

        # Add curves to LAS
        for channel in frame.channels:
            if channel.name not in export_names:
                continue

            data = dlis_curves[channel.name]

            # Skip multi-dimensional data
            if data.ndim > 1:
                print(f"Skipping array channel: {channel.name} (shape: {data.shape})")
                continue

            # Handle data type conversion
            if np.issubdtype(data.dtype, np.floating):
                data = data.astype(np.float64)
            elif np.issubdtype(data.dtype, np.integer):
                data = data.astype(np.float64)

            las.append_curve(
                channel.name,
                data,
                unit=channel.units or "",
                descr=channel.long_name or "",
            )

        # Set depth range
        if las.curves:
            first_curve = las.curves[0]
            las.well["STRT"] = lasio.HeaderItem(
                "STRT", unit=first_curve.unit, value=first_curve.data[0]
            )
            las.well["STOP"] = lasio.HeaderItem(
                "STOP", unit=first_curve.unit, value=first_curve.data[-1]
            )

            # Calculate step
            if len(first_curve.data) > 1:
                step = np.median(np.diff(first_curve.data))
                las.well["STEP"] = lasio.HeaderItem(
                    "STEP", unit=first_curve.unit, value=step
                )
            else:
                las.well["STEP"] = lasio.HeaderItem("STEP", value=0)

        # Set null value
        las.well["NULL"] = lasio.HeaderItem("NULL", value=-999.25)

        # Determine output path
        if las_path is None:
            las_path = str(Path(dlis_path).with_suffix(".las"))

        las.write(las_path)
        return las_path


def list_frames(dlis_path: str) -> None:
    """List all frames and their channels in a DLIS file."""
    with dlisio.dlis.load(dlis_path) as files:
        for lf_idx, f in enumerate(files):
            print(f"\nLogical File {lf_idx}:")

            if f.origins:
                origin = f.origins[0]
                print(f"  Well: {origin.well_name}")
                print(f"  Field: {origin.field_name}")

            for fr_idx, frame in enumerate(f.frames):
                print(f"\n  Frame {fr_idx}: {frame.name}")
                print(f"    Index: {frame.index_type}")
                print(f"    Range: {frame.index_min} - {frame.index_max}")
                print(f"    Channels ({len(frame.channels)}):")

                for ch in frame.channels:
                    dim = ch.dimension
                    dim_str = f"[{dim[0]}]" if len(dim) == 1 and dim[0] > 1 else ""
                    print(f"      {ch.name}{dim_str}: {ch.units}")


def main():
    parser = argparse.ArgumentParser(description="Convert DLIS to LAS")
    parser.add_argument("input", help="DLIS file or directory")
    parser.add_argument("output", nargs="?", help="Output LAS file")
    parser.add_argument(
        "--frame", "-f", type=int, default=0, help="Frame index to convert (default: 0)"
    )
    parser.add_argument(
        "--logical-file",
        "-l",
        type=int,
        default=0,
        help="Logical file index (default: 0)",
    )
    parser.add_argument(
        "--curves", "-c", nargs="+", help="Specific curves to include"
    )
    parser.add_argument(
        "--output-dir", "-o", help="Output directory for batch conversion"
    )
    parser.add_argument(
        "--list", action="store_true", help="List frames and channels, don't convert"
    )
    args = parser.parse_args()

    input_path = Path(args.input)

    # List mode
    if args.list:
        if input_path.is_file():
            list_frames(str(input_path))
        else:
            print(f"Error: {input_path} not found")
            exit(1)
        return

    # Conversion mode
    if input_path.is_file():
        output = args.output or str(input_path.with_suffix(".las"))
        try:
            result = dlis_to_las(
                str(input_path),
                output,
                frame_index=args.frame,
                curves=args.curves,
                logical_file_index=args.logical_file,
            )
            print(f"Created: {result}")
        except Exception as e:
            print(f"Error converting {input_path}: {e}")
            exit(1)

    elif input_path.is_dir():
        output_dir = Path(args.output_dir) if args.output_dir else input_path
        output_dir.mkdir(parents=True, exist_ok=True)

        success = 0
        failed = 0

        for dlis_file in input_path.glob("*.dlis"):
            las_path = output_dir / dlis_file.with_suffix(".las").name
            try:
                result = dlis_to_las(
                    str(dlis_file),
                    str(las_path),
                    frame_index=args.frame,
                    curves=args.curves,
                    logical_file_index=args.logical_file,
                )
                print(f"Created: {result}")
                success += 1
            except Exception as e:
                print(f"Error converting {dlis_file}: {e}")
                failed += 1

        print(f"\nSummary: {success} converted, {failed} failed")

    else:
        print(f"Error: {input_path} not found")
        exit(1)


if __name__ == "__main__":
    main()
