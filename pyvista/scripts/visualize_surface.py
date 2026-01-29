#!/usr/bin/env python3
"""
Visualize geological surfaces from VTK or other supported files.

Usage:
    python visualize_surface.py <file.vtk> [options]
    python visualize_surface.py surface.vtk --scalars=elevation --cmap=terrain
    python visualize_surface.py model.vtk --output=figure.png --resolution=2
"""

import argparse
import sys
from pathlib import Path

import pyvista as pv


def visualize_surface(
    filepath: str,
    scalars: str | None = None,
    cmap: str = "viridis",
    opacity: float = 1.0,
    show_edges: bool = False,
    output: str | None = None,
    resolution: int = 1,
    view: str = "iso",
    background: str = "white",
) -> None:
    """
    Visualize a surface mesh from file.

    Args:
        filepath: Path to mesh file (VTK, STL, OBJ, PLY, etc.)
        scalars: Name of scalar array to color by
        cmap: Color map name
        opacity: Surface opacity (0-1)
        show_edges: Display mesh edges
        output: Output image path (None for interactive)
        resolution: Screenshot resolution multiplier
        view: Camera view ('iso', 'xy', 'xz', 'yz')
        background: Background color
    """
    # Load mesh
    path = Path(filepath)
    if not path.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    print(f"Loading: {filepath}")
    mesh = pv.read(filepath)

    # Print mesh info
    print(f"  Type: {type(mesh).__name__}")
    print(f"  Points: {mesh.n_points:,}")
    print(f"  Cells: {mesh.n_cells:,}")
    print(f"  Bounds: {mesh.bounds}")

    if mesh.array_names:
        print(f"  Arrays: {mesh.array_names}")

    # Validate scalars
    if scalars and scalars not in mesh.array_names:
        print(f"Warning: Scalar '{scalars}' not found. Available: {mesh.array_names}")
        scalars = None

    # Create plotter
    off_screen = output is not None
    plotter = pv.Plotter(off_screen=off_screen)
    plotter.set_background(background)

    # Add mesh
    plotter.add_mesh(
        mesh,
        scalars=scalars,
        cmap=cmap,
        opacity=opacity,
        show_edges=show_edges,
        scalar_bar_args={"title": scalars} if scalars else None,
    )

    # Set view
    if view == "xy":
        plotter.view_xy()
    elif view == "xz":
        plotter.view_xz()
    elif view == "yz":
        plotter.view_yz()
    else:
        plotter.view_isometric()

    # Add annotations
    plotter.add_axes()
    plotter.show_bounds(grid="front", location="outer")

    # Output or display
    if output:
        output_path = Path(output)
        if output_path.suffix.lower() in [".svg", ".pdf", ".eps"]:
            plotter.save_graphic(output)
            print(f"Saved vector graphic: {output}")
        else:
            plotter.screenshot(output, scale=resolution)
            print(f"Saved screenshot: {output}")
    else:
        plotter.show()


def main():
    parser = argparse.ArgumentParser(
        description="Visualize geological surfaces",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python visualize_surface.py model.vtk
    python visualize_surface.py horizon.vtk --scalars=depth --cmap=terrain
    python visualize_surface.py fault.stl --show-edges --opacity=0.7
    python visualize_surface.py model.vtk --output=figure.png --resolution=3
    python visualize_surface.py model.vtk --view=xy --output=plan_view.png
        """,
    )
    parser.add_argument("filepath", help="Path to mesh file")
    parser.add_argument(
        "--scalars", "-s", help="Scalar array to color by"
    )
    parser.add_argument(
        "--cmap", "-c", default="viridis", help="Color map (default: viridis)"
    )
    parser.add_argument(
        "--opacity", "-a", type=float, default=1.0, help="Opacity 0-1 (default: 1.0)"
    )
    parser.add_argument(
        "--show-edges", "-e", action="store_true", help="Show mesh edges"
    )
    parser.add_argument(
        "--output", "-o", help="Output image path (omit for interactive)"
    )
    parser.add_argument(
        "--resolution", "-r", type=int, default=1, help="Screenshot scale (default: 1)"
    )
    parser.add_argument(
        "--view",
        "-v",
        choices=["iso", "xy", "xz", "yz"],
        default="iso",
        help="Camera view (default: iso)",
    )
    parser.add_argument(
        "--background", "-b", default="white", help="Background color (default: white)"
    )

    args = parser.parse_args()

    visualize_surface(
        filepath=args.filepath,
        scalars=args.scalars,
        cmap=args.cmap,
        opacity=args.opacity,
        show_edges=args.show_edges,
        output=args.output,
        resolution=args.resolution,
        view=args.view,
        background=args.background,
    )


if __name__ == "__main__":
    main()
