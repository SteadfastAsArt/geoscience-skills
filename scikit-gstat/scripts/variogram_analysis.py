#!/usr/bin/env python3
"""
Complete variogram analysis workflow with model comparison and export.

Usage:
    python variogram_analysis.py <data.csv> --x X --y Y --z VALUE
    python variogram_analysis.py <data.csv> --x X --y Y --z VALUE --output results/

Example:
    python variogram_analysis.py samples.csv --x easting --y northing --z porosity
"""

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import skgstat as skg


def load_data(filepath: str, x_col: str, y_col: str, z_col: str) -> tuple:
    """
    Load spatial data from CSV file.

    Returns:
        tuple: (coordinates array, values array)
    """
    df = pd.read_csv(filepath)

    # Validate columns exist
    for col in [x_col, y_col, z_col]:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found. Available: {list(df.columns)}")

    # Remove rows with missing values
    df = df[[x_col, y_col, z_col]].dropna()

    coords = df[[x_col, y_col]].values
    values = df[z_col].values

    return coords, values


def analyze_variogram(
    coords: np.ndarray,
    values: np.ndarray,
    n_lags: int = 15,
    maxlag: str = "median",
) -> dict:
    """
    Perform comprehensive variogram analysis.

    Returns:
        dict: Analysis results with best model and parameters
    """
    results = {
        "n_points": len(values),
        "value_stats": {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
        },
        "models": [],
        "best_model": None,
    }

    # Create base variogram
    V = skg.Variogram(coords, values, n_lags=n_lags, maxlag=maxlag)

    # Compare models
    models = ["spherical", "exponential", "gaussian", "matern"]

    for model_name in models:
        try:
            V.model = model_name
            model_result = {
                "name": model_name,
                "range": float(V.parameters[0]),
                "sill": float(V.parameters[1]),
                "nugget": float(V.parameters[2]),
                "rmse": float(V.rmse),
            }
            results["models"].append(model_result)
        except Exception as e:
            print(f"Warning: {model_name} model failed: {e}")

    # Find best model by RMSE
    if results["models"]:
        best = min(results["models"], key=lambda x: x["rmse"])
        results["best_model"] = best["name"]

        # Set variogram to best model
        V.model = best["name"]

    return results, V


def compare_estimators(coords: np.ndarray, values: np.ndarray) -> list:
    """
    Compare different variogram estimators.

    Returns:
        list: Results for each estimator
    """
    estimators = ["matheron", "cressie", "dowd"]
    results = []

    for est in estimators:
        try:
            V = skg.Variogram(coords, values, estimator=est, model="spherical")
            results.append(
                {
                    "estimator": est,
                    "range": float(V.parameters[0]),
                    "sill": float(V.parameters[1]),
                    "nugget": float(V.parameters[2]),
                    "rmse": float(V.rmse),
                }
            )
        except Exception as e:
            print(f"Warning: {est} estimator failed: {e}")

    return results


def check_anisotropy(coords: np.ndarray, values: np.ndarray) -> list:
    """
    Check for spatial anisotropy using directional variograms.

    Returns:
        list: Range values for different azimuths
    """
    azimuths = [0, 45, 90, 135]
    results = []

    for az in azimuths:
        try:
            DV = skg.DirectionalVariogram(
                coords, values, azimuth=az, tolerance=22.5, model="spherical"
            )
            results.append(
                {
                    "azimuth": az,
                    "range": float(DV.parameters[0]),
                    "sill": float(DV.parameters[1]),
                }
            )
        except Exception as e:
            print(f"Warning: Directional variogram at {az} failed: {e}")

    return results


def plot_variogram(V: skg.Variogram, output_path: str = None) -> None:
    """
    Create variogram plot with model fit.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot experimental variogram
    ax.scatter(V.bins, V.experimental, s=50, c="blue", label="Experimental", zorder=3)

    # Plot fitted model
    x_model = np.linspace(0, V.bins[-1], 100)
    y_model = V.model(x_model, *V.parameters[:3])
    ax.plot(x_model, y_model, "r-", linewidth=2, label=f"{V.model.__name__} model")

    # Add parameter annotations
    params_text = (
        f"Range: {V.parameters[0]:.2f}\n"
        f"Sill: {V.parameters[1]:.4f}\n"
        f"Nugget: {V.parameters[2]:.4f}\n"
        f"RMSE: {V.rmse:.4f}"
    )
    ax.text(
        0.95,
        0.05,
        params_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="bottom",
        horizontalalignment="right",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    ax.set_xlabel("Lag Distance")
    ax.set_ylabel("Semivariance")
    ax.set_title("Variogram Analysis")
    ax.legend()
    ax.grid(True, alpha=0.3)

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Saved variogram plot to: {output_path}")
    else:
        plt.show()

    plt.close()


def plot_model_comparison(coords: np.ndarray, values: np.ndarray, output_path: str = None) -> None:
    """
    Create comparison plot of all variogram models.
    """
    models = ["spherical", "exponential", "gaussian", "matern"]
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    V = skg.Variogram(coords, values)

    for ax, model_name in zip(axes.flat, models):
        V.model = model_name

        # Plot experimental
        ax.scatter(V.bins, V.experimental, s=30, c="blue", zorder=3)

        # Plot model
        x_model = np.linspace(0, V.bins[-1], 100)
        y_model = V.model(x_model, *V.parameters[:3])
        ax.plot(x_model, y_model, "r-", linewidth=2)

        ax.set_title(f"{model_name.capitalize()} (RMSE: {V.rmse:.4f})")
        ax.set_xlabel("Lag Distance")
        ax.set_ylabel("Semivariance")
        ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches="tight")
        print(f"Saved model comparison to: {output_path}")
    else:
        plt.show()

    plt.close()


def print_report(results: dict, estimator_results: list, anisotropy_results: list) -> None:
    """
    Print analysis report to console.
    """
    print("\n" + "=" * 60)
    print("VARIOGRAM ANALYSIS REPORT")
    print("=" * 60)

    print(f"\nData points: {results['n_points']}")
    print(f"Value mean: {results['value_stats']['mean']:.4f}")
    print(f"Value std: {results['value_stats']['std']:.4f}")

    print("\n--- Model Comparison ---")
    print(f"{'Model':<12} {'Range':>10} {'Sill':>10} {'Nugget':>10} {'RMSE':>10}")
    print("-" * 54)
    for m in results["models"]:
        marker = " *" if m["name"] == results["best_model"] else ""
        print(
            f"{m['name']:<12} {m['range']:>10.2f} {m['sill']:>10.4f} "
            f"{m['nugget']:>10.4f} {m['rmse']:>10.4f}{marker}"
        )
    print("\n* Best model (lowest RMSE)")

    if estimator_results:
        print("\n--- Estimator Comparison (Spherical) ---")
        print(f"{'Estimator':<12} {'Range':>10} {'Sill':>10} {'Nugget':>10}")
        print("-" * 44)
        for e in estimator_results:
            print(
                f"{e['estimator']:<12} {e['range']:>10.2f} "
                f"{e['sill']:>10.4f} {e['nugget']:>10.4f}"
            )

    if anisotropy_results:
        print("\n--- Anisotropy Check ---")
        print(f"{'Azimuth':>10} {'Range':>10} {'Sill':>10}")
        print("-" * 32)
        for a in anisotropy_results:
            print(f"{a['azimuth']:>10} {a['range']:>10.2f} {a['sill']:>10.4f}")

        ranges = [a["range"] for a in anisotropy_results]
        ratio = max(ranges) / min(ranges) if min(ranges) > 0 else float("inf")
        print(f"\nAnisotropy ratio: {ratio:.2f}")
        if ratio > 1.5:
            print("Note: Significant anisotropy detected. Consider directional kriging.")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Variogram analysis workflow")
    parser.add_argument("data", help="CSV file with spatial data")
    parser.add_argument("--x", required=True, help="X coordinate column name")
    parser.add_argument("--y", required=True, help="Y coordinate column name")
    parser.add_argument("--z", required=True, help="Value column name")
    parser.add_argument("--n-lags", type=int, default=15, help="Number of lag bins")
    parser.add_argument("--maxlag", default="median", help="Maximum lag distance")
    parser.add_argument("--output", "-o", help="Output directory for results")
    parser.add_argument(
        "--no-plots", action="store_true", help="Skip generating plots"
    )
    args = parser.parse_args()

    # Load data
    print(f"Loading data from: {args.data}")
    coords, values = load_data(args.data, args.x, args.y, args.z)
    print(f"Loaded {len(values)} data points")

    # Run analysis
    print("Analyzing variogram...")
    results, V = analyze_variogram(coords, values, args.n_lags, args.maxlag)

    print("Comparing estimators...")
    estimator_results = compare_estimators(coords, values)

    print("Checking anisotropy...")
    anisotropy_results = check_anisotropy(coords, values)

    # Print report
    print_report(results, estimator_results, anisotropy_results)

    # Save outputs
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save JSON results
        full_results = {
            "variogram": results,
            "estimators": estimator_results,
            "anisotropy": anisotropy_results,
        }
        json_path = output_dir / "variogram_results.json"
        with open(json_path, "w") as f:
            json.dump(full_results, f, indent=2)
        print(f"\nSaved results to: {json_path}")

        # Generate plots
        if not args.no_plots:
            plot_variogram(V, str(output_dir / "variogram.png"))
            plot_model_comparison(coords, values, str(output_dir / "model_comparison.png"))


if __name__ == "__main__":
    main()
