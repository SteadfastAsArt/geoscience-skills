#!/usr/bin/env python3
"""
Merge curves from multiple LAS files into one.

Usage:
    python merge_curves.py file1.las file2.las -o merged.las
    python merge_curves.py *.las -o merged.las --resample 0.5
"""

import argparse
import glob
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

    The first occurrence of a curve wins. Resampling uses that curve's original
    depth grid, preserves original NaN gaps, and does not extrapolate. Input
    depth units must match; unit conversion is not performed.
    """
    if not las_paths:
        raise ValueError("At least one input LAS file is required")
    if resample_step is not None and (
        not np.isfinite(resample_step) or resample_step <= 0
    ):
        raise ValueError("Resample step must be finite and positive")
    destination = Path(output_path)
    for path in las_paths:
        source = Path(path)
        if source.resolve() == destination.resolve() or (
            destination.exists() and source.samefile(destination)
        ):
            raise ValueError("Output must not overwrite an input LAS file")

    dfs = []
    well_info = None
    curve_info = {}
    curve_samples = {}
    depth_col = depth_curve
    depth_unit = None

    for path in las_paths:
        las = lasio.read(path)
        df = las.df().reset_index()
        if df.empty:
            raise ValueError(f"{path}: no depth samples")
        source_depth = depth_curve or df.columns[0]
        if source_depth not in df.columns:
            raise ValueError(f"{path}: depth curve {source_depth!r} not found")
        if depth_col is None:
            depth_col = source_depth
        unit = las.curves[source_depth].unit
        if depth_unit is None:
            depth_unit = unit
        elif unit.strip().casefold() != depth_unit.strip().casefold():
            raise ValueError(f"{path}: depth units {unit!r} do not match {depth_unit!r}")
        if source_depth != depth_col:
            if depth_col in df.columns:
                raise ValueError(f"{path}: conflicting depth curve {depth_col!r}")
            df = df.rename(columns={source_depth: depth_col})
        depth = df[depth_col].to_numpy(dtype=float)
        # lasio can leave the LAS NULL sentinel in the index curve unchanged.
        if not np.isfinite(depth).all() or (depth == las.well["NULL"].value).any():
            raise ValueError(f"{path}: depth samples must be finite and not LAS NULL")
        if df[depth_col].duplicated().any():
            raise ValueError(f"{path}: duplicate depth samples are ambiguous")
        df = df.sort_values(depth_col).reset_index(drop=True)
        # LAS requires its index curve first, including when --depth-curve is used.
        df = df[[depth_col] + [name for name in df.columns if name != depth_col]]

        # Get first file's well info
        if well_info is None:
            well_info = las.well

        # Store curve metadata
        for curve in las.curves:
            name = depth_col if curve.mnemonic == source_depth else curve.mnemonic
            if name not in curve_info:
                curve_info[name] = {
                    "unit": curve.unit,
                    "descr": curve.descr,
                }
                if name != depth_col:
                    curve_samples[name] = (
                        df[depth_col].to_numpy(dtype=float),
                        df[name].to_numpy(dtype=float),
                    )
        dfs.append(df)

    # Merge all dataframes
    merged = dfs[0]
    for df in dfs[1:]:
        # Only add curves that don't exist
        new_cols = [c for c in df.columns if c not in merged.columns]
        if new_cols:
            merged = merged.merge(
                df[[depth_col] + new_cols], on=depth_col, how="outer"
            )

    # Sort by depth
    merged = merged.sort_values(depth_col).reset_index(drop=True)

    # Resample if requested
    if resample_step is not None:
        depth_min = merged[depth_col].min()
        depth_max = merged[depth_col].max()
        intervals = (depth_max - depth_min) / resample_step
        aligned_end = np.isclose(intervals, round(intervals), rtol=0, atol=1e-9)
        if aligned_end:
            intervals = round(intervals)
        new_depth = depth_min + np.arange(int(np.floor(intervals)) + 1) * resample_step
        if aligned_end:
            new_depth[-1] = depth_max

        resampled = pd.DataFrame({depth_col: new_depth})
        for col in merged.columns:
            if col != depth_col:
                original_depth, original_values = curve_samples[col]
                resampled[col] = np.interp(
                    new_depth,
                    original_depth,
                    original_values,
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
    steps = np.diff(merged[depth_col].to_numpy(dtype=float))
    output_las.well["STEP"].value = (
        float(steps[0]) if len(steps) and np.allclose(steps, steps[0]) else 0
    )
    for key in ("STRT", "STOP", "STEP"):
        output_las.well[key].unit = depth_unit

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
        matches = glob.glob(f) if glob.has_magic(f) else [f]
        if not matches:
            parser.error(f"No files match {f!r}")
        for match in matches:
            path = Path(match)
            if not path.is_file():
                parser.error(f"Input LAS file not found: {path}")
            files.append(path)

    if len(files) < 2:
        print("Error: Need at least 2 files to merge")
        exit(1)

    try:
        result = merge_las_files(
            [str(f) for f in files],
            args.output,
            resample_step=args.resample,
            depth_curve=args.depth_curve,
        )
    except Exception as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Created: {result}")
    print(f"Merged {len(files)} files")


if __name__ == "__main__":
    main()
