#!/usr/bin/env python3
"""
Build a basic geological model from CSV data.

Usage:
    python build_model.py data.csv --output model.vtk
    python build_model.py data.csv --feature strat --isovalue 0
    python build_model.py data.csv --with-faults fault_data.csv
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from LoopStructural import GeologicalModel


def load_data(filepath: str) -> pd.DataFrame:
    """
    Load geological data from CSV file.

    Expected columns:
        - X, Y, Z: Coordinates
        - feature_name: Name of geological feature
        - val: Interface value (NaN for orientations)
        - strike, dip: Optional orientation data
        - gx, gy, gz: Optional gradient vectors
    """
    df = pd.read_csv(filepath)

    required = ["X", "Y", "Z", "feature_name"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    return df


def infer_extent(data: pd.DataFrame, buffer: float = 0.1) -> tuple:
    """
    Infer model extent from data with buffer.

    Args:
        data: DataFrame with X, Y, Z columns
        buffer: Buffer fraction (0.1 = 10% on each side)

    Returns:
        (origin, maximum) as lists
    """
    x_range = data["X"].max() - data["X"].min()
    y_range = data["Y"].max() - data["Y"].min()
    z_range = data["Z"].max() - data["Z"].min()

    origin = [
        data["X"].min() - buffer * x_range,
        data["Y"].min() - buffer * y_range,
        data["Z"].min() - buffer * z_range,
    ]
    maximum = [
        data["X"].max() + buffer * x_range,
        data["Y"].max() + buffer * y_range,
        data["Z"].max() + buffer * z_range,
    ]

    return origin, maximum


def build_model(
    data: pd.DataFrame,
    fault_data: pd.DataFrame = None,
    interpolator: str = "PLI",
    nelements: int = 1000,
) -> GeologicalModel:
    """
    Build a geological model from data.

    Args:
        data: DataFrame with interface and orientation data
        fault_data: Optional DataFrame with fault data
        interpolator: Interpolation method ('PLI', 'FDI', 'Surfe')
        nelements: Number of mesh elements

    Returns:
        GeologicalModel object
    """
    origin, maximum = infer_extent(data)

    model = GeologicalModel(origin, maximum)

    # Add fault data if provided
    if fault_data is not None:
        all_data = pd.concat([fault_data, data], ignore_index=True)
        model.data = all_data

        # Add faults first
        fault_names = fault_data["feature_name"].unique()
        for fault_name in fault_names:
            model.create_and_add_fault(
                fault_name,
                interpolatortype=interpolator,
                nelements=nelements,
            )
    else:
        model.data = data

    # Add stratigraphic features
    feature_names = data["feature_name"].unique()
    for feature_name in feature_names:
        model.create_and_add_foliation(
            feature_name,
            interpolatortype=interpolator,
            nelements=nelements,
        )

    model.update()

    return model


def export_surfaces(
    model: GeologicalModel,
    output_path: str,
    feature_name: str = None,
    isovalues: list = None,
) -> list:
    """
    Export model surfaces to VTK files.

    Args:
        model: Built GeologicalModel
        output_path: Output file path (without extension)
        feature_name: Specific feature to export (default: all)
        isovalues: List of isovalues to extract (default: [0])

    Returns:
        List of created file paths
    """
    if isovalues is None:
        isovalues = [0]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    created_files = []

    features = [feature_name] if feature_name else list(model.feature_name_index.keys())

    for fname in features:
        feature = model[fname]
        for isovalue in isovalues:
            try:
                surface = feature.isosurface(isovalue=isovalue)
                filepath = f"{output_path}_{fname}_iso{isovalue}.vtk"
                surface.save(filepath)
                created_files.append(filepath)
                print(f"Created: {filepath}")
            except Exception as e:
                print(f"Warning: Could not create isosurface for {fname} at {isovalue}: {e}")

    return created_files


def export_grid(
    model: GeologicalModel,
    output_path: str,
    nsteps: list = None,
) -> str:
    """
    Export model as regular grid to VTK.

    Args:
        model: Built GeologicalModel
        output_path: Output file path
        nsteps: Grid resolution [nx, ny, nz]

    Returns:
        Path to created file
    """
    try:
        import pyvista as pv
    except ImportError:
        raise ImportError("pyvista required for grid export: pip install pyvista")

    if nsteps is None:
        nsteps = [50, 50, 50]

    output_path = Path(output_path)
    if output_path.suffix != ".vtk":
        output_path = output_path.with_suffix(".vtk")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Create regular grid
    grid_data = model.regular_grid(nsteps=nsteps)
    grid = pv.StructuredGrid(*grid_data)
    grid.save(str(output_path))

    print(f"Created: {output_path}")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Build geological model from CSV data"
    )
    parser.add_argument("input", help="CSV file with geological data")
    parser.add_argument(
        "--output", "-o", default="model", help="Output path (without extension)"
    )
    parser.add_argument(
        "--with-faults", help="CSV file with fault data"
    )
    parser.add_argument(
        "--feature", "-f", help="Specific feature to export"
    )
    parser.add_argument(
        "--isovalue", "-i", type=float, nargs="+", default=[0],
        help="Isovalues to extract (default: 0)"
    )
    parser.add_argument(
        "--interpolator", choices=["PLI", "FDI", "Surfe"], default="PLI",
        help="Interpolation method (default: PLI)"
    )
    parser.add_argument(
        "--nelements", "-n", type=int, default=1000,
        help="Number of mesh elements (default: 1000)"
    )
    parser.add_argument(
        "--grid", action="store_true",
        help="Also export as regular grid"
    )
    parser.add_argument(
        "--grid-resolution", type=int, nargs=3, default=[50, 50, 50],
        help="Grid resolution [nx ny nz] (default: 50 50 50)"
    )
    args = parser.parse_args()

    # Load data
    print(f"Loading data from {args.input}")
    data = load_data(args.input)
    print(f"  Loaded {len(data)} data points")
    print(f"  Features: {data['feature_name'].unique().tolist()}")

    fault_data = None
    if args.with_faults:
        print(f"Loading fault data from {args.with_faults}")
        fault_data = load_data(args.with_faults)
        print(f"  Loaded {len(fault_data)} fault data points")

    # Build model
    print(f"\nBuilding model with {args.interpolator} interpolator...")
    model = build_model(
        data,
        fault_data=fault_data,
        interpolator=args.interpolator,
        nelements=args.nelements,
    )
    print("  Model built successfully")

    # Export surfaces
    print(f"\nExporting isosurfaces...")
    export_surfaces(
        model,
        args.output,
        feature_name=args.feature,
        isovalues=args.isovalue,
    )

    # Export grid if requested
    if args.grid:
        print(f"\nExporting regular grid...")
        export_grid(model, f"{args.output}_grid", nsteps=args.grid_resolution)

    print("\nDone!")


if __name__ == "__main__":
    main()
