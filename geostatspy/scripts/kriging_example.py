#!/usr/bin/env python3
"""
Complete kriging workflow using GeostatsPy.

This script demonstrates:
1. Loading and exploring spatial data
2. Normal score transformation
3. Experimental variogram calculation
4. Variogram model fitting
5. Simple and ordinary kriging
6. Back-transformation and visualization

Usage:
    python kriging_example.py <data.csv>

Input CSV must have columns: X, Y, and a property column (default: 'porosity')
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import geostatspy.GSLIB as GSLIB
import geostatspy.geostats as geostats


def load_and_explore(filepath: str, prop_col: str = "porosity") -> pd.DataFrame:
    """Load data and print summary statistics."""
    df = pd.read_csv(filepath)

    print("=" * 60)
    print("Data Summary")
    print("=" * 60)
    print(f"Number of samples: {len(df)}")
    print(f"\nCoordinate ranges:")
    print(f"  X: {df['X'].min():.1f} to {df['X'].max():.1f}")
    print(f"  Y: {df['Y'].min():.1f} to {df['Y'].max():.1f}")
    print(f"\n{prop_col} statistics:")
    print(df[prop_col].describe())

    return df


def normal_score_transform(df: pd.DataFrame, prop_col: str) -> tuple:
    """Transform property to normal scores."""
    df["nscore"], tv, tns = geostats.nscore(df, prop_col)

    print("\n" + "=" * 60)
    print("Normal Score Transform")
    print("=" * 60)
    print(f"Original mean: {df[prop_col].mean():.4f}")
    print(f"Original std:  {df[prop_col].std():.4f}")
    print(f"Transformed mean: {df['nscore'].mean():.4f}")
    print(f"Transformed std:  {df['nscore'].std():.4f}")

    return tv, tns


def calculate_variogram(
    df: pd.DataFrame,
    lag_dist: float = 50,
    n_lags: int = 15,
    azimuth: float = 0,
    atol: float = 90,
) -> tuple:
    """Calculate experimental variogram."""
    lag, gamma, npairs = geostats.gamv(
        df,
        "X",
        "Y",
        "nscore",
        tmin=-9999,
        tmax=9999,
        xlag=lag_dist,
        xltol=lag_dist / 2,
        nlag=n_lags,
        azm=azimuth,
        atol=atol,
        bandwh=9999,
        bandwd=9999,
    )

    print("\n" + "=" * 60)
    print("Experimental Variogram")
    print("=" * 60)
    print(f"Lag distance: {lag_dist}")
    print(f"Number of lags: {n_lags}")
    print(f"Azimuth: {azimuth} (tolerance: {atol})")
    print("\nLag    Gamma    Pairs")
    print("-" * 30)
    for i in range(min(5, len(lag))):
        print(f"{lag[i]:6.1f}  {gamma[i]:6.4f}  {int(npairs[i]):6d}")
    if len(lag) > 5:
        print("...")

    return lag, gamma, npairs


def fit_variogram_model(
    nug: float = 0.0,
    sill: float = 1.0,
    range_maj: float = 300,
    range_min: float = 300,
    model_type: int = 1,
    azimuth: float = 0,
) -> dict:
    """Create variogram model."""
    vario = GSLIB.make_variogram(
        nug=nug,
        nst=1,
        it1=model_type,
        cc1=sill - nug,
        azi1=azimuth,
        hmaj1=range_maj,
        hmin1=range_min,
    )

    model_names = {1: "Spherical", 2: "Exponential", 3: "Gaussian", 4: "Power"}

    print("\n" + "=" * 60)
    print("Variogram Model")
    print("=" * 60)
    print(f"Model type: {model_names.get(model_type, 'Unknown')}")
    print(f"Nugget: {nug}")
    print(f"Sill: {sill}")
    print(f"Range (major): {range_maj}")
    print(f"Range (minor): {range_min}")
    print(f"Azimuth: {azimuth}")

    return vario


def perform_kriging(
    df: pd.DataFrame,
    vario: dict,
    nx: int = 50,
    ny: int = 50,
    ndmax: int = 10,
    radius: float = 500,
    ktype: int = 0,
) -> tuple:
    """Perform kriging estimation."""
    # Determine grid parameters
    xmin, xmax = df["X"].min(), df["X"].max()
    ymin, ymax = df["Y"].min(), df["Y"].max()

    # Add 5% buffer
    buffer_x = (xmax - xmin) * 0.05
    buffer_y = (ymax - ymin) * 0.05
    xmin -= buffer_x
    xmax += buffer_x
    ymin -= buffer_y
    ymax += buffer_y

    xsiz = (xmax - xmin) / nx
    ysiz = (ymax - ymin) / ny

    ktype_names = {0: "Simple", 1: "Ordinary"}

    print("\n" + "=" * 60)
    print(f"{ktype_names.get(ktype, 'Unknown')} Kriging")
    print("=" * 60)
    print(f"Grid: {nx} x {ny} cells")
    print(f"Cell size: {xsiz:.1f} x {ysiz:.1f}")
    print(f"Extent: ({xmin:.1f}, {ymin:.1f}) to ({xmax:.1f}, {ymax:.1f})")
    print(f"Max conditioning data: {ndmax}")
    print(f"Search radius: {radius}")

    # Run kriging
    est, var = geostats.kb2d(
        df,
        "X",
        "Y",
        "nscore",
        tmin=-9999,
        tmax=9999,
        nx=nx,
        xmn=xmin + xsiz / 2,
        xsiz=xsiz,
        ny=ny,
        ymn=ymin + ysiz / 2,
        ysiz=ysiz,
        nxdis=1,
        nydis=1,
        ndmin=1,
        ndmax=ndmax,
        radius=radius,
        ktype=ktype,
        skmean=0.0,
        vario=vario,
    )

    grid_params = {
        "xmin": xmin,
        "xmax": xmax,
        "ymin": ymin,
        "ymax": ymax,
        "nx": nx,
        "ny": ny,
        "xsiz": xsiz,
        "ysiz": ysiz,
    }

    return est, var, grid_params


def back_transform(
    est: np.ndarray, tv: np.ndarray, tns: np.ndarray, zmin: float, zmax: float
) -> np.ndarray:
    """Back-transform kriging estimate to original units."""
    est_flat = est.flatten()
    original = geostats.backtr(est_flat, tv, tns, zmin=zmin, zmax=zmax)
    return original.reshape(est.shape)


def plot_results(
    df: pd.DataFrame,
    est: np.ndarray,
    var: np.ndarray,
    grid_params: dict,
    prop_col: str,
    output_dir: str = ".",
):
    """Create visualization of results."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Location map
    ax = axes[0, 0]
    scatter = ax.scatter(
        df["X"], df["Y"], c=df[prop_col], cmap="viridis", s=20, edgecolors="k", lw=0.5
    )
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title(f"Sample Locations - {prop_col}")
    plt.colorbar(scatter, ax=ax)

    # Kriging estimate
    ax = axes[0, 1]
    extent = [
        grid_params["xmin"],
        grid_params["xmax"],
        grid_params["ymin"],
        grid_params["ymax"],
    ]
    im = ax.imshow(est, extent=extent, origin="lower", cmap="viridis", aspect="auto")
    ax.scatter(df["X"], df["Y"], c="white", s=10, edgecolors="k", lw=0.5)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title(f"Kriging Estimate - {prop_col}")
    plt.colorbar(im, ax=ax)

    # Kriging variance
    ax = axes[1, 0]
    im = ax.imshow(var, extent=extent, origin="lower", cmap="Reds", aspect="auto")
    ax.scatter(df["X"], df["Y"], c="blue", s=10, edgecolors="k", lw=0.5)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Kriging Variance")
    plt.colorbar(im, ax=ax)

    # Histogram comparison
    ax = axes[1, 1]
    ax.hist(
        df[prop_col], bins=30, density=True, alpha=0.7, label="Data", color="blue"
    )
    ax.hist(
        est.flatten(), bins=30, density=True, alpha=0.7, label="Kriging", color="orange"
    )
    ax.set_xlabel(prop_col)
    ax.set_ylabel("Density")
    ax.set_title("Histogram Comparison")
    ax.legend()

    plt.tight_layout()

    output_path = Path(output_dir) / "kriging_results.png"
    plt.savefig(output_path, dpi=150)
    print(f"\nResults saved to: {output_path}")

    plt.show()


def main():
    parser = argparse.ArgumentParser(description="Kriging workflow with GeostatsPy")
    parser.add_argument("input", help="Input CSV file with X, Y, and property columns")
    parser.add_argument(
        "--property", "-p", default="porosity", help="Property column name"
    )
    parser.add_argument("--lag", type=float, default=50, help="Lag distance")
    parser.add_argument("--nlags", type=int, default=15, help="Number of lags")
    parser.add_argument("--range", type=float, default=300, help="Variogram range")
    parser.add_argument("--nugget", type=float, default=0.0, help="Nugget effect")
    parser.add_argument("--sill", type=float, default=1.0, help="Sill value")
    parser.add_argument(
        "--model",
        type=int,
        default=1,
        choices=[1, 2, 3],
        help="Model type: 1=spherical, 2=exponential, 3=gaussian",
    )
    parser.add_argument("--nx", type=int, default=50, help="Grid cells in X")
    parser.add_argument("--ny", type=int, default=50, help="Grid cells in Y")
    parser.add_argument(
        "--ktype",
        type=int,
        default=0,
        choices=[0, 1],
        help="Kriging type: 0=simple, 1=ordinary",
    )
    parser.add_argument("--output", "-o", default=".", help="Output directory")

    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: File not found: {args.input}")
        sys.exit(1)

    # Load and explore data
    df = load_and_explore(args.input, args.property)

    # Normal score transform
    tv, tns = normal_score_transform(df, args.property)

    # Calculate experimental variogram
    lag, gamma, npairs = calculate_variogram(
        df, lag_dist=args.lag, n_lags=args.nlags, azimuth=0, atol=90
    )

    # Fit variogram model
    vario = fit_variogram_model(
        nug=args.nugget,
        sill=args.sill,
        range_maj=args.range,
        range_min=args.range,
        model_type=args.model,
    )

    # Perform kriging
    est, var, grid_params = perform_kriging(
        df, vario, nx=args.nx, ny=args.ny, ktype=args.ktype
    )

    # Back-transform to original units
    zmin, zmax = df[args.property].min(), df[args.property].max()
    est_original = back_transform(est, tv, tns, zmin=zmin * 0.9, zmax=zmax * 1.1)

    print("\n" + "=" * 60)
    print("Results Summary")
    print("=" * 60)
    print(f"Estimate range: {est_original.min():.4f} to {est_original.max():.4f}")
    print(f"Estimate mean: {est_original.mean():.4f}")
    print(f"Variance range: {var.min():.4f} to {var.max():.4f}")

    # Plot results
    plot_results(df, est_original, var, grid_params, args.property, args.output)


if __name__ == "__main__":
    main()
