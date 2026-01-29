#!/usr/bin/env python3
"""
Compute and analyze surface wave dispersion curves.

Usage:
    python dispersion_analysis.py --model gradient
    python dispersion_analysis.py --model file --input model.txt
    python dispersion_analysis.py --model gradient --output dispersion.csv
"""

import argparse
import sys
from pathlib import Path

import numpy as np

try:
    from disba import PhaseDispersion, GroupDispersion, PhaseSensitivity
except ImportError:
    print("Error: disba not installed. Run: pip install disba")
    sys.exit(1)


def create_gradient_model(n_layers=10, vs_top=0.5, vs_bot=4.0, total_depth=10.0):
    """Create a linear gradient velocity model."""
    layer_thickness = total_depth / n_layers
    thickness = np.full(n_layers + 1, layer_thickness)
    thickness[-1] = 0.0  # half-space

    vs = np.linspace(vs_top, vs_bot, n_layers + 1)
    vp = vs * 1.73
    rho = 0.32 * vp + 0.77

    return thickness, vp, vs, rho


def create_lvz_model():
    """Create a model with a low velocity zone."""
    thickness = np.array([1.0, 1.0, 2.0, 0.0])
    vs = np.array([1.0, 0.7, 2.0, 3.5])
    vp = vs * 1.73
    rho = 0.32 * vp + 0.77

    return thickness, vp, vs, rho


def create_crust_model():
    """Create a simplified continental crust model."""
    thickness = np.array([2.0, 15.0, 18.0, 0.0])
    vs = np.array([2.0, 3.5, 3.9, 4.5])
    vp = np.array([3.5, 6.1, 6.8, 8.1])
    rho = np.array([2.3, 2.7, 2.9, 3.3])

    return thickness, vp, vs, rho


def load_model_file(filepath: str):
    """
    Load velocity model from text file.

    Expected format (space/tab separated):
    thickness vp vs rho
    0.5 1.5 0.8 1.8
    1.0 2.5 1.4 2.0
    0.0 4.0 2.3 2.3
    """
    data = np.loadtxt(filepath, skiprows=1)
    thickness = data[:, 0]
    vp = data[:, 1]
    vs = data[:, 2]
    rho = data[:, 3]

    return thickness, vp, vs, rho


def compute_dispersion(
    thickness,
    vp,
    vs,
    rho,
    periods=None,
    wave="rayleigh",
    max_modes=1,
):
    """
    Compute phase and group velocity dispersion.

    Args:
        thickness: Layer thicknesses (km)
        vp: P-wave velocities (km/s)
        vs: S-wave velocities (km/s)
        rho: Densities (g/cm3)
        periods: Periods to compute (s), default 0.1-10s
        wave: 'rayleigh' or 'love'
        max_modes: Number of modes to attempt (default 1)

    Returns:
        dict with periods, phase velocities, group velocities per mode
    """
    if periods is None:
        periods = np.linspace(0.1, 10.0, 100)

    pd = PhaseDispersion(*zip(thickness, vp, vs, rho))
    gd = GroupDispersion(*zip(thickness, vp, vs, rho))

    results = {
        "periods": periods,
        "wave": wave,
        "modes": {},
    }

    for mode in range(max_modes):
        try:
            phase_vel = pd(periods, mode=mode, wave=wave)
            group_vel = gd(periods, mode=mode, wave=wave)
            results["modes"][mode] = {
                "phase_velocity": phase_vel,
                "group_velocity": group_vel,
            }
        except Exception as e:
            print(f"Mode {mode} not computed: {e}")
            break

    return results


def compute_sensitivity(thickness, vp, vs, rho, period, wave="rayleigh", mode=0):
    """
    Compute sensitivity kernels at a specific period.

    Returns:
        dict with sensitivity to vs, vp, rho
    """
    ps = PhaseSensitivity(*zip(thickness, vp, vs, rho))

    sensitivity = {}
    for param in ["velocity_s", "velocity_p", "density"]:
        try:
            kernel = ps(period, mode=mode, wave=wave, parameter=param)
            sensitivity[param] = kernel
        except Exception as e:
            print(f"Could not compute sensitivity to {param}: {e}")

    return sensitivity


def print_model(thickness, vp, vs, rho):
    """Print model summary."""
    print("\nVelocity Model:")
    print("-" * 60)
    print(f"{'Layer':>6} {'Thick(km)':>10} {'Vp(km/s)':>10} {'Vs(km/s)':>10} {'Rho(g/cc)':>10}")
    print("-" * 60)

    depth = 0
    for i, (t, p, s, r) in enumerate(zip(thickness, vp, vs, rho)):
        if t == 0:
            print(f"{i+1:>6} {'half-space':>10} {p:>10.2f} {s:>10.2f} {r:>10.2f}")
        else:
            print(f"{i+1:>6} {t:>10.2f} {p:>10.2f} {s:>10.2f} {r:>10.2f}")
            depth += t

    print("-" * 60)
    print(f"Total depth (excluding half-space): {depth:.2f} km")


def print_dispersion(results):
    """Print dispersion results summary."""
    periods = results["periods"]
    wave = results["wave"]

    print(f"\n{wave.capitalize()} Wave Dispersion:")
    print("-" * 60)

    for mode, data in results["modes"].items():
        c = data["phase_velocity"]
        u = data["group_velocity"]

        # Handle potential NaN values
        valid = ~np.isnan(c)
        if np.any(valid):
            print(f"\nMode {mode}:")
            print(f"  Period range: {periods[valid].min():.2f} - {periods[valid].max():.2f} s")
            print(f"  Phase velocity: {np.nanmin(c):.3f} - {np.nanmax(c):.3f} km/s")
            print(f"  Group velocity: {np.nanmin(u):.3f} - {np.nanmax(u):.3f} km/s")
        else:
            print(f"\nMode {mode}: No valid data")


def save_dispersion(results, output_path):
    """Save dispersion results to CSV."""
    periods = results["periods"]

    # Build header and data columns
    header = ["period_s"]
    columns = [periods]

    for mode, data in results["modes"].items():
        header.append(f"phase_mode{mode}_km_s")
        header.append(f"group_mode{mode}_km_s")
        columns.append(data["phase_velocity"])
        columns.append(data["group_velocity"])

    data = np.column_stack(columns)
    np.savetxt(output_path, data, delimiter=",", header=",".join(header), comments="")
    print(f"\nDispersion saved to: {output_path}")


def plot_dispersion(results, show=True, save_path=None):
    """Plot dispersion curves."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Warning: matplotlib not available for plotting")
        return

    periods = results["periods"]
    wave = results["wave"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    colors = plt.cm.tab10(np.linspace(0, 1, 10))

    for mode, data in results["modes"].items():
        c = data["phase_velocity"]
        u = data["group_velocity"]

        ax1.plot(periods, c, color=colors[mode], label=f"Mode {mode}")
        ax2.plot(periods, u, color=colors[mode], label=f"Mode {mode}")

    ax1.set_xlabel("Period (s)")
    ax1.set_ylabel("Phase velocity (km/s)")
    ax1.set_title(f"{wave.capitalize()} Wave Phase Velocity")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    ax2.set_xlabel("Period (s)")
    ax2.set_ylabel("Group velocity (km/s)")
    ax2.set_title(f"{wave.capitalize()} Wave Group Velocity")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Plot saved to: {save_path}")

    if show:
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Compute surface wave dispersion curves"
    )
    parser.add_argument(
        "--model",
        choices=["gradient", "lvz", "crust", "file"],
        default="gradient",
        help="Velocity model type",
    )
    parser.add_argument(
        "--input",
        type=str,
        help="Input model file (required if --model file)",
    )
    parser.add_argument(
        "--wave",
        choices=["rayleigh", "love"],
        default="rayleigh",
        help="Wave type",
    )
    parser.add_argument(
        "--modes",
        type=int,
        default=3,
        help="Maximum number of modes to compute",
    )
    parser.add_argument(
        "--period-min",
        type=float,
        default=0.1,
        help="Minimum period (s)",
    )
    parser.add_argument(
        "--period-max",
        type=float,
        default=10.0,
        help="Maximum period (s)",
    )
    parser.add_argument(
        "--n-periods",
        type=int,
        default=100,
        help="Number of periods",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output CSV file for dispersion data",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Show dispersion plot",
    )
    parser.add_argument(
        "--plot-file",
        type=str,
        help="Save plot to file",
    )
    args = parser.parse_args()

    # Load or create model
    if args.model == "gradient":
        thickness, vp, vs, rho = create_gradient_model()
    elif args.model == "lvz":
        thickness, vp, vs, rho = create_lvz_model()
    elif args.model == "crust":
        thickness, vp, vs, rho = create_crust_model()
    elif args.model == "file":
        if not args.input:
            print("Error: --input required when --model file")
            sys.exit(1)
        if not Path(args.input).exists():
            print(f"Error: File not found: {args.input}")
            sys.exit(1)
        thickness, vp, vs, rho = load_model_file(args.input)

    # Print model
    print_model(thickness, vp, vs, rho)

    # Compute dispersion
    periods = np.linspace(args.period_min, args.period_max, args.n_periods)
    results = compute_dispersion(
        thickness, vp, vs, rho,
        periods=periods,
        wave=args.wave,
        max_modes=args.modes,
    )

    # Print results
    print_dispersion(results)

    # Save if requested
    if args.output:
        save_dispersion(results, args.output)

    # Plot if requested
    if args.plot or args.plot_file:
        plot_dispersion(results, show=args.plot, save_path=args.plot_file)


if __name__ == "__main__":
    main()
