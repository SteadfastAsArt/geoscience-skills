#!/usr/bin/env python3
"""
Complete ERT inversion workflow with pyGIMLi.

Usage:
    python ert_inversion.py survey.ohm
    python ert_inversion.py survey.ohm --lam 30 --output results/
    python ert_inversion.py survey.ohm --show-data --export-vtk
"""

import argparse
from pathlib import Path

import numpy as np
import pygimli as pg
from pygimli.physics import ert


def load_and_validate(filepath: str) -> pg.DataContainer:
    """
    Load ERT data and perform basic validation.

    Args:
        filepath: Path to ERT data file (.ohm, .dat, etc.)

    Returns:
        Validated DataContainer
    """
    data = ert.load(filepath)
    print(f"Loaded: {filepath}")
    print(f"  Measurements: {data.size()}")
    print(f"  Electrodes: {data.sensorCount()}")

    # Check for invalid data
    if "rhoa" in data.dataKeys():
        rhoa = data["rhoa"]
        invalid = (rhoa <= 0) | ~np.isfinite(rhoa)
        if np.any(invalid):
            print(f"  Invalid measurements: {np.sum(invalid)}")
            data.markInvalid(invalid)
            data.removeInvalid()
            print(f"  After removal: {data.size()}")

    return data


def create_mesh(
    data: pg.DataContainer,
    quality: float = 34.0,
    max_cell_size: float = 5.0,
    depth: float = None,
) -> pg.Mesh:
    """
    Create inversion mesh from data.

    Args:
        data: ERT DataContainer with sensor positions
        quality: Mesh quality (minimum angle in degrees)
        max_cell_size: Maximum cell size in parameter region
        depth: Depth of investigation (auto if None)

    Returns:
        Parameter mesh
    """
    if depth is None:
        # Estimate depth from electrode spread
        sensors = np.array(data.sensors())
        spread = sensors[:, 0].max() - sensors[:, 0].min()
        depth = spread / 3

    mesh = pg.meshtools.createParaMesh(
        data.sensors(),
        quality=quality,
        paraMaxCellSize=max_cell_size,
        boundary=2,
        paraDepth=depth,
    )
    print(f"Mesh created: {mesh.cellCount()} cells")
    return mesh


def run_inversion(
    data: pg.DataContainer,
    mesh: pg.Mesh = None,
    lam: float = 20.0,
    z_weight: float = 0.7,
    robust: bool = False,
    max_iter: int = 20,
    verbose: bool = True,
) -> tuple:
    """
    Run ERT inversion.

    Args:
        data: ERT DataContainer
        mesh: Optional custom mesh
        lam: Regularization parameter
        z_weight: Vertical smoothing weight (0-1)
        robust: Use robust data weighting
        max_iter: Maximum iterations
        verbose: Print progress

    Returns:
        Tuple of (ERTManager, model array)
    """
    mgr = ert.ERTManager(data)

    if mesh is not None:
        mgr.setMesh(mesh)

    model = mgr.invert(
        lam=lam,
        zWeight=z_weight,
        robustData=robust,
        maxIter=max_iter,
        verbose=verbose,
    )

    # Print summary
    chi2 = mgr.inv.chi2()
    rms = mgr.inv.relrms()
    print(f"\nInversion complete:")
    print(f"  Chi-squared: {chi2:.2f}")
    print(f"  Relative RMS: {rms:.1f}%")
    print(f"  Iterations: {mgr.inv.iter()}")

    return mgr, model


def save_results(
    mgr: ert.ERTManager,
    output_dir: str,
    export_vtk: bool = True,
) -> None:
    """
    Save inversion results.

    Args:
        mgr: ERTManager after inversion
        output_dir: Output directory
        export_vtk: Export VTK for ParaView
    """
    outpath = Path(output_dir)
    outpath.mkdir(parents=True, exist_ok=True)

    # Save mesh
    mesh_file = outpath / "mesh.bms"
    mgr.mesh.save(str(mesh_file))
    print(f"Saved mesh: {mesh_file}")

    # Save model
    model_file = outpath / "resistivity.vector"
    pg.save(mgr.model, str(model_file))
    print(f"Saved model: {model_file}")

    # Save coverage
    coverage_file = outpath / "coverage.vector"
    pg.save(mgr.coverage(), str(coverage_file))
    print(f"Saved coverage: {coverage_file}")

    # Export VTK
    if export_vtk:
        vtk_file = outpath / "result"
        mgr.mesh.exportVTK(
            str(vtk_file),
            {
                "resistivity": mgr.model,
                "coverage": mgr.coverage(),
            },
        )
        print(f"Saved VTK: {vtk_file}.vtk")


def main():
    parser = argparse.ArgumentParser(
        description="Run ERT inversion with pyGIMLi",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python ert_inversion.py survey.ohm
    python ert_inversion.py survey.ohm --lam 30 --robust
    python ert_inversion.py survey.ohm -o results/ --export-vtk
        """,
    )
    parser.add_argument("input", help="ERT data file (.ohm, .dat)")
    parser.add_argument(
        "--lam",
        "-l",
        type=float,
        default=20.0,
        help="Regularization parameter (default: 20)",
    )
    parser.add_argument(
        "--z-weight",
        "-z",
        type=float,
        default=0.7,
        help="Vertical smoothing weight (default: 0.7)",
    )
    parser.add_argument(
        "--robust",
        "-r",
        action="store_true",
        help="Use robust data weighting",
    )
    parser.add_argument(
        "--max-iter",
        type=int,
        default=20,
        help="Maximum iterations (default: 20)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="ert_results",
        help="Output directory (default: ert_results)",
    )
    parser.add_argument(
        "--show-data",
        action="store_true",
        help="Display data pseudosection",
    )
    parser.add_argument(
        "--show-result",
        action="store_true",
        help="Display inversion result",
    )
    parser.add_argument(
        "--export-vtk",
        action="store_true",
        help="Export VTK for ParaView",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress verbose output",
    )
    args = parser.parse_args()

    # Load data
    data = load_and_validate(args.input)

    # Show data if requested
    if args.show_data:
        ert.showData(data)
        pg.wait()

    # Create mesh
    mesh = create_mesh(data)

    # Run inversion
    mgr, model = run_inversion(
        data,
        mesh=mesh,
        lam=args.lam,
        z_weight=args.z_weight,
        robust=args.robust,
        max_iter=args.max_iter,
        verbose=not args.quiet,
    )

    # Save results
    save_results(mgr, args.output, export_vtk=args.export_vtk)

    # Show result if requested
    if args.show_result:
        mgr.showResult()
        pg.wait()

    print(f"\nResults saved to: {args.output}/")


if __name__ == "__main__":
    main()
