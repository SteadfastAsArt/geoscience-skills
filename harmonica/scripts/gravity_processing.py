#!/usr/bin/env python3
"""
Process gravity survey data: apply corrections and compute anomalies.

Usage:
    python gravity_processing.py <input.csv> <dem.nc> [--output output.csv]
    python gravity_processing.py --example

Input CSV must have columns: longitude, latitude, height, observed_gravity
DEM must be a NetCDF file with easting, northing coordinates
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def load_gravity_data(filepath: str) -> pd.DataFrame:
    """
    Load gravity survey data from CSV.

    Expected columns: longitude, latitude, height, observed_gravity
    """
    df = pd.read_csv(filepath)

    required_cols = ["longitude", "latitude", "height", "observed_gravity"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return df


def calculate_normal_gravity(latitude: np.ndarray, height: np.ndarray) -> np.ndarray:
    """
    Calculate normal gravity using WGS84 ellipsoid.

    Args:
        latitude: Latitude in degrees
        height: Height above ellipsoid in meters

    Returns:
        Normal gravity in mGal
    """
    import boule as bl

    ellipsoid = bl.WGS84
    return ellipsoid.normal_gravity(latitude, height)


def calculate_free_air_anomaly(
    observed: np.ndarray, normal: np.ndarray
) -> np.ndarray:
    """
    Calculate free-air anomaly.

    Args:
        observed: Observed gravity in mGal
        normal: Normal gravity in mGal

    Returns:
        Free-air anomaly in mGal
    """
    return observed - normal


def calculate_bouguer_correction(
    height: np.ndarray, density: float = 2670.0
) -> np.ndarray:
    """
    Calculate simple Bouguer correction.

    Args:
        height: Height in meters
        density: Density in kg/m3 (default: 2670)

    Returns:
        Bouguer correction in mGal
    """
    import harmonica as hm

    return hm.bouguer_correction(height, density=density)


def calculate_terrain_correction(
    easting: np.ndarray,
    northing: np.ndarray,
    height: np.ndarray,
    dem_path: str,
    density: float = 2670.0,
) -> np.ndarray:
    """
    Calculate terrain correction using prism layer.

    Args:
        easting, northing, height: Observation coordinates in meters
        dem_path: Path to DEM NetCDF file
        density: Rock density in kg/m3

    Returns:
        Terrain correction in mGal
    """
    import harmonica as hm
    import xarray as xr

    # Load DEM
    topo = xr.open_dataarray(dem_path)

    # Create prism layer
    layer = hm.prism_layer(
        (topo.easting.values, topo.northing.values),
        surface=topo.values,
        reference=0,
        properties={"density": density},
    )

    # Calculate terrain effect
    coordinates = (easting, northing, height)
    terrain_effect = layer.gravity(coordinates, field="g_z")

    return terrain_effect


def project_coordinates(
    longitude: np.ndarray, latitude: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """
    Project geographic coordinates to local Cartesian (UTM).

    Args:
        longitude, latitude: Geographic coordinates in degrees

    Returns:
        easting, northing in meters
    """
    import verde as vd

    projection = vd.get_projection(longitude, latitude)
    easting, northing = projection(longitude, latitude)
    return easting, northing


def process_gravity(
    df: pd.DataFrame,
    dem_path: str | None = None,
    density: float = 2670.0,
) -> pd.DataFrame:
    """
    Apply gravity corrections and compute anomalies.

    Args:
        df: DataFrame with longitude, latitude, height, observed_gravity
        dem_path: Optional path to DEM for terrain correction
        density: Rock density for corrections (kg/m3)

    Returns:
        DataFrame with added correction and anomaly columns
    """
    result = df.copy()

    # Calculate normal gravity
    print("Calculating normal gravity...")
    result["normal_gravity"] = calculate_normal_gravity(
        df["latitude"].values, df["height"].values
    )

    # Free-air anomaly
    print("Calculating free-air anomaly...")
    result["free_air_anomaly"] = calculate_free_air_anomaly(
        df["observed_gravity"].values, result["normal_gravity"].values
    )

    # Bouguer correction
    print("Calculating Bouguer correction...")
    result["bouguer_correction"] = calculate_bouguer_correction(
        df["height"].values, density=density
    )

    # Simple Bouguer anomaly
    result["simple_bouguer_anomaly"] = (
        result["free_air_anomaly"] - result["bouguer_correction"]
    )

    # Terrain correction (if DEM provided)
    if dem_path is not None:
        print("Calculating terrain correction...")

        # Project coordinates
        easting, northing = project_coordinates(
            df["longitude"].values, df["latitude"].values
        )
        result["easting"] = easting
        result["northing"] = northing

        result["terrain_correction"] = calculate_terrain_correction(
            easting, northing, df["height"].values, dem_path, density=density
        )

        # Complete Bouguer anomaly
        result["complete_bouguer_anomaly"] = (
            result["simple_bouguer_anomaly"] + result["terrain_correction"]
        )

    return result


def create_example_data() -> pd.DataFrame:
    """Create example gravity survey data."""
    np.random.seed(42)

    n_points = 50
    lon_center, lat_center = -25.0, -15.0

    df = pd.DataFrame(
        {
            "station": [f"S{i:03d}" for i in range(n_points)],
            "longitude": lon_center + 0.5 * (np.random.rand(n_points) - 0.5),
            "latitude": lat_center + 0.5 * (np.random.rand(n_points) - 0.5),
            "height": 500 + 200 * np.random.rand(n_points),
            "observed_gravity": 978000 + 100 * np.random.randn(n_points),
        }
    )

    return df


def print_summary(df: pd.DataFrame) -> None:
    """Print summary statistics."""
    print("\n" + "=" * 60)
    print("Processing Summary")
    print("=" * 60)

    print(f"\nNumber of stations: {len(df)}")

    stats_cols = [
        "observed_gravity",
        "free_air_anomaly",
        "simple_bouguer_anomaly",
    ]
    if "complete_bouguer_anomaly" in df.columns:
        stats_cols.append("complete_bouguer_anomaly")

    print("\nStatistics (mGal):")
    print("-" * 60)
    for col in stats_cols:
        if col in df.columns:
            print(
                f"{col:30s}: "
                f"min={df[col].min():10.2f}, "
                f"max={df[col].max():10.2f}, "
                f"mean={df[col].mean():10.2f}"
            )


def main():
    parser = argparse.ArgumentParser(
        description="Process gravity survey data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input", nargs="?", help="Input CSV file")
    parser.add_argument("dem", nargs="?", help="DEM NetCDF file (optional)")
    parser.add_argument("-o", "--output", help="Output CSV file")
    parser.add_argument(
        "--density",
        type=float,
        default=2670.0,
        help="Rock density kg/m3 (default: 2670)",
    )
    parser.add_argument(
        "--example",
        action="store_true",
        help="Run with example data",
    )

    args = parser.parse_args()

    if args.example:
        print("Creating example data...")
        df = create_example_data()
        df.to_csv("example_gravity_input.csv", index=False)
        print("Saved example input to: example_gravity_input.csv")
        args.input = "example_gravity_input.csv"
        args.dem = None
        args.output = "example_gravity_output.csv"

    if args.input is None:
        parser.print_help()
        sys.exit(1)

    # Load data
    print(f"Loading data from: {args.input}")
    df = load_gravity_data(args.input)
    print(f"Loaded {len(df)} stations")

    # Process
    result = process_gravity(df, dem_path=args.dem, density=args.density)

    # Print summary
    print_summary(result)

    # Save output
    if args.output:
        output_path = Path(args.output)
        result.to_csv(output_path, index=False)
        print(f"\nSaved results to: {output_path}")

    return result


if __name__ == "__main__":
    main()
