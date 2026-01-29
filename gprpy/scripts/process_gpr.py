#!/usr/bin/env python3
"""
Process GPR data files with standard workflow.

Usage:
    python process_gpr.py <file.DZT>
    python process_gpr.py <directory> --recursive
    python process_gpr.py <file.DZT> --velocity 0.1 --output processed/
"""

import argparse
import sys
from pathlib import Path

import gprpy.gprpy as gp
import matplotlib.pyplot as plt


def process_gpr(
    filepath: str,
    output_dir: str = None,
    velocity: float = 0.1,
    dewow_window: int = 10,
    background_traces: int = 50,
    gain_power: float = 1.5,
    export_formats: list = None,
) -> dict:
    """
    Process a GPR file with standard workflow.

    Args:
        filepath: Path to GPR file
        output_dir: Output directory (default: same as input)
        velocity: Velocity in m/ns for depth conversion
        dewow_window: Window size for dewow filter (ns)
        background_traces: Number of traces for background removal
        gain_power: Exponent for time-power gain
        export_formats: List of export formats ['png', 'sgy', 'txt']

    Returns:
        dict with processing results and metadata
    """
    if export_formats is None:
        export_formats = ["png"]

    report = {
        "success": True,
        "errors": [],
        "warnings": [],
        "info": {},
        "output_files": [],
    }

    # Load data
    try:
        data = gp.gprpyProfile()
        data.importdata(filepath)
    except Exception as e:
        report["success"] = False
        report["errors"].append(f"Failed to load file: {e}")
        return report

    # Record basic info
    report["info"]["input_file"] = filepath
    report["info"]["n_traces"] = data.data.shape[1]
    report["info"]["n_samples"] = data.data.shape[0]
    report["info"]["time_range_ns"] = float(data.twtt.max())
    report["info"]["profile_length_m"] = float(data.profilePos.max())

    # Processing steps
    try:
        # Step 1: Dewow
        data.dewow(window=dewow_window)
        report["info"]["dewow_window"] = dewow_window

        # Step 2: Background removal
        if data.data.shape[1] > background_traces:
            data.remMeanTrace(ntraces=background_traces)
            report["info"]["background_traces"] = background_traces
        else:
            report["warnings"].append(
                f"Profile has fewer traces ({data.data.shape[1]}) than background window ({background_traces})"
            )

        # Step 3: Gain
        data.tpowGain(power=gain_power)
        report["info"]["gain_power"] = gain_power

        # Step 4: Set velocity for depth display
        data.setVelocity(velocity)
        report["info"]["velocity_m_ns"] = velocity
        report["info"]["max_depth_m"] = float(data.twtt.max() * velocity / 2)

    except Exception as e:
        report["success"] = False
        report["errors"].append(f"Processing failed: {e}")
        return report

    # Determine output paths
    input_path = Path(filepath)
    if output_dir:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = input_path.parent

    base_name = input_path.stem

    # Export results
    try:
        if "png" in export_formats:
            png_path = out_dir / f"{base_name}_processed.png"
            fig, ax = plt.subplots(figsize=(12, 6))
            data.showProfile(ax=ax, color="gray")
            ax.set_title(f"GPR Profile: {input_path.name}")
            plt.savefig(png_path, dpi=200, bbox_inches="tight")
            plt.close(fig)
            report["output_files"].append(str(png_path))

        if "sgy" in export_formats:
            sgy_path = out_dir / f"{base_name}_processed.sgy"
            data.exportSEGY(str(sgy_path))
            report["output_files"].append(str(sgy_path))

        if "txt" in export_formats:
            txt_path = out_dir / f"{base_name}_processed.txt"
            data.exportASCII(str(txt_path))
            report["output_files"].append(str(txt_path))

    except Exception as e:
        report["warnings"].append(f"Export warning: {e}")

    return report


def print_report(report: dict) -> None:
    """Print processing report."""
    status = "SUCCESS" if report["success"] else "FAILED"
    print(f"\n{'='*60}")
    print(f"File: {report['info'].get('input_file', 'Unknown')}")
    print(f"Status: {status}")
    print(f"{'='*60}")

    if report["info"]:
        print("\nProcessing Info:")
        for key, value in report["info"].items():
            if key != "input_file":
                print(f"  {key}: {value}")

    if report["output_files"]:
        print("\nOutput Files:")
        for f in report["output_files"]:
            print(f"  - {f}")

    if report["errors"]:
        print("\nErrors:")
        for error in report["errors"]:
            print(f"  - {error}")

    if report["warnings"]:
        print("\nWarnings:")
        for warning in report["warnings"]:
            print(f"  - {warning}")


def main():
    parser = argparse.ArgumentParser(
        description="Process GPR files with standard workflow"
    )
    parser.add_argument("path", help="GPR file or directory to process")
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Recursively search directories"
    )
    parser.add_argument(
        "-o", "--output", help="Output directory for processed files"
    )
    parser.add_argument(
        "-v", "--velocity", type=float, default=0.1, help="Velocity in m/ns (default: 0.1)"
    )
    parser.add_argument(
        "--dewow", type=int, default=10, help="Dewow window in ns (default: 10)"
    )
    parser.add_argument(
        "--background", type=int, default=50, help="Background removal traces (default: 50)"
    )
    parser.add_argument(
        "--gain", type=float, default=1.5, help="Gain power exponent (default: 1.5)"
    )
    parser.add_argument(
        "--format",
        nargs="+",
        choices=["png", "sgy", "txt"],
        default=["png"],
        help="Export formats (default: png)",
    )
    args = parser.parse_args()

    path = Path(args.path)

    # Find files to process
    if path.is_file():
        files = [path]
    elif path.is_dir():
        extensions = ["*.DZT", "*.dzt", "*.DT1", "*.dt1", "*.GPR", "*.gpr", "*.rd3", "*.sgy"]
        files = []
        for ext in extensions:
            pattern = f"**/{ext}" if args.recursive else ext
            files.extend(path.glob(pattern))
    else:
        print(f"Error: {path} not found")
        sys.exit(1)

    if not files:
        print("No GPR files found")
        sys.exit(1)

    print(f"Found {len(files)} GPR file(s) to process")

    # Process files
    success_count = 0
    for filepath in files:
        report = process_gpr(
            str(filepath),
            output_dir=args.output,
            velocity=args.velocity,
            dewow_window=args.dewow,
            background_traces=args.background,
            gain_power=args.gain,
            export_formats=args.format,
        )
        print_report(report)
        if report["success"]:
            success_count += 1

    print(f"\n{'='*60}")
    print(f"Summary: {success_count}/{len(files)} files processed successfully")


if __name__ == "__main__":
    main()
