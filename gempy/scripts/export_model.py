#!/usr/bin/env python3
"""
Export GemPy model to various formats.

Usage:
    python export_model.py model.pkl --format vtk --output model_export
    python export_model.py model.pkl --format numpy --output lithology.npy
    python export_model.py model.pkl --format csv --output slices/
    python export_model.py model.pkl --format all --output exports/
"""

import argparse
import sys
from pathlib import Path

import numpy as np


def export_to_numpy(geo_model, sol, output_path: str) -> str:
    """
    Export lithology block as numpy array.

    Args:
        geo_model: GemPy GeoModel object
        sol: GemPy Solutions object
        output_path: Output file path (.npy)

    Returns:
        Path to created file
    """
    lith_block = sol.raw_arrays.lith_block
    resolution = geo_model.grid.regular_grid.resolution
    lith_3d = lith_block.reshape(resolution)

    output_path = Path(output_path)
    if output_path.suffix != ".npy":
        output_path = output_path.with_suffix(".npy")

    np.save(str(output_path), lith_3d)

    # Also save metadata
    meta_path = output_path.with_suffix(".meta.npz")
    np.savez(
        str(meta_path),
        extent=geo_model.grid.regular_grid.extent,
        resolution=resolution,
        surfaces=[s.name for s in geo_model.structural_frame.surfaces],
    )

    return str(output_path)


def export_to_csv(geo_model, sol, output_dir: str) -> list:
    """
    Export cross-sections as CSV files.

    Args:
        geo_model: GemPy GeoModel object
        sol: GemPy Solutions object
        output_dir: Output directory for CSV files

    Returns:
        List of created file paths
    """
    import pandas as pd

    lith_block = sol.raw_arrays.lith_block
    resolution = geo_model.grid.regular_grid.resolution
    extent = geo_model.grid.regular_grid.extent
    lith_3d = lith_block.reshape(resolution)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    created_files = []

    # Create coordinate arrays
    x = np.linspace(extent[0], extent[1], resolution[0])
    y = np.linspace(extent[2], extent[3], resolution[1])
    z = np.linspace(extent[4], extent[5], resolution[2])

    # Export X slices (YZ planes)
    for i in [0, resolution[0] // 2, resolution[0] - 1]:
        yy, zz = np.meshgrid(y, z, indexing="ij")
        df = pd.DataFrame(
            {
                "Y": yy.flatten(),
                "Z": zz.flatten(),
                "lithology": lith_3d[i, :, :].flatten(),
            }
        )
        path = output_dir / f"slice_x_{i}.csv"
        df.to_csv(path, index=False)
        created_files.append(str(path))

    # Export Y slices (XZ planes)
    for j in [0, resolution[1] // 2, resolution[1] - 1]:
        xx, zz = np.meshgrid(x, z, indexing="ij")
        df = pd.DataFrame(
            {
                "X": xx.flatten(),
                "Z": zz.flatten(),
                "lithology": lith_3d[:, j, :].flatten(),
            }
        )
        path = output_dir / f"slice_y_{j}.csv"
        df.to_csv(path, index=False)
        created_files.append(str(path))

    # Export Z slices (XY planes)
    for k in [0, resolution[2] // 2, resolution[2] - 1]:
        xx, yy = np.meshgrid(x, y, indexing="ij")
        df = pd.DataFrame(
            {
                "X": xx.flatten(),
                "Y": yy.flatten(),
                "lithology": lith_3d[:, :, k].flatten(),
            }
        )
        path = output_dir / f"slice_z_{k}.csv"
        df.to_csv(path, index=False)
        created_files.append(str(path))

    return created_files


def export_to_vtk(geo_model, sol, output_path: str) -> str:
    """
    Export model as VTK file for visualization.

    Args:
        geo_model: GemPy GeoModel object
        sol: GemPy Solutions object
        output_path: Output file path (.vtk or .vti)

    Returns:
        Path to created file
    """
    try:
        import pyvista as pv
    except ImportError:
        raise ImportError("PyVista required for VTK export: pip install pyvista")

    lith_block = sol.raw_arrays.lith_block
    resolution = geo_model.grid.regular_grid.resolution
    extent = geo_model.grid.regular_grid.extent

    # Create structured grid
    x = np.linspace(extent[0], extent[1], resolution[0] + 1)
    y = np.linspace(extent[2], extent[3], resolution[1] + 1)
    z = np.linspace(extent[4], extent[5], resolution[2] + 1)

    grid = pv.RectilinearGrid(x, y, z)
    grid.cell_data["lithology"] = lith_block

    output_path = Path(output_path)
    if output_path.suffix not in [".vtk", ".vti", ".vtr"]:
        output_path = output_path.with_suffix(".vtr")

    grid.save(str(output_path))
    return str(output_path)


def export_surfaces_to_obj(geo_model, sol, output_dir: str) -> list:
    """
    Export geological surfaces as OBJ mesh files.

    Args:
        geo_model: GemPy GeoModel object
        sol: GemPy Solutions object
        output_dir: Output directory for OBJ files

    Returns:
        List of created file paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    created_files = []

    # Check if vertices and edges exist
    if not hasattr(sol, "vertices") or sol.vertices is None:
        print("Warning: No mesh data available. Compute model with compute_mesh=True")
        return created_files

    for i, surface in enumerate(geo_model.structural_frame.surfaces):
        if i >= len(sol.vertices) or sol.vertices[i] is None:
            continue

        vertices = sol.vertices[i]
        edges = sol.edges[i]

        if len(vertices) == 0:
            continue

        path = output_dir / f"{surface.name}.obj"
        with open(path, "w") as f:
            f.write(f"# Surface: {surface.name}\n")

            # Write vertices
            for v in vertices:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")

            # Write faces (OBJ uses 1-indexed)
            for e in edges:
                f.write(f"f {e[0]+1} {e[1]+1} {e[2]+1}\n")

        created_files.append(str(path))

    return created_files


def load_model(model_path: str):
    """
    Load a saved GemPy model.

    Args:
        model_path: Path to saved model (.pkl or directory)

    Returns:
        Tuple of (geo_model, solutions)
    """
    import gempy as gp

    path = Path(model_path)

    if path.is_dir():
        # Load from directory (GemPy save format)
        geo_model = gp.load_model(str(path))
        # Recompute solution
        gp.set_interpolator(geo_model)
        sol = gp.compute_model(geo_model)
    elif path.suffix == ".pkl":
        # Load from pickle
        import pickle

        with open(path, "rb") as f:
            data = pickle.load(f)
        if isinstance(data, tuple):
            geo_model, sol = data
        else:
            geo_model = data
            gp.set_interpolator(geo_model)
            sol = gp.compute_model(geo_model)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

    return geo_model, sol


def main():
    parser = argparse.ArgumentParser(
        description="Export GemPy model to various formats"
    )
    parser.add_argument("model", help="Path to saved GemPy model (.pkl or directory)")
    parser.add_argument(
        "-f",
        "--format",
        choices=["numpy", "csv", "vtk", "obj", "all"],
        default="numpy",
        help="Output format",
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Output file or directory"
    )
    args = parser.parse_args()

    # Load model
    print(f"Loading model from {args.model}...")
    try:
        geo_model, sol = load_model(args.model)
    except Exception as e:
        print(f"Error loading model: {e}")
        sys.exit(1)

    print(f"Model loaded: {len(geo_model.structural_frame.surfaces)} surfaces")

    # Export based on format
    output = Path(args.output)

    if args.format == "numpy" or args.format == "all":
        out_path = output if args.format == "numpy" else output / "lithology.npy"
        result = export_to_numpy(geo_model, sol, str(out_path))
        print(f"Created: {result}")

    if args.format == "csv" or args.format == "all":
        out_dir = output if args.format == "csv" else output / "csv"
        results = export_to_csv(geo_model, sol, str(out_dir))
        print(f"Created {len(results)} CSV files in {out_dir}")

    if args.format == "vtk" or args.format == "all":
        out_path = output if args.format == "vtk" else output / "model.vtr"
        try:
            result = export_to_vtk(geo_model, sol, str(out_path))
            print(f"Created: {result}")
        except ImportError as e:
            print(f"Skipping VTK export: {e}")

    if args.format == "obj" or args.format == "all":
        out_dir = output if args.format == "obj" else output / "surfaces"
        results = export_surfaces_to_obj(geo_model, sol, str(out_dir))
        if results:
            print(f"Created {len(results)} OBJ files in {out_dir}")
        else:
            print("No surface meshes exported (compute with compute_mesh=True)")

    print("\nExport complete.")


if __name__ == "__main__":
    main()
