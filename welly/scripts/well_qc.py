#!/usr/bin/env python3
"""
Quality control for well data using welly.

Usage:
    python well_qc.py <file.las>
    python well_qc.py <directory> --recursive
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from welly import Well


def qc_well(filepath: str) -> dict:
    """
    Perform QC on a well and return a report.

    Returns:
        dict with keys: valid, errors, warnings, info, curves
    """
    report = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "info": {},
        "curves": {},
    }

    # Try to load the well
    try:
        w = Well.from_las(filepath)
    except Exception as e:
        report["valid"] = False
        report["errors"].append(f"Failed to load well: {e}")
        return report

    # Basic info
    report["info"]["name"] = w.name or "Unknown"
    report["info"]["uwi"] = w.uwi or "Unknown"
    report["info"]["n_curves"] = len(w.data)

    # Check if any curves exist
    if len(w.data) == 0:
        report["errors"].append("No curves in well")
        report["valid"] = False
        return report

    # Get depth range from first curve
    first_curve = list(w.data.values())[0]
    report["info"]["depth_start"] = first_curve.start
    report["info"]["depth_stop"] = first_curve.stop
    report["info"]["depth_step"] = first_curve.step

    # Check each curve
    for name, curve in w.data.items():
        curve_report = {
            "start": curve.start,
            "stop": curve.stop,
            "step": curve.step,
            "units": curve.units or "Unknown",
            "samples": len(curve.values),
        }

        values = curve.values

        # Count nulls/NaNs
        null_count = np.sum(np.isnan(values))
        null_pct = 100 * null_count / len(values) if len(values) > 0 else 0
        curve_report["null_count"] = int(null_count)
        curve_report["null_pct"] = null_pct

        if null_pct > 50:
            report["warnings"].append(f"Curve {name}: {null_pct:.1f}% null values")
        elif null_pct > 20:
            report["warnings"].append(f"Curve {name}: {null_pct:.1f}% null values")

        # Statistics on valid data
        valid = values[~np.isnan(values)]
        if len(valid) > 0:
            curve_report["min"] = float(valid.min())
            curve_report["max"] = float(valid.max())
            curve_report["mean"] = float(valid.mean())
            curve_report["std"] = float(valid.std())

            # Check for constant values
            if curve_report["std"] == 0:
                report["warnings"].append(f"Curve {name}: constant value ({valid[0]})")

            # Check for suspicious ranges
            if name == "GR" and (valid.max() > 300 or valid.min() < 0):
                report["warnings"].append(
                    f"Curve {name}: suspicious range ({valid.min():.1f} - {valid.max():.1f})"
                )
            if name == "NPHI" and (valid.max() > 1 or valid.min() < -0.15):
                report["warnings"].append(
                    f"Curve {name}: suspicious range ({valid.min():.3f} - {valid.max():.3f})"
                )
            if name == "RHOB" and (valid.max() > 3.5 or valid.min() < 1.5):
                report["warnings"].append(
                    f"Curve {name}: suspicious range ({valid.min():.2f} - {valid.max():.2f})"
                )

        # Detect gaps (consecutive nulls)
        is_null = np.isnan(values)
        diff = np.diff(is_null.astype(int))
        gap_starts = np.where(diff == 1)[0]
        if len(gap_starts) > 0:
            curve_report["n_gaps"] = len(gap_starts)
            if len(gap_starts) > 5:
                report["warnings"].append(f"Curve {name}: {len(gap_starts)} gaps in data")

        report["curves"][name] = curve_report

    # Check depth consistency across curves
    steps = [c.step for c in w.data.values()]
    if len(set(steps)) > 1:
        report["warnings"].append(f"Curves have different step sizes: {set(steps)}")

    return report


def print_report(filepath: str, report: dict) -> None:
    """Print QC report."""
    status = "VALID" if report["valid"] else "INVALID"
    print(f"\n{'='*70}")
    print(f"File: {filepath}")
    print(f"Status: {status}")
    print(f"{'='*70}")

    if report["info"]:
        print("\nWell Info:")
        for key, value in report["info"].items():
            print(f"  {key}: {value}")

    if report["curves"]:
        print("\nCurve Summary:")
        print(f"  {'Curve':<12} {'Unit':<8} {'Samples':<10} {'Null%':<8} {'Min':<12} {'Max':<12}")
        print(f"  {'-'*12} {'-'*8} {'-'*10} {'-'*8} {'-'*12} {'-'*12}")
        for name, info in report["curves"].items():
            min_val = f"{info.get('min', 'N/A'):.4g}" if 'min' in info else "N/A"
            max_val = f"{info.get('max', 'N/A'):.4g}" if 'max' in info else "N/A"
            print(
                f"  {name:<12} {info['units']:<8} {info['samples']:<10} "
                f"{info['null_pct']:<8.1f} {min_val:<12} {max_val:<12}"
            )

    if report["errors"]:
        print("\nErrors:")
        for error in report["errors"]:
            print(f"  - {error}")

    if report["warnings"]:
        print("\nWarnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")

    if not report["errors"] and not report["warnings"]:
        print("\nNo issues found.")


def main():
    parser = argparse.ArgumentParser(description="QC well data")
    parser.add_argument("path", help="LAS file or directory to QC")
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Recursively search directories"
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Only show files with issues"
    )
    args = parser.parse_args()

    path = Path(args.path)

    if path.is_file():
        files = [path]
    elif path.is_dir():
        pattern = "**/*.las" if args.recursive else "*.las"
        files = list(path.glob(pattern))
    else:
        print(f"Error: {path} not found")
        sys.exit(1)

    if not files:
        print("No LAS files found")
        sys.exit(1)

    valid_count = 0
    warning_count = 0

    for filepath in files:
        report = qc_well(str(filepath))

        if report["valid"]:
            valid_count += 1

        has_issues = report["errors"] or report["warnings"]
        if has_issues:
            warning_count += 1

        if not args.quiet or has_issues:
            print_report(str(filepath), report)

    print(f"\n{'='*70}")
    print(f"Summary: {valid_count}/{len(files)} files valid, {warning_count} with warnings")


if __name__ == "__main__":
    main()
