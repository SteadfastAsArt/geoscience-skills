#!/usr/bin/env python3
"""
Basic landscape evolution model with stream power erosion and hillslope diffusion.

This script demonstrates a simple but complete landscape evolution model using
Landlab. It combines:
- Stream power erosion (fluvial incision)
- Linear hillslope diffusion
- Uniform tectonic uplift

Usage:
    python erosion_model.py
    python erosion_model.py --rows 100 --cols 100 --dx 100 --runtime 1e6
    python erosion_model.py --output results/
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from landlab import RasterModelGrid
from landlab.components import FlowAccumulator, LinearDiffuser, StreamPowerEroder
from landlab.io import write_esri_ascii


def create_initial_topography(grid: RasterModelGrid, noise_amplitude: float = 0.1) -> np.ndarray:
    """
    Create initial topography with slight slope and random noise.

    Args:
        grid: Landlab RasterModelGrid
        noise_amplitude: Amplitude of random noise (m)

    Returns:
        Elevation array attached to grid
    """
    z = grid.add_zeros("topographic__elevation", at="node")

    # Add slight slope toward outlet (bottom edge)
    z += grid.node_y / 1000

    # Add random noise to break symmetry
    np.random.seed(42)
    z += np.random.rand(grid.number_of_nodes) * noise_amplitude

    return z


def setup_boundaries(grid: RasterModelGrid) -> None:
    """
    Set boundary conditions with outlet at bottom edge.

    Args:
        grid: Landlab RasterModelGrid
    """
    grid.set_closed_boundaries_at_grid_edges(
        right_is_closed=True,
        top_is_closed=True,
        left_is_closed=True,
        bottom_is_closed=False,  # Open outlet
    )


def run_model(
    nrows: int = 50,
    ncols: int = 50,
    dx: float = 100.0,
    runtime: float = 5e5,
    dt: float = 1000.0,
    uplift_rate: float = 0.001,
    k_sp: float = 1e-5,
    m_sp: float = 0.5,
    n_sp: float = 1.0,
    diffusivity: float = 0.01,
    output_interval: int = 50,
    output_dir: str | None = None,
) -> tuple[RasterModelGrid, list[float]]:
    """
    Run a landscape evolution model.

    Args:
        nrows: Number of grid rows
        ncols: Number of grid columns
        dx: Grid spacing (m)
        runtime: Total model runtime (years)
        dt: Timestep (years)
        uplift_rate: Tectonic uplift rate (m/yr)
        k_sp: Stream power erodibility coefficient
        m_sp: Stream power drainage area exponent
        n_sp: Stream power slope exponent
        diffusivity: Hillslope diffusivity (m^2/yr)
        output_interval: Steps between output
        output_dir: Directory for output files

    Returns:
        Tuple of (grid, mean_elevation_history)
    """
    # Create grid and topography
    grid = RasterModelGrid((nrows, ncols), xy_spacing=dx)
    z = create_initial_topography(grid)
    setup_boundaries(grid)

    # Initialize components
    fa = FlowAccumulator(grid, flow_director="D8")
    sp = StreamPowerEroder(grid, K_sp=k_sp, m_sp=m_sp, n_sp=n_sp)
    ld = LinearDiffuser(grid, linear_diffusivity=diffusivity)

    # Setup output
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

    # Time loop
    n_steps = int(runtime / dt)
    mean_elevation = []

    print(f"Running model for {runtime:.0e} years ({n_steps} steps)")
    print(f"Grid: {nrows}x{ncols}, dx={dx}m")
    print(f"Uplift: {uplift_rate*1000:.1f} mm/yr, K_sp: {k_sp:.0e}")
    print("-" * 50)

    for i in range(n_steps):
        # Route flow
        fa.run_one_step()

        # Erode by stream power
        sp.run_one_step(dt)

        # Diffuse hillslopes
        ld.run_one_step(dt)

        # Apply uplift to core nodes
        z[grid.core_nodes] += uplift_rate * dt

        # Track mean elevation
        mean_elevation.append(z[grid.core_nodes].mean())

        # Output progress
        if (i + 1) % output_interval == 0:
            time_kyr = (i + 1) * dt / 1000
            print(f"  Time: {time_kyr:.0f} kyr, Mean elevation: {mean_elevation[-1]:.1f} m")

            # Save intermediate output
            if output_dir:
                filename = output_path / f"topo_{i+1:06d}.asc"
                write_esri_ascii(str(filename), grid, names="topographic__elevation")

    return grid, mean_elevation


def plot_results(
    grid: RasterModelGrid,
    mean_elevation: list[float],
    dt: float,
    save_path: str | None = None,
) -> None:
    """
    Create summary plots of model results.

    Args:
        grid: Landlab grid with final topography
        mean_elevation: Time series of mean elevation
        dt: Model timestep (years)
        save_path: Path to save figure (optional)
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Topography
    ax = axes[0, 0]
    im = grid.imshow("topographic__elevation", cmap="terrain", ax=ax)
    ax.set_title("Final Topography")
    plt.colorbar(im, ax=ax, label="Elevation (m)")

    # Drainage area
    ax = axes[0, 1]
    im = grid.imshow(
        "drainage_area",
        cmap="Blues",
        ax=ax,
        norm=plt.matplotlib.colors.LogNorm(),
    )
    ax.set_title("Drainage Area")
    plt.colorbar(im, ax=ax, label="Area (m²)")

    # Slope
    ax = axes[1, 0]
    z = grid.at_node["topographic__elevation"]
    slope = np.zeros(grid.number_of_nodes)
    for node in grid.core_nodes:
        neighbors = grid.active_adjacent_nodes_at_node[node]
        neighbors = neighbors[neighbors != -1]
        if len(neighbors) > 0:
            dz = z[node] - z[neighbors]
            dist = np.sqrt(
                (grid.node_x[node] - grid.node_x[neighbors]) ** 2
                + (grid.node_y[node] - grid.node_y[neighbors]) ** 2
            )
            slope[node] = np.max(np.abs(dz / dist))

    grid.add_field("slope", slope, at="node", clobber=True)
    im = grid.imshow("slope", cmap="YlOrRd", ax=ax, vmin=0)
    ax.set_title("Local Slope")
    plt.colorbar(im, ax=ax, label="Slope (m/m)")

    # Mean elevation time series
    ax = axes[1, 1]
    time_kyr = np.arange(1, len(mean_elevation) + 1) * dt / 1000
    ax.plot(time_kyr, mean_elevation, "b-", linewidth=1)
    ax.set_xlabel("Time (kyr)")
    ax.set_ylabel("Mean Elevation (m)")
    ax.set_title("Elevation Evolution")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Figure saved to: {save_path}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Run a basic landscape evolution model"
    )
    parser.add_argument("--rows", type=int, default=50, help="Number of grid rows")
    parser.add_argument("--cols", type=int, default=50, help="Number of grid columns")
    parser.add_argument("--dx", type=float, default=100.0, help="Grid spacing (m)")
    parser.add_argument(
        "--runtime", type=float, default=5e5, help="Model runtime (years)"
    )
    parser.add_argument("--dt", type=float, default=1000.0, help="Timestep (years)")
    parser.add_argument(
        "--uplift", type=float, default=0.001, help="Uplift rate (m/yr)"
    )
    parser.add_argument(
        "--k-sp", type=float, default=1e-5, help="Stream power erodibility"
    )
    parser.add_argument("--output", type=str, help="Output directory")
    parser.add_argument(
        "--save-fig", type=str, help="Path to save summary figure"
    )
    args = parser.parse_args()

    # Run model
    grid, mean_elevation = run_model(
        nrows=args.rows,
        ncols=args.cols,
        dx=args.dx,
        runtime=args.runtime,
        dt=args.dt,
        uplift_rate=args.uplift,
        k_sp=args.k_sp,
        output_dir=args.output,
    )

    # Plot results
    print("-" * 50)
    print("Model complete. Generating plots...")
    plot_results(grid, mean_elevation, args.dt, save_path=args.save_fig)


if __name__ == "__main__":
    main()
