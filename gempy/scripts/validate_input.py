#!/usr/bin/env python3
"""
Validate GemPy input data files.

Usage:
    python validate_input.py surface_points.csv orientations.csv
    python validate_input.py surface_points.csv orientations.csv --extent 0,1000,0,1000,0,500
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def validate_surface_points(filepath: str) -> dict:
    """
    Validate surface points CSV file.

    Returns:
        dict with keys: valid, errors, warnings, info
    """
    report = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "info": {},
    }

    # Try to read file
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        report["valid"] = False
        report["errors"].append(f"Failed to read file: {e}")
        return report

    # Check required columns
    required_cols = ["X", "Y", "Z", "surface"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        report["valid"] = False
        report["errors"].append(f"Missing required columns: {missing}")
        return report

    # Basic info
    report["info"]["n_points"] = len(df)
    report["info"]["n_surfaces"] = df["surface"].nunique()
    report["info"]["surfaces"] = df["surface"].unique().tolist()

    # Check for empty values
    for col in ["X", "Y", "Z"]:
        null_count = df[col].isna().sum()
        if null_count > 0:
            report["errors"].append(f"Column {col} has {null_count} null values")
            report["valid"] = False

    # Check numeric types
    for col in ["X", "Y", "Z"]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            report["errors"].append(f"Column {col} is not numeric")
            report["valid"] = False

    # Check points per surface
    for surface in df["surface"].unique():
        count = len(df[df["surface"] == surface])
        if count < 2:
            report["warnings"].append(
                f"Surface '{surface}' has only {count} point(s) (minimum 2 required)"
            )

    # Check for duplicate points
    dups = df.duplicated(subset=["X", "Y", "Z", "surface"], keep=False)
    if dups.sum() > 0:
        report["warnings"].append(f"Found {dups.sum()} duplicate points")

    # Coordinate ranges
    report["info"]["x_range"] = [df["X"].min(), df["X"].max()]
    report["info"]["y_range"] = [df["Y"].min(), df["Y"].max()]
    report["info"]["z_range"] = [df["Z"].min(), df["Z"].max()]

    return report


def validate_orientations(filepath: str) -> dict:
    """
    Validate orientations CSV file.

    Returns:
        dict with keys: valid, errors, warnings, info
    """
    report = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "info": {},
    }

    # Try to read file
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        report["valid"] = False
        report["errors"].append(f"Failed to read file: {e}")
        return report

    # Check required columns
    required_base = ["X", "Y", "Z", "surface"]
    missing_base = [c for c in required_base if c not in df.columns]
    if missing_base:
        report["valid"] = False
        report["errors"].append(f"Missing required columns: {missing_base}")
        return report

    # Check for dip/azimuth OR pole vector
    has_dip_azimuth = "dip" in df.columns and "azimuth" in df.columns
    has_pole_vector = all(c in df.columns for c in ["Gx", "Gy", "Gz"])

    if not has_dip_azimuth and not has_pole_vector:
        report["valid"] = False
        report["errors"].append(
            "Must have either (dip, azimuth) or (Gx, Gy, Gz) columns"
        )
        return report

    # Basic info
    report["info"]["n_orientations"] = len(df)
    report["info"]["n_surfaces"] = df["surface"].nunique()
    report["info"]["surfaces"] = df["surface"].unique().tolist()
    report["info"]["format"] = "dip/azimuth" if has_dip_azimuth else "pole_vector"

    # Check for empty values
    for col in ["X", "Y", "Z"]:
        null_count = df[col].isna().sum()
        if null_count > 0:
            report["errors"].append(f"Column {col} has {null_count} null values")
            report["valid"] = False

    # Validate dip/azimuth ranges
    if has_dip_azimuth:
        if (df["dip"] < 0).any() or (df["dip"] > 90).any():
            report["warnings"].append("Dip values should be between 0 and 90 degrees")
        if (df["azimuth"] < 0).any() or (df["azimuth"] >= 360).any():
            report["warnings"].append("Azimuth values should be between 0 and 360 degrees")

    # Validate pole vectors (should be unit vectors)
    if has_pole_vector:
        magnitudes = np.sqrt(df["Gx"]**2 + df["Gy"]**2 + df["Gz"]**2)
        not_unit = np.abs(magnitudes - 1.0) > 0.01
        if not_unit.any():
            report["warnings"].append(
                f"{not_unit.sum()} pole vectors are not unit vectors"
            )

    # Check orientations per surface
    for surface in df["surface"].unique():
        count = len(df[df["surface"] == surface])
        if count < 1:
            report["warnings"].append(
                f"Surface '{surface}' has no orientations (minimum 1 required)"
            )

    return report


def check_data_consistency(
    points_report: dict, ori_report: dict, extent: list = None
) -> dict:
    """
    Check consistency between surface points and orientations.

    Returns:
        dict with warnings about inconsistencies
    """
    report = {"warnings": []}

    # Check surfaces match
    points_surfaces = set(points_report["info"].get("surfaces", []))
    ori_surfaces = set(ori_report["info"].get("surfaces", []))

    missing_ori = points_surfaces - ori_surfaces
    if missing_ori:
        report["warnings"].append(
            f"Surfaces without orientations: {missing_ori}"
        )

    extra_ori = ori_surfaces - points_surfaces
    if extra_ori:
        report["warnings"].append(
            f"Orientations for unknown surfaces: {extra_ori}"
        )

    # Check extent if provided
    if extent:
        x_range = points_report["info"].get("x_range", [0, 0])
        y_range = points_report["info"].get("y_range", [0, 0])
        z_range = points_report["info"].get("z_range", [0, 0])

        if x_range[0] < extent[0] or x_range[1] > extent[1]:
            report["warnings"].append("X coordinates outside specified extent")
        if y_range[0] < extent[2] or y_range[1] > extent[3]:
            report["warnings"].append("Y coordinates outside specified extent")
        if z_range[0] < extent[4] or z_range[1] > extent[5]:
            report["warnings"].append("Z coordinates outside specified extent")

    return report


def print_report(name: str, report: dict) -> None:
    """Print validation report."""
    status = "VALID" if report["valid"] else "INVALID"
    print(f"\n{'='*60}")
    print(f"{name}: {status}")
    print(f"{'='*60}")

    if report.get("info"):
        print("\nInfo:")
        for key, value in report["info"].items():
            print(f"  {key}: {value}")

    if report.get("errors"):
        print("\nErrors:")
        for error in report["errors"]:
            print(f"  - {error}")

    if report.get("warnings"):
        print("\nWarnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")

    if not report.get("errors") and not report.get("warnings"):
        print("\nNo issues found.")


def main():
    parser = argparse.ArgumentParser(
        description="Validate GemPy input data files"
    )
    parser.add_argument(
        "surface_points", help="Surface points CSV file"
    )
    parser.add_argument(
        "orientations", help="Orientations CSV file"
    )
    parser.add_argument(
        "--extent",
        help="Model extent as xmin,xmax,ymin,ymax,zmin,zmax",
    )
    args = parser.parse_args()

    # Parse extent if provided
    extent = None
    if args.extent:
        try:
            extent = [float(x) for x in args.extent.split(",")]
            if len(extent) != 6:
                print("Error: Extent must have 6 values")
                sys.exit(1)
        except ValueError:
            print("Error: Invalid extent format")
            sys.exit(1)

    # Validate files
    points_report = validate_surface_points(args.surface_points)
    ori_report = validate_orientations(args.orientations)

    print_report("Surface Points", points_report)
    print_report("Orientations", ori_report)

    # Check consistency
    if points_report["valid"] and ori_report["valid"]:
        consistency = check_data_consistency(points_report, ori_report, extent)
        if consistency["warnings"]:
            print(f"\n{'='*60}")
            print("Consistency Check")
            print(f"{'='*60}")
            print("\nWarnings:")
            for warning in consistency["warnings"]:
                print(f"  - {warning}")

    # Summary
    all_valid = points_report["valid"] and ori_report["valid"]
    print(f"\n{'='*60}")
    print(f"Overall: {'VALID' if all_valid else 'INVALID'}")

    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
