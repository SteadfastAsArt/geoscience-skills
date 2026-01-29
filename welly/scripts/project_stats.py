#!/usr/bin/env python3
"""
Compute project-level statistics across multiple wells.

Usage:
    python project_stats.py <directory>
    python project_stats.py <directory> --curves GR RHOB NPHI
    python project_stats.py <directory> --output stats.csv
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from welly import Well


def compute_well_stats(filepath: str, curves: list = None) -> dict:
    """
    Compute statistics for a single well.

    Args:
        filepath: Path to LAS file
        curves: List of curve names to analyze (default: all)

    Returns:
        dict with well statistics
    """
    try:
        w = Well.from_las(filepath)
    except Exception as e:
        return {"path": filepath, "error": str(e)}

    stats = {
        "path": filepath,
        "name": w.name or Path(filepath).stem,
        "uwi": w.uwi or "",
        "n_curves": len(w.data),
        "curves_available": ", ".join(w.data.keys()),
    }

    # Get depth info from first curve
    if len(w.data) > 0:
        first_curve = list(w.data.values())[0]
        stats["depth_start"] = first_curve.start
        stats["depth_stop"] = first_curve.stop
        stats["depth_range"] = first_curve.stop - first_curve.start
        stats["depth_step"] = first_curve.step
        stats["n_samples"] = len(first_curve.values)

    # Determine which curves to analyze
    curves_to_analyze = curves if curves else list(w.data.keys())

    for curve_name in curves_to_analyze:
        if curve_name not in w.data:
            continue

        curve = w.data[curve_name]
        values = curve.values
        valid = values[~np.isnan(values)]

        if len(valid) == 0:
            continue

        prefix = curve_name.lower()
        stats[f"{prefix}_min"] = float(valid.min())
        stats[f"{prefix}_max"] = float(valid.max())
        stats[f"{prefix}_mean"] = float(valid.mean())
        stats[f"{prefix}_std"] = float(valid.std())
        stats[f"{prefix}_p10"] = float(np.percentile(valid, 10))
        stats[f"{prefix}_p50"] = float(np.percentile(valid, 50))
        stats[f"{prefix}_p90"] = float(np.percentile(valid, 90))
        stats[f"{prefix}_null_pct"] = 100 * (len(values) - len(valid)) / len(values)

    return stats


def compute_project_summary(well_stats: list, curves: list = None) -> dict:
    """
    Compute aggregate statistics across all wells.

    Args:
        well_stats: List of well statistics dicts
        curves: List of curve names to summarize

    Returns:
        dict with project summary statistics
    """
    df = pd.DataFrame(well_stats)

    summary = {
        "n_wells": len(df),
        "n_wells_valid": len(df[~df.get("error", pd.Series()).notna()]),
    }

    # Aggregate depth info
    if "depth_start" in df.columns:
        summary["depth_start_min"] = df["depth_start"].min()
        summary["depth_stop_max"] = df["depth_stop"].max()
        summary["depth_range_mean"] = df["depth_range"].mean()

    # Determine curves to summarize
    if curves is None:
        # Find all curve columns
        curve_cols = [c for c in df.columns if c.endswith("_mean")]
        curves = [c.replace("_mean", "").upper() for c in curve_cols]

    for curve_name in curves:
        prefix = curve_name.lower()
        mean_col = f"{prefix}_mean"

        if mean_col not in df.columns:
            continue

        # Aggregate statistics across wells
        values = df[mean_col].dropna()
        if len(values) == 0:
            continue

        summary[f"{prefix}_wells_with_curve"] = len(values)
        summary[f"{prefix}_mean_of_means"] = values.mean()
        summary[f"{prefix}_std_of_means"] = values.std()

        # Range across all wells
        if f"{prefix}_min" in df.columns:
            summary[f"{prefix}_global_min"] = df[f"{prefix}_min"].min()
        if f"{prefix}_max" in df.columns:
            summary[f"{prefix}_global_max"] = df[f"{prefix}_max"].max()

    return summary


def main():
    parser = argparse.ArgumentParser(description="Compute project statistics")
    parser.add_argument("path", help="Directory containing LAS files")
    parser.add_argument(
        "-c", "--curves", nargs="+", help="Specific curves to analyze (e.g., GR RHOB NPHI)"
    )
    parser.add_argument(
        "-o", "--output", help="Output CSV file for well statistics"
    )
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Recursively search directories"
    )
    parser.add_argument(
        "-s", "--summary-only", action="store_true", help="Only print summary, not per-well stats"
    )
    args = parser.parse_args()

    path = Path(args.path)

    if not path.is_dir():
        print(f"Error: {path} is not a directory")
        sys.exit(1)

    pattern = "**/*.las" if args.recursive else "*.las"
    files = list(path.glob(pattern))

    if not files:
        print("No LAS files found")
        sys.exit(1)

    print(f"Processing {len(files)} files...")

    # Compute statistics for each well
    well_stats = []
    for filepath in files:
        stats = compute_well_stats(str(filepath), args.curves)
        well_stats.append(stats)

        if "error" in stats:
            print(f"  Error: {filepath.name} - {stats['error']}")

    # Create DataFrame
    df = pd.DataFrame(well_stats)

    # Print per-well statistics
    if not args.summary_only:
        print(f"\n{'='*80}")
        print("Per-Well Statistics")
        print(f"{'='*80}")

        # Select columns to display
        display_cols = ["name", "depth_start", "depth_stop", "n_curves"]
        if args.curves:
            for curve in args.curves:
                prefix = curve.lower()
                for suffix in ["_mean", "_std", "_null_pct"]:
                    col = f"{prefix}{suffix}"
                    if col in df.columns:
                        display_cols.append(col)

        available_cols = [c for c in display_cols if c in df.columns]
        print(df[available_cols].to_string(index=False))

    # Compute and print project summary
    summary = compute_project_summary(well_stats, args.curves)

    print(f"\n{'='*80}")
    print("Project Summary")
    print(f"{'='*80}")
    for key, value in summary.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")

    # Export to CSV if requested
    if args.output:
        df.to_csv(args.output, index=False)
        print(f"\nStatistics exported to: {args.output}")

    # Print curve availability summary
    print(f"\n{'='*80}")
    print("Curve Availability")
    print(f"{'='*80}")

    # Count wells with each curve
    curve_counts = {}
    for stats in well_stats:
        if "curves_available" in stats:
            for curve in stats["curves_available"].split(", "):
                curve = curve.strip()
                if curve:
                    curve_counts[curve] = curve_counts.get(curve, 0) + 1

    for curve, count in sorted(curve_counts.items(), key=lambda x: -x[1]):
        pct = 100 * count / len(well_stats)
        print(f"  {curve}: {count}/{len(well_stats)} wells ({pct:.0f}%)")


if __name__ == "__main__":
    main()
