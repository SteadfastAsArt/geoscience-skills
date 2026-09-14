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
    from disba import DispersionError, PhaseDispersion, GroupDispersion, PhaseSensitivity
except ImportError:
    print("Error: install disba in an isolated Python environment", file=sys.stderr)
    sys.exit(1)


def validate_model(thickness, vp, vs, rho):
    """Validate solid-layer arrays in km, km/s, km/s and g/cm3."""
    arrays = tuple(np.asarray(a, dtype=float) for a in (thickness, vp, vs, rho))
    if any(a.ndim != 1 for a in arrays):
        raise ValueError("Model properties must be one-dimensional arrays")
    if not arrays[0].size or any(a.size != arrays[0].size for a in arrays):
        raise ValueError("Model properties must have the same nonzero length")
    if any(not np.all(np.isfinite(a)) for a in arrays):
        raise ValueError("Model properties must be finite")
    thickness, vp, vs, rho = arrays
    if np.any(thickness[:-1] <= 0) or thickness[-1] != 0:
        raise ValueError("Positive layer thicknesses must end with a zero half-space")
    if np.any(vp <= 0) or np.any(vs <= 0) or np.any(rho <= 0):
        raise ValueError("This helper requires positive solid velocities and density")
    if np.any(vp**2 <= (4.0 / 3.0) * vs**2):
        raise ValueError("Solid elastic bulk modulus must be positive")
    return arrays


def validate_periods(periods):
    periods = np.asarray(periods, dtype=float)
    if (periods.ndim != 1 or not periods.size or
            not np.all(np.isfinite(periods)) or np.any(periods <= 0) or
            np.any(np.diff(periods) <= 0)):
        raise ValueError("Periods must be finite, positive and strictly increasing")
    return periods


def _validate_wave_mode(wave, mode):
    if wave not in ("rayleigh", "love"):
        raise ValueError("Wave must be rayleigh or love")
    if not isinstance(mode, (int, np.integer)) or mode < 0:
        raise ValueError("Mode must be a nonnegative integer")


def _align_curve(curve, periods):
    """Retain the requested grid, marking unavailable roots with NaN."""
    values = np.full(periods.shape, np.nan)
    indices = np.searchsorted(periods, curve.period)
    if np.any(indices >= periods.size) or not np.array_equal(periods[indices], curve.period):
        raise ValueError("Solver returned periods outside the requested grid")
    values[indices] = curve.velocity
    return values


def create_gradient_model(n_layers=10, vs_top=0.5, vs_bot=4.0, total_depth=10.0):
    """Illustrative gradient; constant Vp/Vs and linear density are assumptions."""
    if not isinstance(n_layers, (int, np.integer)) or n_layers < 1:
        raise ValueError("n_layers must be a positive integer")
    if not np.isfinite(total_depth) or total_depth <= 0:
        raise ValueError("total_depth must be finite and positive")
    layer_thickness = total_depth / n_layers
    thickness = np.full(n_layers + 1, layer_thickness)
    thickness[-1] = 0.0  # half-space

    vs = np.linspace(vs_top, vs_bot, n_layers + 1)
    vp = vs * 1.73
    rho = 0.32 * vp + 0.77

    return validate_model(thickness, vp, vs, rho)


def create_lvz_model():
    """Illustrative LVZ; the linear density estimate is not Gardner's relation."""
    thickness = np.array([1.0, 1.0, 2.0, 0.0])
    vs = np.array([1.0, 0.7, 2.0, 3.5])
    vp = vs * 1.73
    rho = 0.32 * vp + 0.77

    return validate_model(thickness, vp, vs, rho)


def create_crust_model():
    """Create a simplified continental crust model."""
    thickness = np.array([2.0, 15.0, 18.0, 0.0])
    vs = np.array([2.0, 3.5, 3.9, 4.5])
    vp = np.array([3.5, 6.1, 6.8, 8.1])
    rho = np.array([2.3, 2.7, 2.9, 3.3])

    return validate_model(thickness, vp, vs, rho)


def load_model_file(filepath: str):
    """
    Load velocity model from text file.

    Expected format (space/tab separated):
    thickness vp vs rho   # Required header; km, km/s, km/s, g/cm3.
    0.5 1.5 0.8 1.8
    1.0 2.5 1.4 2.0
    0.0 4.0 2.3 2.3
    """
    with open(filepath, encoding="utf-8-sig") as source:
        header = source.readline().strip().lstrip("#").split("#", 1)[0].split()
        if header != ["thickness", "vp", "vs", "rho"]:
            raise ValueError("Model file must start with: thickness vp vs rho")
        data = np.loadtxt(source, ndmin=2)
    if not data.size or data.shape[1] != 4:
        raise ValueError("Model file must contain four numeric columns")
    return validate_model(*data.T)


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
        dict with requested periods and aligned velocity arrays per mode.
        Missing roots remain NaN; numerical failures are recorded in errors.
    """
    if periods is None:
        periods = np.linspace(0.1, 10.0, 100)

    model = validate_model(thickness, vp, vs, rho)
    periods = validate_periods(periods)
    _validate_wave_mode(wave, 0)
    if not isinstance(max_modes, (int, np.integer)) or max_modes < 1:
        raise ValueError("max_modes must be a positive integer")
    pd = PhaseDispersion(*model)
    gd = GroupDispersion(*model)

    results = {
        "periods": periods,
        "wave": wave,
        "modes": {},
        "errors": {},
    }

    for mode in range(max_modes):
        data = {}
        for kind, solver in (("phase", pd), ("group", gd)):
            try:
                curve = solver(periods, mode=mode, wave=wave)
            except DispersionError as error:
                data[f"{kind}_velocity"] = np.full(periods.shape, np.nan)
                results["errors"].setdefault(mode, {})[kind] = str(error)
            else:
                data[f"{kind}_velocity"] = _align_curve(curve, periods)
        results["modes"][mode] = data

    if not any(np.any(np.isfinite(values)) for data in results["modes"].values()
               for values in data.values()):
        raise DispersionError(f"No dispersion roots computed: {results['errors']}")

    return results


def compute_sensitivity(thickness, vp, vs, rho, period, wave="rayleigh", mode=0):
    """
    Compute sensitivity kernels at a specific period.

    Returns:
        dict with sensitivity to vs, vp, rho
    """
    model = validate_model(thickness, vp, vs, rho)
    if not np.isscalar(period):
        raise ValueError("Sensitivity period must be a positive finite scalar")
    period = validate_periods([period])[0]
    _validate_wave_mode(wave, mode)
    ps = PhaseSensitivity(*model)

    sensitivity = {}
    for param in ["velocity_s", "velocity_p", "density"]:
        sensitivity[param] = ps(period, mode=mode, wave=wave, parameter=param)

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
        print(f"\nMode {mode}:")
        for kind in ("phase", "group"):
            values = data[f"{kind}_velocity"]
            valid = np.isfinite(values)
            count = np.count_nonzero(valid)
            if count:
                print(f"  {kind.capitalize()}: {count}/{periods.size} periods, "
                      f"{periods[valid].min():.2f}-{periods[valid].max():.2f} s; "
                      f"{values[valid].min():.3f}-{values[valid].max():.3f} km/s")
            else:
                print(f"  {kind.capitalize()}: no computed roots")
        for kind, error in results.get("errors", {}).get(mode, {}).items():
            print(f"  {kind} root search failed: {error}")


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
    import matplotlib.pyplot as plt

    periods = results["periods"]
    wave = results["wave"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    colors = plt.cm.tab10(np.linspace(0, 1, 10))

    for mode, data in results["modes"].items():
        c = data["phase_velocity"]
        u = data["group_velocity"]

        ax1.plot(periods, c, color=colors[mode % len(colors)], label=f"Mode {mode}")
        ax2.plot(periods, u, color=colors[mode % len(colors)], label=f"Mode {mode}")

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
    plt.close(fig)


def _check_output_paths(input_path, output_path, plot_path):
    """Reject aliases that would replace input or one another's output."""
    paths = [Path(p) for p in (input_path, output_path, plot_path) if p is not None]
    for index, first in enumerate(paths):
        for second in paths[index + 1:]:
            same = first.resolve() == second.resolve()
            if not same and first.exists() and second.exists():
                same = first.samefile(second)
            if same:
                raise ValueError("Input, CSV output and plot output must use different files")


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
        help="Four-column solid model (km, km/s, km/s, g/cm3), with header thickness vp vs rho",
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

    try:
        if (not np.isfinite(args.period_min) or not np.isfinite(args.period_max)
                or not 0 < args.period_min < args.period_max):
            raise ValueError("Require 0 < --period-min < --period-max, both finite")
        if args.n_periods < 2:
            raise ValueError("--n-periods must be at least 2")
        if args.modes < 1:
            raise ValueError("--modes must be at least 1")
        if args.model == "file" and not args.input:
            raise ValueError("--input is required when --model file")
        if args.model != "file" and args.input:
            raise ValueError("--input applies only to --model file")
        _check_output_paths(args.input, args.output, args.plot_file)

        if args.model == "gradient":
            model = create_gradient_model()
        elif args.model == "lvz":
            model = create_lvz_model()
        elif args.model == "crust":
            model = create_crust_model()
        else:
            model = load_model_file(args.input)

        print_model(*model)
        if args.model in ("gradient", "lvz"):
            print("Illustrative model: Vp/Vs = 1.73 and density = 0.32*Vp + 0.77 "
                  "(g/cm3, Vp in km/s); this density estimate is not Gardner's law.")
        periods = np.linspace(args.period_min, args.period_max, args.n_periods)
        results = compute_dispersion(*model, periods=periods, wave=args.wave,
                                     max_modes=args.modes)
        print_dispersion(results)
        if args.output:
            save_dispersion(results, args.output)
        if args.plot or args.plot_file:
            plot_dispersion(results, show=args.plot, save_path=args.plot_file)
    except (ValueError, OSError, DispersionError, ImportError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
