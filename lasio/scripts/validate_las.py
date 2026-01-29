#!/usr/bin/env python3
"""
Validate LAS file format and report issues.

Usage:
    python validate_las.py <file.las>
    python validate_las.py <directory> --recursive
"""

import argparse
import sys
from pathlib import Path

import lasio
import numpy as np


def validate_las(filepath: str) -> dict:
    """
    Validate a LAS file and return a report.

    Returns:
        dict with keys: valid, errors, warnings, info
    """
    report = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "info": {},
    }

    # Try to read the file
    try:
        las = lasio.read(filepath, ignore_header_errors=True)
    except Exception as e:
        report["valid"] = False
        report["errors"].append(f"Failed to read file: {e}")
        return report

    # Basic info
    report["info"]["version"] = las.version.get("VERS", {}).get("value", "Unknown")
    report["info"]["n_curves"] = len(las.curves)
    report["info"]["n_samples"] = len(las.data) if las.data.size > 0 else 0

    # Check required well headers
    required_headers = ["STRT", "STOP", "STEP", "NULL", "WELL"]
    for header in required_headers:
        if header not in las.well:
            report["warnings"].append(f"Missing required header: {header}")

    # Check for data
    if las.data.size == 0:
        report["errors"].append("No data in file")
        report["valid"] = False
        return report

    # Check depth curve exists
    depth_names = ["DEPT", "DEPTH", "MD", "TVD"]
    has_depth = any(name in las.curves.keys() for name in depth_names)
    if not has_depth:
        report["warnings"].append(
            f"No standard depth curve found. First curve: {las.curves[0].mnemonic}"
        )

    # Check depth monotonicity
    depth = las.data[:, 0]
    diff = np.diff(depth)
    if not (np.all(diff > 0) or np.all(diff < 0)):
        report["warnings"].append("Depth values are not monotonic")

    # Check for null values
    null_val = las.well.get("NULL", {}).get("value", -999.25)
    try:
        null_val = float(null_val)
        for curve in las.curves:
            null_count = np.sum(curve.data == null_val)
            if null_count > 0:
                pct = 100 * null_count / len(curve.data)
                if pct > 50:
                    report["warnings"].append(
                        f"Curve {curve.mnemonic}: {pct:.1f}% null values"
                    )
    except (ValueError, TypeError):
        report["warnings"].append(f"Invalid NULL value: {null_val}")

    # Check for duplicate curve names
    names = [c.mnemonic for c in las.curves]
    seen = set()
    duplicates = [n for n in names if n in seen or seen.add(n)]
    if duplicates:
        report["warnings"].append(f"Duplicate curve names: {duplicates}")

    # Check curves have units
    for curve in las.curves:
        if not curve.unit:
            report["warnings"].append(f"Curve {curve.mnemonic} has no unit")

    return report


def print_report(filepath: str, report: dict) -> None:
    """Print validation report."""
    status = "VALID" if report["valid"] else "INVALID"
    print(f"\n{'='*60}")
    print(f"File: {filepath}")
    print(f"Status: {status}")
    print(f"{'='*60}")

    if report["info"]:
        print("\nInfo:")
        for key, value in report["info"].items():
            print(f"  {key}: {value}")

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
    parser = argparse.ArgumentParser(description="Validate LAS files")
    parser.add_argument("path", help="LAS file or directory to validate")
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Recursively search directories"
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
    for filepath in files:
        report = validate_las(str(filepath))
        print_report(str(filepath), report)
        if report["valid"]:
            valid_count += 1

    print(f"\n{'='*60}")
    print(f"Summary: {valid_count}/{len(files)} files valid")


if __name__ == "__main__":
    main()
