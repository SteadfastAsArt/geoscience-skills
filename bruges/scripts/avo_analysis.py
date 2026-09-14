#!/usr/bin/env python3
"""
AVO Analysis and Classification.

Usage:
    python avo_analysis.py --vp1 3000 --vs1 1500 --rho1 2.4 --vp2 3500 --vs2 1800 --rho2 2.5
    python avo_analysis.py --vp1 3000 --vs1 1500 --rho1 2.4 --vp2 3500 --vs2 1800 --rho2 2.5 --no-plot
"""

import argparse
import sys
from dataclasses import dataclass
from typing import Tuple, Optional

import numpy as np


@dataclass
class LayerProperties:
    """Elastic properties for a layer."""
    vp: float   # P-wave velocity (m/s)
    vs: float   # S-wave velocity (m/s)
    rho: float  # Density (g/cc)

    def __post_init__(self):
        values = np.asarray([self.vp, self.vs, self.rho], dtype=float)
        if values.shape != (3,) or not np.all(np.isfinite(values)) or np.any(values <= 0):
            raise ValueError("Solid-layer Vp, Vs and density must be finite positive scalars")
        if self.vp**2 <= (4.0 / 3.0) * self.vs**2:
            raise ValueError("Solid-layer elastic bulk modulus must be positive")

    @property
    def impedance(self) -> float:
        """Acoustic impedance in (m/s)*(g/cm3); multiply by 1000 for SI."""
        return self.vp * self.rho

    @property
    def vp_vs_ratio(self) -> float:
        """Vp/Vs ratio."""
        return self.vp / self.vs

    @property
    def poissons_ratio(self) -> float:
        """Poisson's ratio."""
        r = self.vp_vs_ratio
        return (r**2 - 2) / (2 * (r**2 - 1))


def zoeppritz(layer1: LayerProperties, layer2: LayerProperties,
              theta: np.ndarray) -> np.ndarray:
    """
    Calculate P-wave reflection coefficient using Zoeppritz equations.

    Args:
        layer1: Upper layer properties
        layer2: Lower layer properties
        theta: Incidence angles in degrees

    Returns:
        Reflection coefficients (Rpp)
    """
    theta = _validate_angles(theta)
    try:
        from bruges.reflection import zoeppritz as brg_zoeppritz
    except ImportError as error:
        raise ImportError("Bruges is required for exact Zoeppritz reflectivity; "
                          "install its dependencies in an isolated environment") from error
    result = np.atleast_1d(brg_zoeppritz(layer1.vp, layer1.vs, layer1.rho,
                                       layer2.vp, layer2.vs, layer2.rho, theta))
    if not np.all(np.isfinite(result)):
        raise ValueError("Zoeppritz produced nonfinite reflectivity for these inputs")
    return result


def _validate_angles(theta):
    theta = np.atleast_1d(np.asarray(theta, dtype=float))
    if (theta.ndim != 1 or not theta.size or not np.all(np.isfinite(theta))
            or np.any(theta < 0) or np.any(theta >= 90)):
        raise ValueError("Incidence angles must be finite and satisfy 0 <= angle < 90 degrees")
    return theta


def shuey(layer1: LayerProperties, layer2: LayerProperties,
          theta: np.ndarray) -> np.ndarray:
    """
    Calculate P-wave reflection using Shuey 2-term approximation.

    Args:
        layer1: Upper layer properties
        layer2: Lower layer properties
        theta: Incidence angles in degrees

    Returns:
        Reflection coefficients (Rpp)
    """
    theta_rad = np.deg2rad(_validate_angles(theta))

    # Contrasts
    dvp = layer2.vp - layer1.vp
    dvs = layer2.vs - layer1.vs
    drho = layer2.rho - layer1.rho

    # Averages
    vp_avg = (layer1.vp + layer2.vp) / 2
    vs_avg = (layer1.vs + layer2.vs) / 2
    rho_avg = (layer1.rho + layer2.rho) / 2

    # Intercept (normal incidence)
    R0 = 0.5 * (dvp/vp_avg + drho/rho_avg)

    # Gradient
    G = 0.5 * dvp/vp_avg - 2 * (vs_avg/vp_avg)**2 * (drho/rho_avg + 2*dvs/vs_avg)

    # Shuey 2-term
    Rpp = R0 + G * np.sin(theta_rad)**2

    return Rpp


def calculate_intercept_gradient(layer1: LayerProperties,
                                  layer2: LayerProperties) -> Tuple[float, float]:
    """
    Calculate AVO intercept and gradient.

    Returns:
        Tuple of (intercept, gradient)
    """
    # Use small angle approximation
    theta = np.array([0, 5, 10, 15, 20])
    Rpp = shuey(layer1, layer2, theta)

    # Linear fit: Rpp = A + B * sin^2(theta)
    sin2 = np.sin(np.deg2rad(theta))**2
    A = np.polyfit(sin2, Rpp, 1)

    gradient = A[0]
    intercept = A[1]

    return intercept, gradient


def classify_avo(intercept: float, gradient: float) -> str:
    """
    Heuristic Class I-IV screening using an illustrative intercept threshold.

    Returns:
        AVO class or an unclassified label. IIp requires checking a polarity
        reversal over the measured angle range and is not inferred here.
    """
    if not np.isfinite(intercept) or not np.isfinite(gradient):
        raise ValueError("AVO intercept and gradient must be finite")
    if intercept > 0.02:
        if gradient < 0:
            return "I"
        else:
            return "I (anomalous)"
    elif intercept > -0.02:
        if gradient < 0:
            return "II"
        else:
            return "Unclassified (near-zero intercept, nonnegative gradient)"
    else:  # intercept < -0.02
        if gradient < 0:
            return "III"
        else:
            return "IV"


def analyze_avo(layer1: LayerProperties, layer2: LayerProperties,
                theta_max: float = 45, theta_step: float = 1) -> dict:
    """
    Perform full AVO analysis.

    Args:
        layer1: Upper layer properties
        layer2: Lower layer properties
        theta_max: Maximum angle to compute
        theta_step: Angle increment

    Returns:
        Dictionary with analysis results
    """
    _validate_angles([theta_max])
    if not np.isscalar(theta_step) or not np.isfinite(theta_step) or theta_step <= 0:
        raise ValueError("Angle step must be finite and positive")
    theta = np.append(np.arange(0, theta_max, theta_step), theta_max)

    # Calculate reflectivity
    Rpp = zoeppritz(layer1, layer2, theta)

    # Intercept and gradient
    intercept, gradient = calculate_intercept_gradient(layer1, layer2)

    # Classification
    avo_class = classify_avo(intercept, gradient)

    # Impedance contrast
    imp_contrast = (layer2.impedance - layer1.impedance) / \
                   (layer2.impedance + layer1.impedance)

    return {
        "theta": theta,
        "Rpp": Rpp,
        "intercept": intercept,
        "gradient": gradient,
        "avo_class": avo_class,
        "impedance_contrast": imp_contrast,
        "layer1": layer1,
        "layer2": layer2,
    }


def print_report(results: dict) -> None:
    """Print AVO analysis report."""
    print("\n" + "=" * 60)
    print("AVO ANALYSIS REPORT")
    print("=" * 60)

    layer1 = results["layer1"]
    layer2 = results["layer2"]

    print("\nLayer Properties:")
    print(f"  Upper layer: Vp={layer1.vp:.0f} m/s, Vs={layer1.vs:.0f} m/s, "
          f"rho={layer1.rho:.2f} g/cc")
    print(f"  Lower layer: Vp={layer2.vp:.0f} m/s, Vs={layer2.vs:.0f} m/s, "
          f"rho={layer2.rho:.2f} g/cc")

    print("\nDerived Properties:")
    print(f"  Upper Zp: {layer1.impedance * 1000:.0f} kg/(m² s)")
    print(f"  Lower Zp: {layer2.impedance * 1000:.0f} kg/(m² s)")
    print(f"  Impedance contrast: {results['impedance_contrast']:.4f}")

    print("\nAVO Attributes:")
    print(f"  Intercept (A): {results['intercept']:.4f}")
    print(f"  Gradient (B): {results['gradient']:.4f}")
    print(f"  Heuristic AVO Class: {results['avo_class']}")
    print("  Screening uses |intercept| = 0.02; interpret with polarity, "
          "angle coverage and geology. IIp is not assigned automatically.")

    print("\nReflectivity at key angles:")
    theta = results["theta"]
    Rpp = results["Rpp"]
    reported_indices = set()
    for angle in [0, 15, 30, 45]:
        if angle <= theta.max():
            idx = np.argmin(np.abs(theta - angle))
            if idx not in reported_indices:
                print(f"  R({theta[idx]:g} deg): {Rpp[idx]:.4f}")
                reported_indices.add(idx)
    if np.any(np.abs(np.imag(Rpp)) > 1e-10):
        print("  Complex reflectivity retained; interpret both amplitude and phase.")

    print("=" * 60)


def plot_avo(results: dict, output_path: Optional[str] = None) -> None:
    """
    Plot AVO curve.

    Args:
        results: Analysis results from analyze_avo
        output_path: If provided, save figure to this path
    """
    import matplotlib.pyplot as plt

    theta = results["theta"]
    Rpp = results["Rpp"]

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(theta, np.real(Rpp), 'b-', linewidth=2, label='Zoeppritz (real)')
    if np.any(np.abs(np.imag(Rpp)) > 1e-10):
        ax.plot(theta, np.imag(Rpp), 'g:', linewidth=2, label='Zoeppritz (imaginary)')

    # Add intercept + gradient line
    sin2 = np.sin(np.deg2rad(theta))**2
    Rpp_linear = results["intercept"] + results["gradient"] * sin2
    ax.plot(theta, Rpp_linear, 'r--', linewidth=1.5, label='Shuey two-term approximation')

    ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5)
    ax.set_xlabel('Incidence Angle (degrees)', fontsize=12)
    ax.set_ylabel('Reflection Coefficient (Rpp)', fontsize=12)
    ax.set_title(f'AVO Response - Class {results["avo_class"]}', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Add annotation
    text = f'A = {results["intercept"]:.4f}\nB = {results["gradient"]:.4f}'
    ax.text(0.95, 0.95, text, transform=ax.transAxes,
            fontsize=10, verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150)
        print(f"Figure saved to: {output_path}")
    else:
        plt.show()
    plt.close(fig)
    return fig


def main():
    parser = argparse.ArgumentParser(
        description="AVO Analysis and Classification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Specify properties directly
  python avo_analysis.py --vp1 3000 --vs1 1500 --rho1 2.4 \\
                         --vp2 3500 --vs2 1800 --rho2 2.5

  # Save plot
  python avo_analysis.py --vp1 3000 --vs1 1500 --rho1 2.4 \\
                         --vp2 3500 --vs2 1800 --rho2 2.5 \\
                         --plot avo_response.png
"""
    )

    # Layer 1 properties
    parser.add_argument("--vp1", type=float, required=True,
                        help="Upper layer Vp (m/s)")
    parser.add_argument("--vs1", type=float, required=True,
                        help="Upper layer Vs (m/s)")
    parser.add_argument("--rho1", type=float, required=True,
                        help="Upper layer density (g/cc)")

    # Layer 2 properties
    parser.add_argument("--vp2", type=float, required=True,
                        help="Lower layer Vp (m/s)")
    parser.add_argument("--vs2", type=float, required=True,
                        help="Lower layer Vs (m/s)")
    parser.add_argument("--rho2", type=float, required=True,
                        help="Lower layer density (g/cc)")

    # Options
    parser.add_argument("--theta-max", type=float, default=45,
                        help="Maximum angle (default: 45)")
    parser.add_argument("--plot", type=str, default=None,
                        help="Save plot to file")
    parser.add_argument("--no-plot", action="store_true",
                        help="Suppress plot display")

    args = parser.parse_args()

    try:
        layer1 = LayerProperties(vp=args.vp1, vs=args.vs1, rho=args.rho1)
        layer2 = LayerProperties(vp=args.vp2, vs=args.vs2, rho=args.rho2)
        results = analyze_avo(layer1, layer2, theta_max=args.theta_max)
        print_report(results)
        if args.plot or not args.no_plot:
            plot_avo(results, output_path=args.plot)
    except (ValueError, ImportError, OSError, np.linalg.LinAlgError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
