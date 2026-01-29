#!/usr/bin/env python3
"""
MT data analysis and quality control.

Usage:
    python mt_analysis.py <file.edi>
    python mt_analysis.py <directory> --recursive
    python mt_analysis.py <file.edi> --plot
    python mt_analysis.py <file.edi> --export csv
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def analyze_mt(filepath: str, plot: bool = False) -> dict:
    """
    Analyze MT data from an EDI file and return a report.

    Args:
        filepath: Path to EDI file
        plot: Whether to generate plots

    Returns:
        dict with keys: valid, errors, warnings, info, data
    """
    from mtpy import MT

    report = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "info": {},
        "data": {},
    }

    # Try to read the file
    try:
        mt = MT(filepath)
    except Exception as e:
        report["valid"] = False
        report["errors"].append(f"Failed to read file: {e}")
        return report

    # Basic info
    report["info"]["station"] = mt.station
    report["info"]["latitude"] = mt.latitude
    report["info"]["longitude"] = mt.longitude
    report["info"]["elevation"] = getattr(mt, "elevation", None)
    report["info"]["n_frequencies"] = len(mt.frequency)

    if len(mt.frequency) > 0:
        report["info"]["frequency_range"] = (
            f"{mt.frequency.min():.4f} - {mt.frequency.max():.2f} Hz"
        )
        report["info"]["period_range"] = (
            f"{1/mt.frequency.max():.4f} - {1/mt.frequency.min():.2f} s"
        )

    # Check for tipper
    report["info"]["has_tipper"] = mt.has_tipper

    # Data quality checks
    if len(mt.frequency) == 0:
        report["errors"].append("No frequency data")
        report["valid"] = False
        return report

    # Check impedance quality
    Z = mt.Z
    Z_err = mt.Z_err

    # Calculate relative errors
    with np.errstate(divide="ignore", invalid="ignore"):
        rel_err_xy = np.abs(Z_err[:, 0, 1]) / np.abs(Z[:, 0, 1])
        rel_err_yx = np.abs(Z_err[:, 1, 0]) / np.abs(Z[:, 1, 0])

    # Count bad data points (relative error > 50%)
    bad_xy = np.sum(rel_err_xy > 0.5)
    bad_yx = np.sum(rel_err_yx > 0.5)
    n_freq = len(mt.frequency)

    if bad_xy > n_freq * 0.3:
        report["warnings"].append(
            f"Zxy: {bad_xy}/{n_freq} points have >50% relative error"
        )

    if bad_yx > n_freq * 0.3:
        report["warnings"].append(
            f"Zyx: {bad_yx}/{n_freq} points have >50% relative error"
        )

    # Check for NaN/Inf values
    if np.any(~np.isfinite(Z)):
        nan_count = np.sum(~np.isfinite(Z))
        report["warnings"].append(f"{nan_count} NaN/Inf values in impedance tensor")

    # Check frequency spacing
    log_freq = np.log10(mt.frequency)
    freq_spacing = np.diff(log_freq)
    if np.std(freq_spacing) > 0.1 * np.mean(np.abs(freq_spacing)):
        report["warnings"].append("Irregular frequency spacing detected")

    # Phase tensor analysis
    try:
        pt = mt.phase_tensor
        skew = pt.skew

        # Check for 3D effects
        max_skew = np.nanmax(np.abs(skew))
        if max_skew > 5:
            report["warnings"].append(
                f"Max |skew| = {max_skew:.1f} deg suggests 3D structure"
            )

        report["info"]["max_skew"] = f"{max_skew:.2f} deg"
    except Exception:
        report["warnings"].append("Could not compute phase tensor")

    # Apparent resistivity range check
    rho_xy = mt.apparent_resistivity[:, 0, 1]
    rho_yx = mt.apparent_resistivity[:, 1, 0]

    valid_rho = rho_xy[(rho_xy > 0) & np.isfinite(rho_xy)]
    if len(valid_rho) > 0:
        report["info"]["resistivity_range_xy"] = (
            f"{np.min(valid_rho):.2f} - {np.max(valid_rho):.2f} Ohm-m"
        )

    valid_rho = rho_yx[(rho_yx > 0) & np.isfinite(rho_yx)]
    if len(valid_rho) > 0:
        report["info"]["resistivity_range_yx"] = (
            f"{np.min(valid_rho):.2f} - {np.max(valid_rho):.2f} Ohm-m"
        )

    # Store data summary
    report["data"]["frequency"] = mt.frequency
    report["data"]["apparent_resistivity_xy"] = rho_xy
    report["data"]["apparent_resistivity_yx"] = rho_yx
    report["data"]["phase_xy"] = mt.phase[:, 0, 1]
    report["data"]["phase_yx"] = mt.phase[:, 1, 0]

    # Generate plots if requested
    if plot:
        try:
            from mtpy.imaging import PlotMTResponse

            plot_obj = PlotMTResponse(mt)
            plot_obj.plot()
            plot_filename = Path(filepath).stem + "_response.png"
            plot_obj.save_figure(plot_filename, dpi=150)
            report["info"]["plot_saved"] = plot_filename
        except Exception as e:
            report["warnings"].append(f"Could not generate plot: {e}")

    return report


def export_data(filepath: str, format: str = "csv") -> str:
    """
    Export MT data to specified format.

    Args:
        filepath: Path to EDI file
        format: Output format ('csv', 'excel')

    Returns:
        Path to exported file
    """
    from mtpy import MT

    mt = MT(filepath)

    df = pd.DataFrame(
        {
            "frequency_hz": mt.frequency,
            "period_s": 1 / mt.frequency,
            "rho_xy_ohm_m": mt.apparent_resistivity[:, 0, 1],
            "rho_yx_ohm_m": mt.apparent_resistivity[:, 1, 0],
            "phase_xy_deg": mt.phase[:, 0, 1],
            "phase_yx_deg": mt.phase[:, 1, 0],
            "z_xy_real": mt.Z[:, 0, 1].real,
            "z_xy_imag": mt.Z[:, 0, 1].imag,
            "z_yx_real": mt.Z[:, 1, 0].real,
            "z_yx_imag": mt.Z[:, 1, 0].imag,
            "z_xy_err": mt.Z_err[:, 0, 1],
            "z_yx_err": mt.Z_err[:, 1, 0],
        }
    )

    stem = Path(filepath).stem

    if format == "csv":
        output_path = f"{stem}_data.csv"
        df.to_csv(output_path, index=False)
    elif format == "excel":
        output_path = f"{stem}_data.xlsx"
        df.to_excel(output_path, index=False, sheet_name="MT_Data")
    else:
        raise ValueError(f"Unknown format: {format}")

    return output_path


def print_report(filepath: str, report: dict) -> None:
    """Print analysis report."""
    status = "VALID" if report["valid"] else "INVALID"
    print(f"\n{'='*60}")
    print(f"File: {filepath}")
    print(f"Status: {status}")
    print(f"{'='*60}")

    if report["info"]:
        print("\nStation Information:")
        for key, value in report["info"].items():
            if value is not None:
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
    parser = argparse.ArgumentParser(description="Analyze MT/EDI files")
    parser.add_argument("path", help="EDI file or directory to analyze")
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Recursively search directories"
    )
    parser.add_argument(
        "-p", "--plot", action="store_true", help="Generate response plots"
    )
    parser.add_argument(
        "-e",
        "--export",
        choices=["csv", "excel"],
        help="Export data to specified format",
    )
    args = parser.parse_args()

    path = Path(args.path)

    if path.is_file():
        files = [path]
    elif path.is_dir():
        pattern = "**/*.edi" if args.recursive else "*.edi"
        files = list(path.glob(pattern))
        if not files:
            # Try uppercase extension
            pattern = "**/*.EDI" if args.recursive else "*.EDI"
            files = list(path.glob(pattern))
    else:
        print(f"Error: {path} not found")
        sys.exit(1)

    if not files:
        print("No EDI files found")
        sys.exit(1)

    valid_count = 0
    for filepath in sorted(files):
        report = analyze_mt(str(filepath), plot=args.plot)
        print_report(str(filepath), report)
        if report["valid"]:
            valid_count += 1

        if args.export and report["valid"]:
            try:
                output = export_data(str(filepath), args.export)
                print(f"  Exported to: {output}")
            except Exception as e:
                print(f"  Export failed: {e}")

    print(f"\n{'='*60}")
    print(f"Summary: {valid_count}/{len(files)} files valid")


if __name__ == "__main__":
    main()
