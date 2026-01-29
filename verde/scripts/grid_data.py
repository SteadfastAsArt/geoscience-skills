#!/usr/bin/env python3
"""
Grid scattered spatial data to a regular grid using Verde.

Usage:
    python grid_data.py <input.csv> <output.nc> --spacing 0.1
    python grid_data.py <input.csv> <output.nc> --spacing 1000 --project
    python grid_data.py <input.csv> <output.nc> --gridder linear

Input CSV must have columns: longitude, latitude, value
(or specify with --lon-col, --lat-col, --value-col)
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import verde as vd


def load_data(filepath: str, lon_col: str, lat_col: str, value_col: str) -> tuple:
    """
    Load data from CSV file.

    Returns:
        tuple: (coordinates, values) where coordinates = (lon, lat)
    """
    df = pd.read_csv(filepath)

    # Validate columns exist
    for col in [lon_col, lat_col, value_col]:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found. Available: {list(df.columns)}")

    # Remove rows with NaN
    df = df[[lon_col, lat_col, value_col]].dropna()

    coordinates = (df[lon_col].values, df[lat_col].values)
    values = df[value_col].values

    return coordinates, values


def create_gridder(gridder_type: str, damping: float = None) -> object:
    """
    Create a verde gridder based on type.

    Args:
        gridder_type: One of 'spline', 'linear', 'cubic'
        damping: Damping parameter for spline

    Returns:
        Verde gridder object
    """
    gridders = {
        "spline": vd.Spline(damping=damping),
        "linear": vd.Linear(),
        "cubic": vd.Cubic(),
    }

    if gridder_type not in gridders:
        raise ValueError(f"Unknown gridder: {gridder_type}. Use: {list(gridders.keys())}")

    return gridders[gridder_type]


def grid_data(
    coordinates: tuple,
    values: np.ndarray,
    spacing: float,
    gridder_type: str = "spline",
    damping: float = None,
    region: tuple = None,
    block_reduce: float = None,
    remove_trend: int = None,
    mask_distance: float = None,
    project: bool = False,
) -> object:
    """
    Grid scattered data using Verde.

    Args:
        coordinates: (longitude, latitude) tuple of arrays
        values: 1D array of values to grid
        spacing: Grid spacing (degrees or meters if projected)
        gridder_type: Type of gridder ('spline', 'linear', 'cubic')
        damping: Damping for spline gridder
        region: (west, east, south, north) or None to infer
        block_reduce: Block size for decimation (None to skip)
        remove_trend: Polynomial degree for trend removal (None to skip)
        mask_distance: Max distance from data for masking (None to skip)
        project: Whether to project to Cartesian coordinates

    Returns:
        xarray Dataset with gridded data
    """
    import pyproj

    # Project to Cartesian if requested
    if project:
        lat_mean = np.mean(coordinates[1])
        projection = pyproj.Proj(proj="merc", lat_ts=lat_mean)
        proj_coords = projection(coordinates[0], coordinates[1])
        work_coords = proj_coords
    else:
        projection = None
        work_coords = coordinates

    # Build processing chain
    chain_steps = []

    # Optional trend removal
    if remove_trend is not None:
        chain_steps.append(("trend", vd.Trend(degree=remove_trend)))

    # Optional block reduction
    if block_reduce is not None:
        chain_steps.append(
            ("reduce", vd.BlockReduce(reduction=np.median, spacing=block_reduce))
        )

    # Main gridder
    gridder = create_gridder(gridder_type, damping)
    chain_steps.append(("gridder", gridder))

    # Create chain or use single gridder
    if len(chain_steps) > 1:
        processor = vd.Chain(chain_steps)
    else:
        processor = gridder

    # Fit the processor
    processor.fit(work_coords, values)

    # Create grid
    grid = processor.grid(
        region=region,
        spacing=spacing,
        data_names=["values"],
        projection=projection,
    )

    # Optional distance mask
    if mask_distance is not None:
        mask = vd.distance_mask(work_coords, maxdist=mask_distance, grid=grid)
        grid = grid.where(mask)

    return grid


def main():
    parser = argparse.ArgumentParser(
        description="Grid scattered spatial data using Verde",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic gridding with default spline
    python grid_data.py data.csv output.nc --spacing 0.1

    # Project to meters and grid at 1km
    python grid_data.py data.csv output.nc --spacing 1000 --project

    # Use linear interpolation
    python grid_data.py data.csv output.nc --spacing 0.1 --gridder linear

    # Remove trend and reduce before gridding
    python grid_data.py data.csv output.nc --spacing 0.05 --trend 1 --reduce 0.1

    # Mask areas far from data
    python grid_data.py data.csv output.nc --spacing 0.1 --mask 0.2
        """,
    )

    parser.add_argument("input", help="Input CSV file")
    parser.add_argument("output", help="Output NetCDF file")
    parser.add_argument(
        "--spacing", type=float, required=True, help="Grid spacing (degrees or meters)"
    )
    parser.add_argument(
        "--gridder",
        choices=["spline", "linear", "cubic"],
        default="spline",
        help="Gridding method (default: spline)",
    )
    parser.add_argument("--damping", type=float, help="Damping for spline gridder")
    parser.add_argument(
        "--project", action="store_true", help="Project to Cartesian coordinates"
    )
    parser.add_argument(
        "--reduce", type=float, help="Block reduce spacing before gridding"
    )
    parser.add_argument("--trend", type=int, help="Remove polynomial trend of this degree")
    parser.add_argument(
        "--mask", type=float, help="Mask areas farther than this from data"
    )
    parser.add_argument(
        "--region",
        nargs=4,
        type=float,
        metavar=("W", "E", "S", "N"),
        help="Grid region (west east south north)",
    )
    parser.add_argument("--lon-col", default="longitude", help="Longitude column name")
    parser.add_argument("--lat-col", default="latitude", help="Latitude column name")
    parser.add_argument("--value-col", default="value", help="Value column name")

    args = parser.parse_args()

    # Validate paths
    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # Load data
    print(f"Loading data from {args.input}...")
    try:
        coordinates, values = load_data(
            args.input, args.lon_col, args.lat_col, args.value_col
        )
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

    print(f"  Loaded {len(values)} points")
    print(f"  Longitude range: {coordinates[0].min():.4f} to {coordinates[0].max():.4f}")
    print(f"  Latitude range: {coordinates[1].min():.4f} to {coordinates[1].max():.4f}")
    print(f"  Value range: {values.min():.4f} to {values.max():.4f}")

    # Grid the data
    print(f"\nGridding with {args.gridder}...")
    region = tuple(args.region) if args.region else None

    try:
        grid = grid_data(
            coordinates=coordinates,
            values=values,
            spacing=args.spacing,
            gridder_type=args.gridder,
            damping=args.damping,
            region=region,
            block_reduce=args.reduce,
            remove_trend=args.trend,
            mask_distance=args.mask,
            project=args.project,
        )
    except Exception as e:
        print(f"Error during gridding: {e}")
        sys.exit(1)

    # Report grid info
    print(f"\nGrid created:")
    print(f"  Shape: {grid.values.shape}")
    print(f"  Value range: {float(grid.values.min()):.4f} to {float(grid.values.max()):.4f}")

    # Save
    print(f"\nSaving to {args.output}...")
    grid.to_netcdf(args.output)
    print("Done!")


if __name__ == "__main__":
    main()
