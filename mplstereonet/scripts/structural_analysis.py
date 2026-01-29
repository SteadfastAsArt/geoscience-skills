#!/usr/bin/env python3
"""
Structural data analysis and stereonet plotting.

Usage:
    python structural_analysis.py <input.csv> [--output stereonet.png]
    python structural_analysis.py <input.csv> --contour --stats

Input CSV format:
    strike,dip[,type]
    45,30,bedding
    135,60,joint
    ...
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import mplstereonet
import numpy as np
import pandas as pd


def load_data(filepath: str) -> pd.DataFrame:
    """
    Load structural data from CSV file.

    Expected columns: strike, dip, and optionally type/set
    """
    df = pd.read_csv(filepath)

    # Normalize column names
    df.columns = df.columns.str.lower().str.strip()

    # Check required columns
    if "strike" not in df.columns or "dip" not in df.columns:
        raise ValueError("CSV must have 'strike' and 'dip' columns")

    return df


def calculate_statistics(strikes: np.ndarray, dips: np.ndarray) -> dict:
    """
    Calculate statistical measures for orientation data.

    Returns:
        dict with mean orientation, eigenvalues, K value, etc.
    """
    stats = {}

    # Convert to poles
    lon, lat = mplstereonet.pole(strikes, dips)

    # Mean vector
    mean_lon, mean_lat = mplstereonet.find_mean_vector(lon, lat)
    mean_strike, mean_dip = mplstereonet.pole2strike(mean_lon, mean_lat)
    stats["mean_strike"] = float(mean_strike)
    stats["mean_dip"] = float(mean_dip)

    # Eigenvectors and eigenvalues
    eigenvecs, eigenvals = mplstereonet.eigenvectors(lon, lat)
    stats["eigenvalues"] = eigenvals.tolist()

    # K value (clustering measure)
    # K > 1: clustered, K < 1: girdle distribution
    if eigenvals[1] > 0:
        stats["K"] = float(np.log(eigenvals[0] / eigenvals[1]))
    else:
        stats["K"] = float("inf")

    # C value (strength of preferred orientation)
    stats["C"] = float(np.log(eigenvals[0] / eigenvals[2]))

    # Fit girdle (for folded data)
    girdle_strike, girdle_dip = mplstereonet.fit_girdle(strikes, dips)
    stats["girdle_strike"] = float(girdle_strike)
    stats["girdle_dip"] = float(girdle_dip)

    # Fold axis (pole to girdle)
    fold_trend, fold_plunge = mplstereonet.pole(girdle_strike, girdle_dip)
    stats["fold_axis_trend"] = float(fold_trend)
    stats["fold_axis_plunge"] = float(fold_plunge)

    # Sample size
    stats["n"] = len(strikes)

    return stats


def plot_stereonet(
    df: pd.DataFrame,
    output_path: str = None,
    show_contours: bool = False,
    show_planes: bool = False,
    show_stats: bool = False,
    title: str = None,
) -> None:
    """
    Create stereonet plot from structural data.

    Args:
        df: DataFrame with strike, dip columns (and optionally type)
        output_path: Path to save figure (shows plot if None)
        show_contours: Add density contours
        show_planes: Plot great circles instead of just poles
        show_stats: Calculate and display statistics
        title: Plot title
    """
    fig, ax = mplstereonet.subplots(figsize=(10, 10))

    # Check if we have multiple types/sets
    if "type" in df.columns or "set" in df.columns:
        type_col = "type" if "type" in df.columns else "set"
        groups = df.groupby(type_col)

        colors = plt.cm.tab10(np.linspace(0, 1, len(groups)))

        for (name, group), color in zip(groups, colors):
            strikes = group["strike"].values
            dips = group["dip"].values

            if show_planes:
                for s, d in zip(strikes, dips):
                    ax.plane(s, d, color=color, linewidth=0.5, alpha=0.5)

            ax.pole(strikes, dips, marker="o", color=color, markersize=6, label=name)

            if show_stats:
                stats = calculate_statistics(strikes, dips)
                ax.pole(
                    stats["mean_strike"],
                    stats["mean_dip"],
                    marker="*",
                    color=color,
                    markersize=15,
                    markeredgecolor="black",
                )

        ax.legend(loc="upper left")

    else:
        # Single dataset
        strikes = df["strike"].values
        dips = df["dip"].values

        if show_contours:
            cax = ax.density_contourf(
                strikes, dips, measurement="poles", cmap="Reds", alpha=0.7
            )
            fig.colorbar(cax, ax=ax, shrink=0.7, label="Density")

        if show_planes:
            for s, d in zip(strikes, dips):
                ax.plane(s, d, "b-", linewidth=0.5, alpha=0.3)

        ax.pole(strikes, dips, "ko", markersize=5)

        if show_stats:
            stats = calculate_statistics(strikes, dips)

            # Plot mean pole
            ax.pole(
                stats["mean_strike"],
                stats["mean_dip"],
                "r*",
                markersize=15,
                label="Mean pole",
            )

            # Plot girdle if K < 1 (girdle distribution)
            if stats["K"] < 1:
                ax.plane(
                    stats["girdle_strike"],
                    stats["girdle_dip"],
                    "r-",
                    linewidth=2,
                    label="Best-fit girdle",
                )
                ax.line(
                    stats["fold_axis_trend"],
                    stats["fold_axis_plunge"],
                    "r^",
                    markersize=12,
                    label="Fold axis",
                )

            ax.legend(loc="upper left")

    ax.grid()

    if title:
        ax.set_title(title, fontsize=12)
    elif "n" in dir():
        ax.set_title(f"Structural Data (n={len(df)})", fontsize=12)

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"Saved: {output_path}")
    else:
        plt.show()

    plt.close()


def print_statistics(df: pd.DataFrame) -> None:
    """Print statistical summary of structural data."""
    print("\n" + "=" * 60)
    print("STRUCTURAL DATA STATISTICS")
    print("=" * 60)

    if "type" in df.columns or "set" in df.columns:
        type_col = "type" if "type" in df.columns else "set"
        groups = df.groupby(type_col)

        for name, group in groups:
            strikes = group["strike"].values
            dips = group["dip"].values
            stats = calculate_statistics(strikes, dips)

            print(f"\n{name.upper()}")
            print("-" * 40)
            _print_stats(stats)
    else:
        strikes = df["strike"].values
        dips = df["dip"].values
        stats = calculate_statistics(strikes, dips)
        _print_stats(stats)


def _print_stats(stats: dict) -> None:
    """Print formatted statistics."""
    print(f"  Sample size: {stats['n']}")
    print(f"  Mean pole: {stats['mean_strike']:.1f}/{stats['mean_dip']:.1f}")
    print(f"  Best-fit girdle: {stats['girdle_strike']:.1f}/{stats['girdle_dip']:.1f}")
    print(
        f"  Fold axis: {stats['fold_axis_trend']:.1f}/{stats['fold_axis_plunge']:.1f}"
    )
    print(f"  K value: {stats['K']:.2f}", end="")
    if stats["K"] > 1:
        print(" (clustered)")
    else:
        print(" (girdle distribution)")
    print(f"  C value: {stats['C']:.2f}")
    print(f"  Eigenvalues: {stats['eigenvalues'][0]:.3f}, "
          f"{stats['eigenvalues'][1]:.3f}, {stats['eigenvalues'][2]:.3f}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze structural geology data and create stereonet plots"
    )
    parser.add_argument("input", help="Input CSV file with strike,dip data")
    parser.add_argument(
        "-o", "--output", help="Output image file (shows plot if not specified)"
    )
    parser.add_argument(
        "-c", "--contour", action="store_true", help="Add density contours"
    )
    parser.add_argument(
        "-p", "--planes", action="store_true", help="Plot great circles"
    )
    parser.add_argument(
        "-s", "--stats", action="store_true", help="Calculate and show statistics"
    )
    parser.add_argument("-t", "--title", help="Plot title")

    args = parser.parse_args()

    # Check input file
    if not Path(args.input).exists():
        print(f"Error: File not found: {args.input}")
        sys.exit(1)

    # Load data
    try:
        df = load_data(args.input)
        print(f"Loaded {len(df)} measurements from {args.input}")
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

    # Print statistics if requested
    if args.stats:
        print_statistics(df)

    # Create plot
    plot_stereonet(
        df,
        output_path=args.output,
        show_contours=args.contour,
        show_planes=args.planes,
        show_stats=args.stats,
        title=args.title,
    )


if __name__ == "__main__":
    main()
