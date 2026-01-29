#!/usr/bin/env python3
"""
Convert LAS files to CSV format.

Usage:
    python las_to_csv.py input.las output.csv
    python las_to_csv.py input.las  # outputs to input.csv
    python las_to_csv.py directory/ --output-dir csv_output/
"""

import argparse
from pathlib import Path

import lasio
import numpy as np


def las_to_csv(
    las_path: str,
    csv_path: str = None,
    curves: list = None,
    replace_null: bool = True,
) -> str:
    """
    Convert LAS file to CSV.

    Args:
        las_path: Path to input LAS file
        csv_path: Path to output CSV (default: same name with .csv)
        curves: List of curve names to include (default: all)
        replace_null: Replace null values with empty string

    Returns:
        Path to created CSV file
    """
    las = lasio.read(las_path)
    df = las.df().reset_index()

    # Filter curves if specified
    if curves:
        # Always include depth
        depth_col = df.columns[0]
        cols = [depth_col] + [c for c in curves if c in df.columns]
        df = df[cols]

    # Replace null values
    if replace_null:
        null_val = las.well.get("NULL", {}).get("value", -999.25)
        try:
            null_val = float(null_val)
            df = df.replace(null_val, np.nan)
        except (ValueError, TypeError):
            pass

    # Determine output path
    if csv_path is None:
        csv_path = str(Path(las_path).with_suffix(".csv"))

    df.to_csv(csv_path, index=False)
    return csv_path


def main():
    parser = argparse.ArgumentParser(description="Convert LAS to CSV")
    parser.add_argument("input", help="LAS file or directory")
    parser.add_argument("output", nargs="?", help="Output CSV file or directory")
    parser.add_argument(
        "--curves", "-c", nargs="+", help="Specific curves to include"
    )
    parser.add_argument(
        "--keep-null", action="store_true", help="Keep null values as-is"
    )
    parser.add_argument(
        "--output-dir", "-o", help="Output directory for batch conversion"
    )
    args = parser.parse_args()

    input_path = Path(args.input)

    if input_path.is_file():
        output = args.output or str(input_path.with_suffix(".csv"))
        result = las_to_csv(
            str(input_path),
            output,
            curves=args.curves,
            replace_null=not args.keep_null,
        )
        print(f"Created: {result}")

    elif input_path.is_dir():
        output_dir = Path(args.output_dir) if args.output_dir else input_path
        output_dir.mkdir(parents=True, exist_ok=True)

        for las_file in input_path.glob("*.las"):
            csv_path = output_dir / las_file.with_suffix(".csv").name
            result = las_to_csv(
                str(las_file),
                str(csv_path),
                curves=args.curves,
                replace_null=not args.keep_null,
            )
            print(f"Created: {result}")
    else:
        print(f"Error: {input_path} not found")
        exit(1)


if __name__ == "__main__":
    main()
