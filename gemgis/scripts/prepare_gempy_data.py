#!/usr/bin/env python3
"""Extract DEM elevations in metres without losing vertex attributes or CRS."""
import argparse
import json
from pathlib import Path
import sys

import gemgis as gg
from rasterio.transform import rowcol
import geopandas as gpd
import numpy as np
import pandas as pd
from pyproj import CRS, Proj, Transformer
import rasterio
from shapely.geometry import box


def load_and_validate_vector(filepath, required_cols=None):
    gdf = gpd.read_file(filepath)
    validate_vector(gdf, required_cols or [])
    return gdf


def validate_vector(gdf, required_cols):
    if gdf.empty or gdf.crs is None:
        raise ValueError('Vector data must be nonempty with a known CRS')
    missing = set(required_cols) - set(gdf.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    if gdf.geometry.isna().any() or gdf.geometry.is_empty.any() or not gdf.is_valid.all():
        raise ValueError('Invalid/empty geometries require an explicit repair before extraction')
    if not gdf.geom_type.isin(['Point', 'LineString', 'MultiLineString']).all():
        raise ValueError('Only points and contact lines are supported')


def metric_crs(crs):
    if crs is None:
        raise ValueError('DEM must declare its CRS')
    crs = CRS.from_user_input(crs)
    if not crs.is_projected or any(not np.isclose(a.unit_conversion_factor, 1.) for a in crs.axis_info[:2]):
        raise ValueError('DEM must use a projected CRS with metre horizontal units; reproject the raster explicitly')
    return crs


def extract_points(gdf, dem_path, formation_col='formation', *, dem_z_unit):
    validate_vector(gdf, [formation_col])
    if gdf[formation_col].isna().any() or gdf[formation_col].astype(str).str.strip().eq('').any():
        raise ValueError('Formation labels cannot be missing')
    if dem_z_unit not in ('m', 'ft'):
        raise ValueError('Declare DEM vertical units as m or ft')
    with rasterio.open(dem_path) as dem:
        metric_crs(dem.crs)
        if dem.count != 1:
            raise ValueError('DEM must have exactly one band')
        # GemGIS preserves attributes while exploding vertices. Do not reassign
        # them by the original row index after extraction.
        projected = gdf.to_crs(dem.crs).copy()
        if projected.geometry.has_z.any():
            raise ValueError('DEM extraction requires 2D geometry; explicitly resolve existing Z values first')
        points = gg.vector.extract_xy(projected)
        xy = points[['X', 'Y']].to_numpy(dtype=float)
        if not np.isfinite(xy).all():
            raise ValueError('Coordinates must be finite')
        rows, cols = np.asarray(rowcol(dem.transform, xy[:, 0], xy[:, 1]))
        inside = (rows >= 0) & (rows < dem.height) & (cols >= 0) & (cols < dem.width)
        if not np.all(inside):
            raise ValueError(f'{np.count_nonzero(~inside)} vertices are outside the DEM')
        sampled = np.ma.vstack(list(dem.sample(xy, indexes=1, masked=True)))[:, 0]
        if np.ma.getmaskarray(sampled).any() or not np.isfinite(sampled.data).all():
            raise ValueError('DEM samples contain NoData/masked/nonfinite elevations')
        result = gg.vector.extract_xyz(gdf=points, dem=dem)
        result['Z'] = result['Z'].astype(float) * (0.3048 if dem_z_unit == 'ft' else 1.)
        # Explicit selection wins over an existing canonical label column.
        # rename would create duplicate 'formation' columns and export stale labels.
        if formation_col != 'formation':
            result['formation'] = result[formation_col]
        return result


def extract_interfaces(contacts_gdf, dem_path, formation_col='formation', *, dem_z_unit):
    result = extract_points(contacts_gdf, dem_path, formation_col, dem_z_unit=dem_z_unit)
    return pd.DataFrame(result[['X', 'Y', 'Z', 'formation']])


def extract_orientations(orientations_gdf, dem_path, formation_col='formation', dip_col='dip',
                         azimuth_col='azimuth', strike_col='strike', *, dem_z_unit, strike_convention=None,
                         azimuth_reference=None):
    if not orientations_gdf.geom_type.eq('Point').all():
        raise ValueError('Orientation measurements must be points')
    if dip_col not in orientations_gdf:
        raise ValueError(f'Missing dip column: {dip_col}')
    result = extract_points(orientations_gdf, dem_path, formation_col, dem_z_unit=dem_z_unit)
    dip = pd.to_numeric(result[dip_col], errors='raise').to_numpy(dtype=float)
    if not np.isfinite(dip).all() or np.any((dip < 0) | (dip > 90)):
        raise ValueError('Dip must be finite and between 0 and 90 degrees')
    if azimuth_col in result:
        azimuth = pd.to_numeric(result[azimuth_col], errors='raise').to_numpy(dtype=float)
    elif strike_col in result and strike_convention == 'rhr':
        azimuth = pd.to_numeric(result[strike_col], errors='raise').to_numpy(dtype=float) + 90
    else:
        raise ValueError('Supply dip-direction azimuth or explicitly declare right-hand-rule strike')
    if not np.isfinite(azimuth).all():
        raise ValueError('Azimuth must be finite')
    if azimuth_reference == 'true-north':
        crs = CRS.from_user_input(result.crs)
        lon, lat = Transformer.from_crs(crs, crs.geodetic_crs, always_xy=True).transform(result.X, result.Y)
        factors = Proj(crs).get_factors(lon, lat)
        # A meridian-convergence rotation preserves azimuth only for a locally
        # conformal projection. Other projections need a full orientation map.
        if not np.allclose(factors.angular_distortion, 0, atol=1e-5):
            raise ValueError('True-north conversion requires a locally conformal DEM projection')
        convergence = np.asarray(factors.meridian_convergence)
        if not np.isfinite(convergence).all():
            raise ValueError('Projection convergence is undefined at a measurement')
        azimuth = azimuth - convergence
    elif azimuth_reference != 'dem-grid':
        raise ValueError('Declare azimuth reference as true-north or dem-grid')
    polarity = result['polarity'].to_numpy(dtype=float) if 'polarity' in result else np.ones(len(result))
    if not np.isin(polarity, [-1, 1]).all():
        raise ValueError('Polarity must be +1 or -1')
    result = result.assign(dip=dip, azimuth=azimuth % 360, polarity=polarity)
    return pd.DataFrame(result[['X', 'Y', 'Z', 'azimuth', 'dip', 'polarity', 'formation']])


def clip_to_extent(gdf, extent):
    extent = np.asarray(extent, dtype=float)
    if extent.shape != (4,) or not np.isfinite(extent).all() or extent[0] >= extent[1] or extent[2] >= extent[3]:
        raise ValueError('Extent must be finite xmin,xmax,ymin,ymax with positive width and height')
    return gdf.clip(box(extent[0], extent[2], extent[1], extent[3]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contacts', required=True)
    parser.add_argument('--orientations')
    parser.add_argument('--dem', required=True)
    parser.add_argument('--dem-z-unit', choices=['m', 'ft'], required=True)
    parser.add_argument('--vertical-datum', required=True, help='Documented elevation datum; not transformed by this helper')
    parser.add_argument('--output-dir', default='.')
    parser.add_argument('--extent', help='Clip xmin,xmax,ymin,ymax in the DEM CRS')
    parser.add_argument('--formation-col', default='formation')
    parser.add_argument('--dip-col', default='dip')
    parser.add_argument('--azimuth-col', default='azimuth')
    parser.add_argument('--strike-col', default='strike')
    parser.add_argument('--strike-convention', choices=['rhr'])
    parser.add_argument('--azimuth-reference', choices=['true-north', 'dem-grid'],
                        help='Required with orientations; grid bearings must already refer to the DEM grid')
    parser.add_argument('--target-crs', help='Optional assertion: must equal the DEM CRS')
    args = parser.parse_args()
    try:
        if not args.vertical_datum.strip():
            raise ValueError('Vertical datum cannot be empty')
        output = Path(args.output_dir)
        if any((output / name).exists() for name in ('interfaces.csv', 'orientations.csv', 'spatial_metadata.json')):
            raise ValueError('Output directory already contains prepared data; select a new directory')
        with rasterio.open(args.dem) as dem:
            crs = metric_crs(dem.crs)
            if args.target_crs and crs != CRS.from_user_input(args.target_crs):
                raise ValueError('--target-crs must match DEM CRS; reproject the raster before extraction')
        extent = [float(v) for v in args.extent.split(',')] if args.extent else None
        def read(path):
            data = load_and_validate_vector(path, [args.formation_col]).to_crs(crs)
            return clip_to_extent(data, extent) if extent is not None else data
        interfaces = extract_interfaces(read(args.contacts), args.dem, args.formation_col, dem_z_unit=args.dem_z_unit)
        orientations = None
        if args.orientations:
            orientations = extract_orientations(read(args.orientations), args.dem, args.formation_col,
                args.dip_col, args.azimuth_col, args.strike_col,
                dem_z_unit=args.dem_z_unit, strike_convention=args.strike_convention,
                azimuth_reference=args.azimuth_reference)
        output.mkdir(parents=True, exist_ok=True)
        interfaces.to_csv(output / 'interfaces.csv', index=False)
        if orientations is not None:
            orientations.to_csv(output / 'orientations.csv', index=False)
        provenance = dict(crs=crs.to_string(), crs_wkt=crs.to_wkt(), xyz_units='m',
                          dem_z_unit=args.dem_z_unit, vertical_datum=args.vertical_datum,
                          dem=str(Path(args.dem).resolve()), contacts=str(Path(args.contacts).resolve()),
                          orientation_convention='dip degrees; output azimuth clockwise from DEM grid north; default polarity +1',
                          input_azimuth_reference=args.azimuth_reference,
                          interfaces=len(interfaces), orientations=0 if orientations is None else len(orientations))
        (output / 'spatial_metadata.json').write_text(json.dumps(provenance, indent=2) + '\n')
        print(f'Created {len(interfaces)} interface points in {output}')
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
