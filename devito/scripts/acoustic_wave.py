#!/usr/bin/env python3
"""
Basic 2D acoustic wave propagation using Devito.

Usage:
    python acoustic_wave.py
    python acoustic_wave.py --nx 201 --nz 201 --nt 1000
    python acoustic_wave.py --output wavefield.npy --save-snapshots

This script demonstrates:
    - Setting up a 2D computational grid
    - Creating a velocity model with an anomaly
    - Defining the acoustic wave equation
    - Adding a Ricker wavelet source
    - Recording at receiver array
    - Running forward modeling
"""

import argparse

import numpy as np


def create_velocity_model(nx: int, nz: int, v_background: float = 1500.0,
                          v_anomaly: float = 2500.0) -> np.ndarray:
    """
    Create a simple velocity model with a circular anomaly.

    Args:
        nx: Number of grid points in x
        nz: Number of grid points in z
        v_background: Background velocity (m/s)
        v_anomaly: Anomaly velocity (m/s)

    Returns:
        2D velocity array
    """
    vel = np.full((nx, nz), v_background, dtype=np.float32)

    # Add circular anomaly in center
    cx, cz = nx // 2, nz // 2
    radius = min(nx, nz) // 6

    for i in range(nx):
        for j in range(nz):
            if (i - cx)**2 + (j - cz)**2 < radius**2:
                vel[i, j] = v_anomaly

    return vel


def run_acoustic_wave(nx: int = 101, nz: int = 101, nt: int = 500,
                      dx: float = 10.0, dt: float = 1.0,
                      f0: float = 10.0, save_snapshots: bool = False) -> dict:
    """
    Run 2D acoustic wave simulation.

    Args:
        nx: Number of grid points in x
        nz: Number of grid points in z
        nt: Number of time steps
        dx: Grid spacing in meters
        dt: Time step in milliseconds
        f0: Source dominant frequency in Hz
        save_snapshots: Whether to save wavefield snapshots

    Returns:
        dict with 'shot_record', 'velocity', and optionally 'snapshots'
    """
    from devito import Grid, Function, TimeFunction, Eq, solve, Operator

    # Import seismic utilities
    try:
        from examples.seismic import RickerSource, Receiver, TimeAxis
    except ImportError:
        raise ImportError(
            "Devito seismic examples not found. Install with: "
            "pip install devito[extras] or clone devito repo."
        )

    # Create computational grid
    extent = (nx * dx, nz * dx)
    grid = Grid(shape=(nx, nz), extent=extent)

    # Velocity model
    v = Function(name='v', grid=grid, space_order=4)
    v.data[:] = create_velocity_model(nx, nz)

    # Time axis
    t0 = 0.0
    tn = nt * dt
    time_range = TimeAxis(start=t0, stop=tn, step=dt)

    # Source: Ricker wavelet at surface center
    src = RickerSource(
        name='src',
        grid=grid,
        f0=f0 / 1000.0,  # Convert to kHz for ms time units
        npoint=1,
        time_range=time_range
    )
    src.coordinates.data[0, 0] = extent[0] / 2  # Center x
    src.coordinates.data[0, 1] = dx * 2         # Near surface

    # Receivers: Line at surface
    nrec = nx
    rec = Receiver(
        name='rec',
        grid=grid,
        npoint=nrec,
        time_range=time_range
    )
    rec.coordinates.data[:, 0] = np.linspace(0, extent[0], nrec)
    rec.coordinates.data[:, 1] = dx * 2  # Same depth as source

    # Wavefield
    if save_snapshots:
        p = TimeFunction(
            name='p', grid=grid, time_order=2, space_order=4, save=nt
        )
    else:
        p = TimeFunction(
            name='p', grid=grid, time_order=2, space_order=4
        )

    # Acoustic wave equation: d2p/dt2 = v^2 * laplacian(p)
    pde = p.dt2 - v**2 * p.laplace
    stencil = Eq(p.forward, solve(pde, p.forward))

    # Source injection
    src_term = src.inject(
        field=p.forward,
        expr=src * dt**2 * v**2
    )

    # Receiver interpolation
    rec_term = rec.interpolate(expr=p)

    # Create and run operator
    op = Operator([stencil] + src_term + rec_term, name='forward')

    print(f"Running acoustic wave simulation:")
    print(f"  Grid: {nx} x {nz} points")
    print(f"  Extent: {extent[0]:.0f} x {extent[1]:.0f} m")
    print(f"  Time steps: {nt}")
    print(f"  Source frequency: {f0} Hz")

    # Execute
    summary = op.apply(time_M=nt-2, dt=dt)

    print(f"\nPerformance:")
    print(f"  {summary}")

    # Prepare results
    results = {
        'shot_record': rec.data.copy(),
        'velocity': v.data.copy(),
        'time_axis': np.arange(0, tn, dt),
        'x_axis': np.linspace(0, extent[0], nrec),
    }

    if save_snapshots:
        results['snapshots'] = p.data.copy()

    return results


def plot_results(results: dict, output_prefix: str = None):
    """
    Plot velocity model and shot record.

    Args:
        results: Dictionary from run_acoustic_wave
        output_prefix: If provided, save figures with this prefix
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Matplotlib not available. Skipping plots.")
        return

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Velocity model
    ax = axes[0]
    im = ax.imshow(results['velocity'].T, cmap='jet', aspect='auto')
    ax.set_title('Velocity Model')
    ax.set_xlabel('X (grid points)')
    ax.set_ylabel('Z (grid points)')
    plt.colorbar(im, ax=ax, label='Velocity (m/s)')

    # Shot record
    ax = axes[1]
    shot = results['shot_record']
    clip = 0.1 * np.abs(shot).max()
    im = ax.imshow(
        shot, cmap='gray', aspect='auto',
        vmin=-clip, vmax=clip,
        extent=[results['x_axis'][0], results['x_axis'][-1],
                results['time_axis'][-1], results['time_axis'][0]]
    )
    ax.set_title('Shot Record')
    ax.set_xlabel('X (m)')
    ax.set_ylabel('Time (ms)')

    plt.tight_layout()

    if output_prefix:
        plt.savefig(f'{output_prefix}_results.png', dpi=150)
        print(f"Saved: {output_prefix}_results.png")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description='2D acoustic wave propagation using Devito'
    )
    parser.add_argument('--nx', type=int, default=101,
                        help='Grid points in x (default: 101)')
    parser.add_argument('--nz', type=int, default=101,
                        help='Grid points in z (default: 101)')
    parser.add_argument('--nt', type=int, default=500,
                        help='Number of time steps (default: 500)')
    parser.add_argument('--dx', type=float, default=10.0,
                        help='Grid spacing in meters (default: 10)')
    parser.add_argument('--dt', type=float, default=1.0,
                        help='Time step in ms (default: 1.0)')
    parser.add_argument('--f0', type=float, default=10.0,
                        help='Source frequency in Hz (default: 10)')
    parser.add_argument('--output', '-o', type=str,
                        help='Output file for shot record (.npy)')
    parser.add_argument('--save-snapshots', action='store_true',
                        help='Save wavefield snapshots (memory intensive)')
    parser.add_argument('--plot', action='store_true',
                        help='Plot results')
    parser.add_argument('--plot-output', type=str,
                        help='Save plots with this prefix')
    args = parser.parse_args()

    # Run simulation
    results = run_acoustic_wave(
        nx=args.nx,
        nz=args.nz,
        nt=args.nt,
        dx=args.dx,
        dt=args.dt,
        f0=args.f0,
        save_snapshots=args.save_snapshots
    )

    # Save output
    if args.output:
        np.save(args.output, results['shot_record'])
        print(f"Saved shot record: {args.output}")

        # Also save velocity
        vel_output = args.output.replace('.npy', '_velocity.npy')
        np.save(vel_output, results['velocity'])
        print(f"Saved velocity model: {vel_output}")

        if args.save_snapshots:
            snap_output = args.output.replace('.npy', '_snapshots.npy')
            np.save(snap_output, results['snapshots'])
            print(f"Saved snapshots: {snap_output}")

    # Plot
    if args.plot or args.plot_output:
        plot_results(results, args.plot_output)


if __name__ == '__main__':
    main()
