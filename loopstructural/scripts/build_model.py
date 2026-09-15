#!/usr/bin/env python3
"""Build constrained foliations and export evaluated world-coordinate VTK data."""
import argparse
from pathlib import Path
import re
import sys

from LoopStructural import GeologicalModel
import numpy as np
import pandas as pd
import pyvista as pv


def validate_data(data):
    required = {'X', 'Y', 'Z', 'feature_name'}
    if not required.issubset(data.columns) or data.empty:
        raise ValueError('Nonempty data requires X, Y, Z and feature_name')
    xyz = data[['X', 'Y', 'Z']].to_numpy(dtype=float)
    if not np.isfinite(xyz).all():
        raise ValueError('Coordinates must be finite')
    if data['feature_name'].isna().any() or not all(re.fullmatch(r'[A-Za-z0-9_-]+', str(n)) for n in data['feature_name']):
        raise ValueError('Feature names must contain only letters, digits, underscore or hyphen')
    constrained = np.zeros(len(data), dtype=bool)
    if 'val' in data:
        values = data['val'].to_numpy(dtype=float)
        if np.isinf(values).any():
            raise ValueError('Scalar constraints cannot be infinite')
        constrained |= np.isfinite(values)
    for columns in [('gx', 'gy', 'gz'), ('nx', 'ny', 'nz')]:
        if any(c in data for c in columns):
            if not all(c in data for c in columns):
                raise ValueError(f'Vector constraints require all of {columns}')
            vector = data[list(columns)].to_numpy(dtype=float)
            valid = np.isfinite(vector).all(axis=1)
            absent = np.isnan(vector).all(axis=1)
            if not np.all(valid | absent) or np.any(valid & (np.linalg.norm(vector, axis=1) == 0)):
                raise ValueError('Vector constraints must be finite/nonzero or entirely missing')
            constrained |= valid
    if not np.all(constrained):
        raise ValueError('Every row needs a scalar val or complete nonzero gx/gy/gz or nx/ny/nz constraint')
    for _, group in data.groupby('feature_name'):
        if 'val' not in group or not np.isfinite(group['val'].to_numpy(dtype=float)).any():
            raise ValueError('Each feature needs a scalar constraint to fix its level')
    return data


def load_data(filepath):
    return validate_data(pd.read_csv(filepath))


def infer_extent(data, buffer=0.1):
    if not np.isfinite(buffer) or buffer < 0:
        raise ValueError('Buffer must be finite and nonnegative')
    xyz = data[['X', 'Y', 'Z']].to_numpy(dtype=float)
    minimum, maximum = xyz.min(axis=0), xyz.max(axis=0)
    span = maximum - minimum
    if np.any(span <= 0):
        raise ValueError('Cannot infer a 3D extent from zero-span data; supply origin and maximum')
    return minimum - buffer * span, maximum + buffer * span


def build_model(data, fault_data=None, interpolator='FDI', nelements=1000, *, origin=None, maximum=None):
    validate_data(data)
    if fault_data is not None:
        raise ValueError('This helper supports foliations; fault kinematics require a separately configured model')
    if interpolator not in ('FDI', 'PLI') or not isinstance(nelements, int) or nelements < 100:
        raise ValueError('Choose FDI/PLI and an integer nelements of at least 100')
    if (origin is None) != (maximum is None):
        raise ValueError('Supply both origin and maximum')
    if origin is None:
        origin, maximum = infer_extent(data)
    origin, maximum = np.asarray(origin, dtype=float), np.asarray(maximum, dtype=float)
    if origin.shape != (3,) or maximum.shape != (3,) or not np.isfinite([origin, maximum]).all() or np.any(maximum <= origin):
        raise ValueError('Origin and maximum must define a finite positive 3D extent')
    xyz = data[['X', 'Y', 'Z']].to_numpy(dtype=float)
    if np.any(xyz < origin) or np.any(xyz > maximum):
        raise ValueError('Constraints lie outside the declared model extent')
    model = GeologicalModel(origin, maximum)
    model.data = data.copy()
    for name in data['feature_name'].unique():
        model.create_and_add_foliation(name, interpolatortype=interpolator, nelements=nelements)
    model.update()
    return model


def evaluated_grid(model, nsteps=None, feature_names=None):
    nsteps = [30, 30, 30] if nsteps is None else nsteps
    if len(nsteps) != 3 or any(not isinstance(n, (int, np.integer)) or n < 2 for n in nsteps):
        raise ValueError('Grid shape must contain three integers of at least 2')
    # F order gives VTK's x-fastest point ordering. The API returns N x 3
    # world coordinates, not three coordinate arrays. Disable shuffling.
    points = model.regular_grid(nsteps=nsteps, shuffle=False, order='F')
    grid = pv.StructuredGrid()
    grid.points = points
    grid.dimensions = nsteps
    names = list(model.feature_name_index) if feature_names is None else feature_names
    if not names:
        raise ValueError('Model contains no features')
    for name in names:
        if name not in model.feature_name_index:
            raise ValueError(f'Unknown feature: {name}')
        values = model.evaluate_feature_value(name, points)
        if not np.isfinite(values).all():
            raise ValueError(f'Feature {name} has nonfinite values on the export grid')
        grid.point_data[name] = values
    return grid


def export_grid(model, output_path, nsteps=None):
    grid = evaluated_grid(model, nsteps)
    path = Path(output_path).with_suffix('.vtk')
    path.parent.mkdir(parents=True, exist_ok=True)
    grid.save(path)
    return str(path)


def export_surfaces(model, output_path, feature_name=None, isovalues=None, nsteps=None):
    levels = np.asarray([0.] if isovalues is None else isovalues, dtype=float)
    if levels.ndim != 1 or not levels.size or not np.isfinite(levels).all():
        raise ValueError('Supply finite isovalues')
    names = [feature_name] if feature_name is not None else list(model.feature_name_index)
    grid = evaluated_grid(model, nsteps, names)
    output = Path(output_path).with_suffix('')
    surfaces = []
    for name in names:
        for value in levels:
            surface = grid.contour([float(value)], scalars=name)
            if surface.n_points == 0 or surface.n_cells == 0:
                raise ValueError(f'No surface for {name} at isovalue {value}; check the scalar range')
            surfaces.append((output.parent / f'{output.name}_{name}_iso{value:g}.vtk', surface))
    output.parent.mkdir(parents=True, exist_ok=True)
    for path, surface in surfaces:
        surface.save(path)
    return [str(path) for path, _ in surfaces]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    parser.add_argument('--output', '-o', default='model')
    parser.add_argument('--feature', '-f')
    parser.add_argument('--isovalue', '-i', type=float, nargs='+', default=[0.])
    parser.add_argument('--interpolator', choices=['FDI', 'PLI'], default='FDI')
    parser.add_argument('--nelements', '-n', type=int, default=1000)
    parser.add_argument('--origin', type=float, nargs=3)
    parser.add_argument('--maximum', type=float, nargs=3)
    parser.add_argument('--grid', action='store_true')
    parser.add_argument('--nsteps', type=int, nargs=3, default=[30, 30, 30])
    args = parser.parse_args()
    try:
        if Path(args.input).resolve() == Path(args.output).with_suffix('.vtk').resolve():
            raise ValueError('Output must not overwrite the input')
        model = build_model(load_data(args.input), interpolator=args.interpolator, nelements=args.nelements,
                            origin=args.origin, maximum=args.maximum)
        if args.grid:
            paths = [export_grid(model, args.output, args.nsteps)]
        else:
            paths = export_surfaces(model, args.output, args.feature, args.isovalue, args.nsteps)
        for path in paths:
            print(f'Created: {path}')
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
