#!/usr/bin/env python3
"""
Batch process seismic waveform files.

Usage:
    python batch_process.py data/*.mseed --output processed/
    python batch_process.py data/ --filter bandpass --freqmin 1 --freqmax 10
    python batch_process.py data/ --remove-response --inventory stations.xml
    python batch_process.py data/ --decimate 2 --output downsampled/
"""

import argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Optional

from obspy import read, read_inventory


def process_file(
    filepath: str,
    output_dir: str,
    detrend: bool = True,
    taper: float = 0.05,
    filter_type: str = None,
    freqmin: float = None,
    freqmax: float = None,
    freq: float = None,
    decimate_factor: int = None,
    remove_response: bool = False,
    inventory_path: str = None,
    output_format: str = "MSEED",
    output_units: str = "VEL",
) -> dict:
    """
    Process a single seismic file.

    Args:
        filepath: Path to input file
        output_dir: Output directory
        detrend: Apply detrend (demean + linear)
        taper: Taper percentage (0-0.5)
        filter_type: Filter type (bandpass, highpass, lowpass)
        freqmin: Minimum frequency for bandpass/highpass
        freqmax: Maximum frequency for bandpass/lowpass
        freq: Frequency for highpass/lowpass
        decimate_factor: Decimation factor
        remove_response: Remove instrument response
        inventory_path: Path to inventory file for response removal
        output_format: Output format (MSEED, SAC, etc.)
        output_units: Output units for response removal (VEL, DISP, ACC)

    Returns:
        dict with status and info
    """
    result = {
        "file": filepath,
        "status": "success",
        "output": None,
        "error": None,
    }

    try:
        st = read(filepath)

        # Basic processing
        if detrend:
            st.detrend("demean")
            st.detrend("linear")

        if taper and taper > 0:
            st.taper(max_percentage=taper)

        # Remove instrument response
        if remove_response:
            if inventory_path:
                inv = read_inventory(inventory_path)
            else:
                # Try to get from IRIS
                from obspy.clients.fdsn import Client
                client = Client("IRIS")
                inv = client.get_stations(
                    network=st[0].stats.network,
                    station=st[0].stats.station,
                    starttime=st[0].stats.starttime,
                    endtime=st[0].stats.endtime,
                    level="response",
                )
            st.remove_response(inventory=inv, output=output_units)

        # Apply filter
        if filter_type:
            if filter_type == "bandpass":
                st.filter("bandpass", freqmin=freqmin, freqmax=freqmax)
            elif filter_type == "highpass":
                st.filter("highpass", freq=freq or freqmin)
            elif filter_type == "lowpass":
                st.filter("lowpass", freq=freq or freqmax)

        # Decimate
        if decimate_factor and decimate_factor > 1:
            st.decimate(factor=decimate_factor)

        # Write output
        output_path = Path(output_dir)
        input_path = Path(filepath)

        # Determine output extension
        ext_map = {
            "MSEED": ".mseed",
            "SAC": ".sac",
            "GSE2": ".gse",
            "SEGY": ".sgy",
        }
        ext = ext_map.get(output_format, ".mseed")

        output_file = output_path / (input_path.stem + ext)
        st.write(str(output_file), format=output_format)

        result["output"] = str(output_file)
        result["n_traces"] = len(st)
        result["sampling_rate"] = st[0].stats.sampling_rate
        result["duration"] = st[0].stats.endtime - st[0].stats.starttime

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def batch_process(
    input_path: str,
    output_dir: str,
    workers: int = 4,
    **kwargs,
) -> list:
    """
    Batch process multiple seismic files.

    Args:
        input_path: Input file or directory
        output_dir: Output directory
        workers: Number of parallel workers
        **kwargs: Arguments passed to process_file

    Returns:
        List of result dicts
    """
    input_path = Path(input_path)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Collect files
    if input_path.is_file():
        files = [input_path]
    elif input_path.is_dir():
        files = list(input_path.glob("*.mseed")) + \
                list(input_path.glob("*.sac")) + \
                list(input_path.glob("*.seed"))
    else:
        # Treat as glob pattern
        files = list(Path(".").glob(str(input_path)))

    if not files:
        print("No files found")
        return []

    print(f"Processing {len(files)} files with {workers} workers...")

    results = []

    if workers == 1:
        # Sequential processing
        for i, f in enumerate(files, 1):
            print(f"  [{i}/{len(files)}] {f.name}...", end=" ")
            result = process_file(str(f), str(output_path), **kwargs)
            results.append(result)
            print(result["status"])
    else:
        # Parallel processing
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(process_file, str(f), str(output_path), **kwargs): f
                for f in files
            }

            for future in as_completed(futures):
                f = futures[future]
                result = future.result()
                results.append(result)
                status = result["status"]
                print(f"  {f.name}: {status}")

    # Summary
    success = sum(1 for r in results if r["status"] == "success")
    errors = sum(1 for r in results if r["status"] == "error")
    print(f"\nCompleted: {success} success, {errors} errors")

    if errors > 0:
        print("\nErrors:")
        for r in results:
            if r["status"] == "error":
                print(f"  {r['file']}: {r['error']}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Batch process seismic waveform files"
    )

    parser.add_argument("input", help="Input file, directory, or glob pattern")
    parser.add_argument(
        "--output", "-o", default="processed", help="Output directory (default: processed)"
    )
    parser.add_argument(
        "--workers", "-w", type=int, default=4, help="Parallel workers (default: 4)"
    )

    # Processing options
    proc_group = parser.add_argument_group("Processing options")
    proc_group.add_argument(
        "--no-detrend", action="store_true", help="Skip detrend step"
    )
    proc_group.add_argument(
        "--taper", type=float, default=0.05, help="Taper percentage (default: 0.05)"
    )
    proc_group.add_argument(
        "--decimate", type=int, help="Decimation factor"
    )

    # Filter options
    filter_group = parser.add_argument_group("Filter options")
    filter_group.add_argument(
        "--filter", "-f", choices=["bandpass", "highpass", "lowpass"],
        help="Filter type"
    )
    filter_group.add_argument(
        "--freqmin", type=float, help="Minimum frequency (Hz)"
    )
    filter_group.add_argument(
        "--freqmax", type=float, help="Maximum frequency (Hz)"
    )
    filter_group.add_argument(
        "--freq", type=float, help="Corner frequency for highpass/lowpass"
    )

    # Response removal
    resp_group = parser.add_argument_group("Response removal")
    resp_group.add_argument(
        "--remove-response", "-r", action="store_true",
        help="Remove instrument response"
    )
    resp_group.add_argument(
        "--inventory", "-i", help="Path to StationXML inventory file"
    )
    resp_group.add_argument(
        "--units", choices=["VEL", "DISP", "ACC"], default="VEL",
        help="Output units (default: VEL)"
    )

    # Output options
    out_group = parser.add_argument_group("Output options")
    out_group.add_argument(
        "--format", choices=["MSEED", "SAC", "GSE2", "SEGY"],
        default="MSEED", help="Output format (default: MSEED)"
    )

    args = parser.parse_args()

    # Validate filter arguments
    if args.filter == "bandpass" and (args.freqmin is None or args.freqmax is None):
        parser.error("Bandpass filter requires --freqmin and --freqmax")
    if args.filter == "highpass" and args.freqmin is None and args.freq is None:
        parser.error("Highpass filter requires --freqmin or --freq")
    if args.filter == "lowpass" and args.freqmax is None and args.freq is None:
        parser.error("Lowpass filter requires --freqmax or --freq")

    batch_process(
        input_path=args.input,
        output_dir=args.output,
        workers=args.workers,
        detrend=not args.no_detrend,
        taper=args.taper,
        filter_type=args.filter,
        freqmin=args.freqmin,
        freqmax=args.freqmax,
        freq=args.freq,
        decimate_factor=args.decimate,
        remove_response=args.remove_response,
        inventory_path=args.inventory,
        output_format=args.format,
        output_units=args.units,
    )


if __name__ == "__main__":
    main()
