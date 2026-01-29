#!/usr/bin/env python3
"""
Merge curves from multiple LAS files into one.

Usage:
    python merge_curves.py file1.las file2.las -o merged.las
    python merge_curves.py *.las -o merged.las --resample 0.5
"""

import argparse
from pathlib import Path

import lasio
import numpy as np
import pandas as pd


def merge_las_files(
    las_paths: list,
    output_path: str,
    resample_step: float = None,
    depth_curve: str = None,
) -> str:
    """
    Merge curves from multiple LAS files.

    Args:
        las_paths: List of input LAS file paths
        output_path: Path for output merged LAS file
        resample_step: If provided, resample all to this depth step
        depth_curve: Name of depth curve (auto-detected if None)

    Returns:
        Path to created LAS file
    """
    dfs = []
    well_info = None
    curve_info = {}

    for path in las_paths:
        las = lasio.read(path)

        # Get first file's well info
        if well_info is None:
            well_info = las.well

        # Store curve metadata
        for curve in las.curves:
            if curve.mnemonic not in curve_info:
                curve_info[curve.mnemonic] = {
                    "unit": curve.unit,
                    "descr": curve.descr,
                }

        df = las.df().reset_index()
        df["_source"] = Path(path).name
        dfs.append(df)

    # Find common depth column
    depth_col = depth_curve
    if depth_col is None:
        for name in ["DEPT", "DEPTH", "MD", "TVD"]:
            if name in dfs[0].columns:
                depth_col = name
                break
        if depth_col is None:
            depth_col = dfs[0].columns[0]

    # Merge all dataframes
    merged = dfs[0].drop("_source", axis=1)
    for df in dfs[1:]:
        df = df.drop("_source", axis=1)
        # Only add curves that don't exist
        new_cols = [c for c in df.columns if c not in merged.columns]
        if new_cols:
            merged = merged.merge(
                df[[depth_col] + new_cols], on=depth_col, how="outer"
            )

    # Sort by depth
    merged = merged.sort_values(depth_col).reset_index(drop=True)

    # Resample if requested
    if resample_step:
        depth_min = merged[depth_col].min()
        depth_max = merged[depth_col].max()
        new_depth = np.arange(depth_min, depth_max, resample_step)

        resampled = pd.DataFrame({depth_col: new_depth})
        for col in merged.columns:
            if col != depth_col:
                resampled[col] = np.interp(
                    new_depth,
                    merged[depth_col].values,
                    merged[col].values,
                    left=np.nan,
                    right=np.nan,
                )
        merged = resampled

    # Create output LAS
    output_las = lasio.LASFile()

    # Copy well info
    for key in well_info.keys():
        output_las.well[key] = well_info[key]

    # Update depth range
    output_las.well["STRT"].value = merged[depth_col].iloc[0]
    output_las.well["STOP"].value = merged[depth_col].iloc[-1]
    if resample_step:
        output_las.well["STEP"].value = resample_step

    # Add curves
    for col in merged.columns:
        info = curve_info.get(col, {"unit": "", "descr": ""})
        output_las.append_curve(
            col, merged[col].values, unit=info["unit"], descr=info["descr"]
        )

    output_las.write(output_path)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Merge curves from multiple LAS files")
    parser.add_argument("files", nargs="+", help="Input LAS files")
    parser.add_argument("-o", "--output", required=True, help="Output LAS file")
    parser.add_argument(
        "--resample", type=float, help="Resample to this depth step"
    )
    parser.add_argument("--depth-curve", help="Name of depth curve")
    args = parser.parse_args()

    # Expand wildcards on Windows
    files = []
    for f in args.files:
        path = Path(f)
        if "*" in f:
            files.extend(Path(".").glob(f))
        elif path.exists():
            files.append(path)

    if len(files) < 2:
        print("Error: Need at least 2 files to merge")
        exit(1)

    result = merge_las_files(
        [str(f) for f in files],
        args.output,
        resample_step=args.resample,
        depth_curve=args.depth_curve,
    )
    print(f"Created: {result}")
    print(f"Merged {len(files)} files")


if __name__ == "__main__":
    main()
