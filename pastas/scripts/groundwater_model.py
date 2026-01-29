#!/usr/bin/env python3
"""
Groundwater time series modeling with Pastas.

Usage:
    python groundwater_model.py <head.csv> <precip.csv> <evap.csv>
    python groundwater_model.py <head.csv> <precip.csv> <evap.csv> --pumping <pump.csv>
    python groundwater_model.py <head.csv> <precip.csv> <evap.csv> --output model.pas
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import pastas as ps


def load_series(filepath: str) -> pd.Series:
    """
    Load a time series from CSV file.

    Expects CSV with datetime index in first column, values in second.
    """
    df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    return df.squeeze()


def create_model(
    head: pd.Series,
    precip: pd.Series,
    evap: pd.Series,
    pumping: pd.Series = None,
    name: str = "groundwater_model",
) -> ps.Model:
    """
    Create a Pastas groundwater model.

    Args:
        head: Groundwater head observations (m)
        precip: Precipitation time series (mm/day)
        evap: Evaporation time series (mm/day)
        pumping: Optional pumping rate series (m3/day)
        name: Model name

    Returns:
        Configured Pastas model (not yet solved)
    """
    ml = ps.Model(head, name=name)

    # Add recharge stress model
    recharge_sm = ps.RechargeModel(
        precip, evap,
        rfunc=ps.Gamma(),
        name='recharge'
    )
    ml.add_stressmodel(recharge_sm)

    # Add pumping if provided
    if pumping is not None:
        pumping_sm = ps.StressModel(
            pumping,
            rfunc=ps.Hantush(),
            name='pumping',
            up=False  # Pumping causes drawdown
        )
        ml.add_stressmodel(pumping_sm)

    return ml


def solve_and_report(ml: ps.Model, noise: bool = False) -> dict:
    """
    Solve model and return statistics.

    Args:
        ml: Pastas model
        noise: Whether to include noise model

    Returns:
        Dictionary of model statistics
    """
    ml.solve(noise=noise)

    stats = {
        'evp': ml.stats.evp(),
        'rmse': ml.stats.rmse(),
        'aic': ml.stats.aic(),
        'bic': ml.stats.bic(),
    }

    return stats


def print_report(ml: ps.Model, stats: dict) -> None:
    """Print model report to console."""
    print("\n" + "=" * 60)
    print(f"Model: {ml.name}")
    print("=" * 60)

    print("\nStress Models:")
    for name in ml.stressmodels:
        sm = ml.stressmodels[name]
        print(f"  - {name}: {sm.rfunc.name}")

    print("\nModel Statistics:")
    print(f"  EVP (Explained Variance):  {stats['evp']:.1f}%")
    print(f"  RMSE:                      {stats['rmse']:.4f} m")
    print(f"  AIC:                       {stats['aic']:.1f}")
    print(f"  BIC:                       {stats['bic']:.1f}")

    print("\nCalibrated Parameters:")
    params = ml.parameters[['optimal', 'stderr', 'pmin', 'pmax']]
    print(params.to_string())


def plot_results(ml: ps.Model, output_path: str = None) -> None:
    """
    Create diagnostic plots.

    Args:
        ml: Solved Pastas model
        output_path: Optional path to save figure
    """
    fig = plt.figure(figsize=(14, 10))

    # Main plot: observed vs simulated
    ax1 = fig.add_subplot(3, 2, (1, 2))
    ml.plot(ax=ax1)
    ax1.set_title('Observed vs Simulated Groundwater Levels')

    # Contributions
    contributions = ml.get_contributions()
    ax2 = fig.add_subplot(3, 2, 3)
    for name, contrib in contributions.items():
        ax2.plot(contrib.index, contrib.values, label=name)
    ax2.legend()
    ax2.set_ylabel('Contribution (m)')
    ax2.set_title('Stress Contributions')

    # Residuals
    ax3 = fig.add_subplot(3, 2, 4)
    residuals = ml.residuals()
    ax3.plot(residuals.index, residuals.values, 'k-', alpha=0.7)
    ax3.axhline(0, color='r', linestyle='--')
    ax3.set_ylabel('Residual (m)')
    ax3.set_title('Model Residuals')

    # Step response
    ax4 = fig.add_subplot(3, 2, 5)
    for name in ml.stressmodels:
        step = ml.get_step_response(name)
        ax4.plot(step.index, step.values, label=name)
    ax4.legend()
    ax4.set_xlabel('Time (days)')
    ax4.set_ylabel('Response')
    ax4.set_title('Step Response Functions')

    # Parameter summary
    ax5 = fig.add_subplot(3, 2, 6)
    ax5.axis('off')
    params = ml.parameters[['optimal', 'stderr']]
    table_text = params.to_string()
    ax5.text(0.1, 0.9, 'Calibrated Parameters:\n\n' + table_text,
             transform=ax5.transAxes, fontsize=9, fontfamily='monospace',
             verticalalignment='top')

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"\nFigure saved to: {output_path}")
    else:
        plt.show()


def compare_response_functions(
    head: pd.Series,
    precip: pd.Series,
    evap: pd.Series
) -> pd.DataFrame:
    """
    Compare different response functions for recharge model.

    Returns:
        DataFrame with comparison statistics
    """
    rfuncs = [
        ps.Gamma(),
        ps.Exponential(),
        ps.Hantush(),
        ps.Polder(),
    ]

    results = []
    for rfunc in rfuncs:
        try:
            ml = ps.Model(head.copy())
            ml.add_stressmodel(ps.RechargeModel(
                precip, evap, rfunc=rfunc, name='recharge'
            ))
            ml.solve(report=False)
            results.append({
                'response_function': rfunc.name,
                'evp': ml.stats.evp(),
                'aic': ml.stats.aic(),
                'bic': ml.stats.bic(),
                'rmse': ml.stats.rmse(),
            })
        except Exception as e:
            results.append({
                'response_function': rfunc.name,
                'evp': None,
                'aic': None,
                'bic': None,
                'rmse': None,
                'error': str(e),
            })

    return pd.DataFrame(results)


def main():
    parser = argparse.ArgumentParser(
        description="Create and solve groundwater time series model"
    )
    parser.add_argument("head", help="Path to head observations CSV")
    parser.add_argument("precip", help="Path to precipitation CSV")
    parser.add_argument("evap", help="Path to evaporation CSV")
    parser.add_argument("--pumping", help="Path to pumping rate CSV")
    parser.add_argument("--name", default="model", help="Model name")
    parser.add_argument("--output", help="Output path for model (.pas)")
    parser.add_argument("--plot", help="Output path for plot (e.g., plot.png)")
    parser.add_argument("--noise", action="store_true", help="Include noise model")
    parser.add_argument("--compare", action="store_true",
                        help="Compare response functions")
    args = parser.parse_args()

    # Load data
    print("Loading data...")
    try:
        head = load_series(args.head)
        precip = load_series(args.precip)
        evap = load_series(args.evap)
        pumping = load_series(args.pumping) if args.pumping else None
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

    print(f"  Head observations: {len(head)} samples")
    print(f"  Date range: {head.index.min()} to {head.index.max()}")

    # Compare response functions if requested
    if args.compare:
        print("\nComparing response functions...")
        comparison = compare_response_functions(head, precip, evap)
        print("\nResponse Function Comparison:")
        print(comparison.to_string(index=False))
        print("\nBest model (lowest AIC):",
              comparison.loc[comparison['aic'].idxmin(), 'response_function'])
        return

    # Create and solve model
    print("\nCreating model...")
    ml = create_model(head, precip, evap, pumping, name=args.name)

    print("Solving model...")
    stats = solve_and_report(ml, noise=args.noise)

    # Print report
    print_report(ml, stats)

    # Save model if requested
    if args.output:
        ml.to_json(args.output)
        print(f"\nModel saved to: {args.output}")

    # Create plots
    plot_results(ml, args.plot)


if __name__ == "__main__":
    main()
