#!/usr/bin/env python3
"""
Prepare spatial data for GemPy geological modeling.

Usage:
    python prepare_gempy_data.py --contacts contacts.shp --orientations orientations.shp --dem dem.tif --output-dir output/
    python prepare_gempy_data.py --contacts contacts.shp --dem dem.tif --extent "500000,510000,5600000,5610000"
"""

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

try:
    import gemgis as gg
except ImportError:
    print("Error: gemgis is required. Install with: pip install gemgis")
    sys.exit(1)


def load_and_validate_vector(filepath: str, required_cols: list = None) -> gpd.GeoDataFrame:
    """Load vector file and validate required columns exist."""
    gdf = gpd.read_file(filepath)

    if required_cols:
        missing = [col for col in required_cols if col not in gdf.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    # Check for valid geometries
    invalid_count = (~gdf.is_valid).sum()
    if invalid_count > 0:
        print(f"Warning: {invalid_count} invalid geometries found, attempting repair...")
        gdf['geometry'] = gdf['geometry'].buffer(0)

    return gdf


def extract_interfaces(contacts_gdf: gpd.GeoDataFrame,
                       dem_path: str,
                       formation_col: str = 'formation') -> pd.DataFrame:
    """Extract interface points from contact lines."""

    # Extract XYZ from contact geometries
    interfaces = gg.vector.extract_xyz(gdf=contacts_gdf, dem=dem_path)

    # Add formation information
    if formation_col in contacts_gdf.columns:
        # Map formation to extracted points based on index
        interfaces['formation'] = contacts_gdf.loc[interfaces.index, formation_col].values
    else:
        print(f"Warning: '{formation_col}' column not found, using 'Unknown'")
        interfaces['formation'] = 'Unknown'

    # Clean up columns for GemPy
    interfaces = interfaces[['X', 'Y', 'Z', 'formation']].copy()

    # Remove any NaN values
    nan_count = interfaces.isna().any(axis=1).sum()
    if nan_count > 0:
        print(f"Warning: Removing {nan_count} points with NaN values")
        interfaces = interfaces.dropna()

    return interfaces


def extract_orientations(orientations_gdf: gpd.GeoDataFrame,
                         dem_path: str,
                         formation_col: str = 'formation',
                         dip_col: str = 'dip',
                         azimuth_col: str = 'azimuth',
                         strike_col: str = 'strike') -> pd.DataFrame:
    """Extract orientation data from structural measurements."""

    # Extract XYZ
    orientations = gg.vector.extract_xyz(gdf=orientations_gdf, dem=dem_path)

    # Add formation
    if formation_col in orientations_gdf.columns:
        orientations['formation'] = orientations_gdf.loc[orientations.index, formation_col].values
    else:
        orientations['formation'] = 'Unknown'

    # Add dip
    if dip_col in orientations_gdf.columns:
        orientations['dip'] = orientations_gdf.loc[orientations.index, dip_col].values
    else:
        raise ValueError(f"Dip column '{dip_col}' not found in data")

    # Add azimuth (dip direction)
    if azimuth_col in orientations_gdf.columns:
        orientations['azimuth'] = orientations_gdf.loc[orientations.index, azimuth_col].values
    elif strike_col in orientations_gdf.columns:
        # Convert strike to azimuth (right-hand rule: azimuth = strike + 90)
        strike = orientations_gdf.loc[orientations.index, strike_col].values
        orientations['azimuth'] = (strike + 90) % 360
    else:
        raise ValueError(f"Neither '{azimuth_col}' nor '{strike_col}' found in data")

    # Add polarity (default to normal)
    orientations['polarity'] = 1

    # Validate ranges
    if not ((orientations['dip'] >= 0) & (orientations['dip'] <= 90)).all():
        print("Warning: Some dip values outside 0-90 range, clamping...")
        orientations['dip'] = orientations['dip'].clip(0, 90)

    if not ((orientations['azimuth'] >= 0) & (orientations['azimuth'] < 360)).all():
        orientations['azimuth'] = orientations['azimuth'] % 360

    # Clean up columns for GemPy
    orientations = orientations[['X', 'Y', 'Z', 'azimuth', 'dip', 'polarity', 'formation']].copy()

    # Remove NaN values
    nan_count = orientations.isna().any(axis=1).sum()
    if nan_count > 0:
        print(f"Warning: Removing {nan_count} orientations with NaN values")
        orientations = orientations.dropna()

    return orientations


def clip_to_extent(gdf: gpd.GeoDataFrame, extent: list) -> gpd.GeoDataFrame:
    """Clip GeoDataFrame to specified extent [xmin, xmax, ymin, ymax]."""
    from shapely.geometry import box
    extent_poly = box(extent[0], extent[2], extent[1], extent[3])
    return gdf.clip(extent_poly)


def print_summary(interfaces: pd.DataFrame, orientations: pd.DataFrame = None):
    """Print summary of prepared data."""
    print("\n" + "=" * 60)
    print("DATA PREPARATION SUMMARY")
    print("=" * 60)

    print(f"\nInterface Points: {len(interfaces)}")
    print(f"  Formations: {interfaces['formation'].nunique()}")
    for form in interfaces['formation'].unique():
        count = (interfaces['formation'] == form).sum()
        print(f"    - {form}: {count} points")

    print(f"\n  X range: {interfaces['X'].min():.1f} - {interfaces['X'].max():.1f}")
    print(f"  Y range: {interfaces['Y'].min():.1f} - {interfaces['Y'].max():.1f}")
    print(f"  Z range: {interfaces['Z'].min():.1f} - {interfaces['Z'].max():.1f}")

    if orientations is not None and len(orientations) > 0:
        print(f"\nOrientation Points: {len(orientations)}")
        print(f"  Formations: {orientations['formation'].nunique()}")
        print(f"  Dip range: {orientations['dip'].min():.1f} - {orientations['dip'].max():.1f}")
        print(f"  Azimuth range: {orientations['azimuth'].min():.1f} - {orientations['azimuth'].max():.1f}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Prepare spatial data for GemPy geological modeling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic usage with contacts only
    python prepare_gempy_data.py --contacts geology_contacts.shp --dem dem.tif

    # Full workflow with orientations
    python prepare_gempy_data.py --contacts contacts.shp --orientations orientations.shp --dem dem.tif --output-dir gempy_data/

    # Clip to specific extent
    python prepare_gempy_data.py --contacts contacts.shp --dem dem.tif --extent "500000,510000,5600000,5610000"
        """
    )

    parser.add_argument('--contacts', required=True, help='Path to contacts shapefile/GeoJSON')
    parser.add_argument('--orientations', help='Path to orientations shapefile/GeoJSON')
    parser.add_argument('--dem', required=True, help='Path to DEM raster (GeoTIFF)')
    parser.add_argument('--output-dir', default='.', help='Output directory (default: current)')
    parser.add_argument('--extent', help='Clip extent as "xmin,xmax,ymin,ymax"')
    parser.add_argument('--formation-col', default='formation', help='Formation column name')
    parser.add_argument('--dip-col', default='dip', help='Dip column name')
    parser.add_argument('--azimuth-col', default='azimuth', help='Azimuth column name')
    parser.add_argument('--strike-col', default='strike', help='Strike column name (if no azimuth)')
    parser.add_argument('--target-crs', help='Target CRS (e.g., EPSG:32632)')

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse extent if provided
    extent = None
    if args.extent:
        extent = [float(x) for x in args.extent.split(',')]
        if len(extent) != 4:
            print("Error: Extent must be 4 values: xmin,xmax,ymin,ymax")
            sys.exit(1)

    # Load contacts
    print(f"Loading contacts from: {args.contacts}")
    contacts = load_and_validate_vector(args.contacts)
    print(f"  Loaded {len(contacts)} features")

    # Reproject if needed
    if args.target_crs:
        print(f"Reprojecting to {args.target_crs}")
        contacts = contacts.to_crs(args.target_crs)

    # Clip to extent if provided
    if extent:
        print(f"Clipping to extent: {extent}")
        contacts = clip_to_extent(contacts, extent)
        print(f"  {len(contacts)} features after clipping")

    # Extract interfaces
    print("Extracting interface points...")
    interfaces = extract_interfaces(
        contacts,
        args.dem,
        formation_col=args.formation_col
    )

    # Process orientations if provided
    orientations = None
    if args.orientations:
        print(f"\nLoading orientations from: {args.orientations}")
        orient_gdf = load_and_validate_vector(args.orientations)
        print(f"  Loaded {len(orient_gdf)} features")

        if args.target_crs:
            orient_gdf = orient_gdf.to_crs(args.target_crs)

        if extent:
            orient_gdf = clip_to_extent(orient_gdf, extent)
            print(f"  {len(orient_gdf)} features after clipping")

        print("Extracting orientations...")
        orientations = extract_orientations(
            orient_gdf,
            args.dem,
            formation_col=args.formation_col,
            dip_col=args.dip_col,
            azimuth_col=args.azimuth_col,
            strike_col=args.strike_col
        )

    # Print summary
    print_summary(interfaces, orientations)

    # Save outputs
    interfaces_path = output_dir / 'interfaces.csv'
    interfaces.to_csv(interfaces_path, index=False)
    print(f"\nSaved interfaces to: {interfaces_path}")

    if orientations is not None:
        orientations_path = output_dir / 'orientations.csv'
        orientations.to_csv(orientations_path, index=False)
        print(f"Saved orientations to: {orientations_path}")

    # Save extent info
    extent_info = {
        'x_min': interfaces['X'].min(),
        'x_max': interfaces['X'].max(),
        'y_min': interfaces['Y'].min(),
        'y_max': interfaces['Y'].max(),
        'z_min': interfaces['Z'].min(),
        'z_max': interfaces['Z'].max(),
    }

    extent_path = output_dir / 'extent.txt'
    with open(extent_path, 'w') as f:
        f.write("# GemPy Model Extent\n")
        f.write(f"# extent = [{extent_info['x_min']:.1f}, {extent_info['x_max']:.1f}, "
                f"{extent_info['y_min']:.1f}, {extent_info['y_max']:.1f}, "
                f"{extent_info['z_min']:.1f}, {extent_info['z_max']:.1f}]\n\n")
        for key, value in extent_info.items():
            f.write(f"{key}={value:.1f}\n")
    print(f"Saved extent info to: {extent_path}")

    print("\nDone! Data is ready for GemPy.")


if __name__ == "__main__":
    main()
