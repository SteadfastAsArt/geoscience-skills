#!/usr/bin/env python3
"""
Seismic deconvolution using PyLops.

Demonstrates recovering reflectivity from a seismic trace by deconvolving
the source wavelet. Shows both simple and regularized inversion approaches.

Usage:
    python deconvolution.py
    python deconvolution.py --noise 0.1 --regularization 0.01
    python deconvolution.py --wavelet ricker --output result.png
"""

import argparse

import matplotlib.pyplot as plt
import numpy as np
import pylops


def create_ricker_wavelet(f: float, dt: float, length: float) -> np.ndarray:
    """
    Create a Ricker (Mexican hat) wavelet.

    Args:
        f: Peak frequency in Hz
        dt: Sample interval in seconds
        length: Wavelet length in seconds

    Returns:
        Wavelet samples
    """
    t = np.arange(-length / 2, length / 2, dt)
    pi2 = (np.pi * f * t) ** 2
    wavelet = (1 - 2 * pi2) * np.exp(-pi2)
    return wavelet


def create_ormsby_wavelet(
    f1: float, f2: float, f3: float, f4: float, dt: float, length: float
) -> np.ndarray:
    """
    Create an Ormsby (bandpass) wavelet.

    Args:
        f1, f2: Low cut frequencies (Hz)
        f3, f4: High cut frequencies (Hz)
        dt: Sample interval in seconds
        length: Wavelet length in seconds

    Returns:
        Wavelet samples
    """
    t = np.arange(-length / 2, length / 2, dt)

    def sinc_sq(f, t):
        return (np.pi * f) ** 2 * np.sinc(f * t) ** 2

    wavelet = (
        (sinc_sq(f4, t) * f4**2 - sinc_sq(f3, t) * f3**2) / (f4 - f3)
        - (sinc_sq(f2, t) * f2**2 - sinc_sq(f1, t) * f1**2) / (f2 - f1)
    ) / (f4 - f1)

    # Normalize
    wavelet = wavelet / np.max(np.abs(wavelet))
    return wavelet


def create_synthetic_reflectivity(n: int, n_reflectors: int = 10, seed: int = 42) -> np.ndarray:
    """
    Create synthetic sparse reflectivity series.

    Args:
        n: Number of samples
        n_reflectors: Number of non-zero reflectors
        seed: Random seed for reproducibility

    Returns:
        Reflectivity series
    """
    rng = np.random.default_rng(seed)
    reflectivity = np.zeros(n)
    positions = rng.choice(n, size=n_reflectors, replace=False)
    reflectivity[positions] = rng.uniform(-1, 1, n_reflectors)
    return reflectivity


def deconvolve(
    seismic: np.ndarray,
    wavelet: np.ndarray,
    offset: int,
    noise_level: float = 0.0,
    regularization: float = 0.0,
    solver: str = "lsqr",
    niter: int = 100,
) -> tuple[np.ndarray, dict]:
    """
    Deconvolve seismic trace to recover reflectivity.

    Args:
        seismic: Seismic trace (convolved signal)
        wavelet: Source wavelet
        offset: Wavelet offset (typically half wavelet length)
        noise_level: Estimated noise level for Tikhonov damping
        regularization: Regularization weight for smoothness constraint
        solver: Solver type ('lsqr', 'cgls', 'normal', 'fista')
        niter: Number of iterations for iterative solvers

    Returns:
        Tuple of (estimated_reflectivity, info_dict)
    """
    n = len(seismic)

    # Create convolution operator
    C = pylops.signalprocessing.Convolve1D(n, h=wavelet, offset=offset, dtype="float64")

    info = {"solver": solver}

    if solver == "normal":
        # Normal equations (direct solve)
        if regularization > 0:
            Reg = pylops.SecondDerivative(n, dtype="float64")
            x_est = pylops.optimization.leastsquares.NormalEquationsInversion(
                C, [Reg], seismic, epsNRs=[regularization]
            )
        else:
            x_est = pylops.optimization.leastsquares.NormalEquationsInversion(
                C, None, seismic
            )

    elif solver == "lsqr":
        # LSQR iterative solver
        x_est, istop, itn, *_ = pylops.optimization.solver.lsqr(
            C, seismic, damp=noise_level, iter_lim=niter
        )
        info["iterations"] = itn
        info["istop"] = istop

    elif solver == "cgls":
        # Conjugate gradient least squares
        x_est, itn, cost = pylops.optimization.solver.cgls(C, seismic, niter=niter)
        info["iterations"] = itn
        info["cost_history"] = cost

    elif solver == "fista":
        # Sparse recovery with L1 regularization
        x_est, itn, cost = pylops.optimization.sparsity.fista(
            C, seismic, niter=niter, eps=regularization, returninfo=True
        )
        info["iterations"] = itn
        info["cost_history"] = cost

    elif solver == "regularized":
        # Regularized inversion with smoothness
        Reg = pylops.SecondDerivative(n, dtype="float64")
        x_est = pylops.optimization.leastsquares.RegularizedInversion(
            C, [Reg], seismic, epsRs=[regularization]
        )

    else:
        raise ValueError(f"Unknown solver: {solver}")

    # Compute residual
    residual = C @ x_est - seismic
    info["residual_norm"] = np.linalg.norm(residual)
    info["relative_residual"] = info["residual_norm"] / np.linalg.norm(seismic)

    return x_est, info


def main():
    parser = argparse.ArgumentParser(
        description="Seismic deconvolution using PyLops",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python deconvolution.py
    python deconvolution.py --noise 0.1 --regularization 0.01
    python deconvolution.py --wavelet ricker --solver fista --regularization 0.1
        """,
    )
    parser.add_argument(
        "--wavelet",
        choices=["ricker", "ormsby"],
        default="ricker",
        help="Wavelet type (default: ricker)",
    )
    parser.add_argument(
        "--frequency",
        type=float,
        default=25.0,
        help="Peak frequency for Ricker wavelet in Hz (default: 25)",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=500,
        help="Number of samples (default: 500)",
    )
    parser.add_argument(
        "--reflectors",
        type=int,
        default=15,
        help="Number of reflectors (default: 15)",
    )
    parser.add_argument(
        "--noise",
        type=float,
        default=0.05,
        help="Noise level (standard deviation) (default: 0.05)",
    )
    parser.add_argument(
        "--solver",
        choices=["lsqr", "cgls", "normal", "fista", "regularized"],
        default="regularized",
        help="Solver type (default: regularized)",
    )
    parser.add_argument(
        "--regularization",
        type=float,
        default=0.01,
        help="Regularization weight (default: 0.01)",
    )
    parser.add_argument(
        "--niter",
        type=int,
        default=100,
        help="Number of iterations for iterative solvers (default: 100)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output figure filename (default: display)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed (default: 42)",
    )
    args = parser.parse_args()

    # Parameters
    dt = 0.004  # 4 ms sample rate
    n = args.samples

    # Create wavelet
    if args.wavelet == "ricker":
        wavelet = create_ricker_wavelet(args.frequency, dt, 0.1)
    else:
        wavelet = create_ormsby_wavelet(5, 10, 40, 50, dt, 0.1)

    offset = len(wavelet) // 2

    # Create synthetic reflectivity
    reflectivity = create_synthetic_reflectivity(n, args.reflectors, args.seed)

    # Create convolution operator and generate seismic
    C = pylops.signalprocessing.Convolve1D(n, h=wavelet, offset=offset, dtype="float64")
    seismic_clean = C @ reflectivity

    # Add noise
    rng = np.random.default_rng(args.seed)
    noise = args.noise * rng.standard_normal(n)
    seismic_noisy = seismic_clean + noise

    # Deconvolve
    reflectivity_est, info = deconvolve(
        seismic_noisy,
        wavelet,
        offset,
        noise_level=args.noise,
        regularization=args.regularization,
        solver=args.solver,
        niter=args.niter,
    )

    # Compute metrics
    correlation = np.corrcoef(reflectivity, reflectivity_est)[0, 1]

    print(f"Deconvolution Results:")
    print(f"  Solver: {args.solver}")
    print(f"  Noise level: {args.noise:.3f}")
    print(f"  Regularization: {args.regularization}")
    print(f"  Relative residual: {info['relative_residual']:.4f}")
    print(f"  Correlation with true: {correlation:.4f}")

    # Plot
    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
    t = np.arange(n) * dt * 1000  # Convert to ms

    # Wavelet
    ax = axes[0]
    t_wav = np.arange(len(wavelet)) * dt * 1000
    ax.plot(t_wav, wavelet, "k", lw=1.5)
    ax.fill_between(t_wav, wavelet, 0, where=wavelet > 0, alpha=0.3)
    ax.set_ylabel("Amplitude")
    ax.set_title(f"Source Wavelet ({args.wavelet.title()}, {args.frequency} Hz)")
    ax.set_xlim(t_wav[0], t_wav[-1])

    # True reflectivity
    ax = axes[1]
    ax.stem(t, reflectivity, linefmt="k-", markerfmt="ko", basefmt=" ")
    ax.set_ylabel("Amplitude")
    ax.set_title(f"True Reflectivity ({args.reflectors} reflectors)")
    ax.set_xlim(t[0], t[-1])

    # Seismic trace
    ax = axes[2]
    ax.plot(t, seismic_clean, "b", alpha=0.5, label="Clean")
    ax.plot(t, seismic_noisy, "k", lw=0.8, label="Noisy")
    ax.fill_between(t, seismic_noisy, 0, where=seismic_noisy > 0, alpha=0.3, color="k")
    ax.set_ylabel("Amplitude")
    ax.set_title(f"Seismic Trace (SNR: {1/args.noise:.1f})")
    ax.legend(loc="upper right")
    ax.set_xlim(t[0], t[-1])

    # Estimated reflectivity
    ax = axes[3]
    ax.stem(t, reflectivity, linefmt="b-", markerfmt="bo", basefmt=" ", label="True")
    ax.stem(
        t,
        reflectivity_est,
        linefmt="r-",
        markerfmt="r^",
        basefmt=" ",
        label="Estimated",
    )
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Amplitude")
    ax.set_title(
        f"Recovered Reflectivity (corr={correlation:.3f}, "
        f"solver={args.solver}, reg={args.regularization})"
    )
    ax.legend(loc="upper right")
    ax.set_xlim(t[0], t[-1])

    plt.tight_layout()

    if args.output:
        plt.savefig(args.output, dpi=150, bbox_inches="tight")
        print(f"Figure saved to: {args.output}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
