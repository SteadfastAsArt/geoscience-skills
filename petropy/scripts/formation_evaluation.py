#!/usr/bin/env python3
"""
Complete formation evaluation workflow using PetroPy.

Usage:
    python formation_evaluation.py input.las output.las
    python formation_evaluation.py input.las output.las --config params.json
    python formation_evaluation.py input.las --plot
"""

import argparse
import json
from pathlib import Path

import numpy as np

try:
    import petropy as pp
except ImportError:
    print("Error: petropy not installed. Run: pip install petropy")
    exit(1)


DEFAULT_PARAMS = {
    # Shale volume parameters
    "gr_clean": 20,
    "gr_shale": 120,
    "vsh_method": "linear",
    # Porosity parameters
    "rhob_matrix": 2.65,
    "rhob_fluid": 1.0,
    "rhob_shale": 2.45,
    # Saturation parameters
    "sw_method": "archie",
    "rw": 0.05,
    "a": 1.0,
    "m": 2.0,
    "n": 2.0,
    # Permeability parameters
    "perm_method": "timur",
    # Pay cutoffs
    "vsh_cutoff": 0.4,
    "phi_cutoff": 0.08,
    "sw_cutoff": 0.6,
    # Curve names
    "depth_curve": "DEPT",
    "gr_curve": "GR",
    "rhob_curve": "RHOB",
    "nphi_curve": "NPHI",
    "rt_curve": "RT",
}


def load_params(config_file: str = None) -> dict:
    """Load parameters from config file or use defaults."""
    params = DEFAULT_PARAMS.copy()
    if config_file and Path(config_file).exists():
        with open(config_file) as f:
            user_params = json.load(f)
            params.update(user_params)
    return params


def check_curves(log, required: list) -> list:
    """Check which required curves are available."""
    available = list(log.keys())
    missing = [c for c in required if c not in available]
    return missing


def formation_evaluation(las_path: str, params: dict) -> pp.Log:
    """
    Perform complete formation evaluation.

    Args:
        las_path: Path to input LAS file
        params: Dictionary of evaluation parameters

    Returns:
        PetroPy Log object with calculated curves
    """
    log = pp.Log(las_path)
    print(f"Loaded: {las_path}")
    print(f"Curves: {list(log.keys())}")
    print(f"Depth range: {log[params['depth_curve']].min():.1f} - "
          f"{log[params['depth_curve']].max():.1f}")

    # Check required curves
    required = [params['depth_curve'], params['gr_curve']]
    missing = check_curves(log, required)
    if missing:
        print(f"Warning: Missing curves: {missing}")

    # 1. Shale Volume
    if params['gr_curve'] in log.keys():
        print("\nCalculating shale volume...")
        log.shale_volume(
            gr_curve=params['gr_curve'],
            gr_clean=params['gr_clean'],
            gr_shale=params['gr_shale'],
            method=params['vsh_method']
        )
        print(f"  VSH range: {log['VSH'].min():.3f} - {log['VSH'].max():.3f}")

    # 2. Porosity
    if params['rhob_curve'] in log.keys():
        print("\nCalculating porosity...")
        if 'VSH' in log.keys():
            log.formation_porosity(
                rhob_curve=params['rhob_curve'],
                rhob_matrix=params['rhob_matrix'],
                rhob_fluid=params['rhob_fluid'],
                rhob_shale=params['rhob_shale'],
                vsh_curve='VSH'
            )
        else:
            log.formation_porosity(
                rhob_curve=params['rhob_curve'],
                rhob_matrix=params['rhob_matrix'],
                rhob_fluid=params['rhob_fluid']
            )
        print(f"  PHIT range: {log['PHIT'].min():.3f} - {log['PHIT'].max():.3f}")

    # 3. Water Saturation
    if params['rt_curve'] in log.keys() and 'PHIT' in log.keys():
        print("\nCalculating water saturation...")
        log.water_saturation(
            method=params['sw_method'],
            rt_curve=params['rt_curve'],
            porosity_curve='PHIT',
            rw=params['rw'],
            a=params['a'],
            m=params['m'],
            n=params['n']
        )
        print(f"  SW range: {log['SW'].min():.3f} - {log['SW'].max():.3f}")

    # 4. Permeability
    if 'PHIT' in log.keys() and 'SW' in log.keys():
        print("\nCalculating permeability...")
        log.permeability(
            method=params['perm_method'],
            porosity_curve='PHIT',
            sw_curve='SW'
        )
        print(f"  PERM range: {log['PERM'].min():.3f} - {log['PERM'].max():.1f} mD")

    # 5. Pay Flag
    if all(c in log.keys() for c in ['VSH', 'PHIT', 'SW']):
        print("\nCalculating pay zones...")
        pay = (
            (log['VSH'] < params['vsh_cutoff']) &
            (log['PHIT'] > params['phi_cutoff']) &
            (log['SW'] < params['sw_cutoff'])
        )
        log['PAY'] = pay.astype(float)

        # Calculate summaries
        depth = log[params['depth_curve']]
        step = np.median(np.abs(np.diff(depth)))
        net_pay = np.sum(pay) * step
        gross = depth.max() - depth.min()
        ntg = net_pay / gross if gross > 0 else 0

        print(f"  Net pay: {net_pay:.1f} m")
        print(f"  Gross: {gross:.1f} m")
        print(f"  N/G: {ntg:.2%}")

        # Pay zone averages
        if np.any(pay):
            print(f"  Avg porosity (pay): {log['PHIT'][pay].mean():.3f}")
            print(f"  Avg Sw (pay): {log['SW'][pay].mean():.3f}")
            print(f"  Avg Sh (pay): {1 - log['SW'][pay].mean():.3f}")

    return log


def create_summary_plot(log, params: dict, output_path: str = None):
    """Create formation evaluation summary plot."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Warning: matplotlib not installed, skipping plot")
        return

    depth = log[params['depth_curve']]

    fig, axes = plt.subplots(1, 5, figsize=(15, 10), sharey=True)
    fig.suptitle('Formation Evaluation Summary', fontsize=14)

    # Track 1: GR and Vsh
    ax = axes[0]
    if params['gr_curve'] in log.keys():
        ax.plot(log[params['gr_curve']], depth, 'g-', linewidth=0.5, label='GR')
        ax.fill_betweenx(depth, log[params['gr_curve']], 0, alpha=0.3, color='green')
    if 'VSH' in log.keys():
        ax2 = ax.twiny()
        ax2.plot(log['VSH'], depth, 'brown', linewidth=1, label='VSH')
        ax2.set_xlim(0, 1)
        ax2.set_xlabel('VSH (v/v)', color='brown')
    ax.set_xlim(0, 150)
    ax.set_xlabel('GR (API)', color='green')
    ax.set_ylabel('Depth')

    # Track 2: Resistivity
    ax = axes[1]
    if params['rt_curve'] in log.keys():
        ax.semilogx(log[params['rt_curve']], depth, 'r-', linewidth=0.5)
    ax.set_xlim(0.1, 1000)
    ax.set_xlabel('RT (ohm-m)')

    # Track 3: Porosity
    ax = axes[2]
    if params['nphi_curve'] in log.keys():
        ax.plot(log[params['nphi_curve']], depth, 'b-', linewidth=0.5, label='NPHI')
    if 'PHIT' in log.keys():
        ax.plot(log['PHIT'], depth, 'r-', linewidth=1, label='PHIT')
    ax.set_xlim(0.45, -0.15)
    ax.set_xlabel('Porosity (v/v)')
    ax.legend(loc='upper right')

    # Track 4: Saturation
    ax = axes[3]
    if 'SW' in log.keys():
        ax.plot(log['SW'], depth, 'b-', linewidth=0.5)
        ax.fill_betweenx(depth, log['SW'], 1, alpha=0.3, color='green', label='HC')
        ax.fill_betweenx(depth, 0, log['SW'], alpha=0.3, color='blue', label='Water')
    ax.set_xlim(0, 1)
    ax.set_xlabel('Sw (v/v)')
    ax.legend(loc='upper right')

    # Track 5: Pay
    ax = axes[4]
    if 'PAY' in log.keys():
        ax.fill_betweenx(depth, log['PAY'], 0, alpha=0.5, color='yellow')
    ax.set_xlim(0, 1.5)
    ax.set_xlabel('Pay Flag')

    axes[0].invert_yaxis()

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=200, bbox_inches='tight')
        print(f"\nPlot saved: {output_path}")
    else:
        plt.show()


def print_summary_table(log, params: dict):
    """Print formation evaluation summary table."""
    depth = log[params['depth_curve']]

    print("\n" + "=" * 60)
    print("FORMATION EVALUATION SUMMARY")
    print("=" * 60)

    if 'PAY' in log.keys():
        pay = log['PAY'] > 0.5
        step = np.median(np.abs(np.diff(depth)))

        print(f"\n{'Parameter':<25} {'Pay Zone':<15} {'Total':<15}")
        print("-" * 55)

        if 'PHIT' in log.keys():
            print(f"{'Avg Porosity (v/v)':<25} "
                  f"{log['PHIT'][pay].mean():.3f} "
                  f"          {log['PHIT'].mean():.3f}")

        if 'SW' in log.keys():
            print(f"{'Avg Sw (v/v)':<25} "
                  f"{log['SW'][pay].mean():.3f} "
                  f"          {log['SW'].mean():.3f}")
            print(f"{'Avg Sh (v/v)':<25} "
                  f"{(1 - log['SW'][pay]).mean():.3f} "
                  f"          {(1 - log['SW']).mean():.3f}")

        if 'VSH' in log.keys():
            print(f"{'Avg Vsh (v/v)':<25} "
                  f"{log['VSH'][pay].mean():.3f} "
                  f"          {log['VSH'].mean():.3f}")

        if 'PERM' in log.keys():
            print(f"{'Avg Perm (mD)':<25} "
                  f"{log['PERM'][pay].mean():.2f} "
                  f"          {log['PERM'].mean():.2f}")

        print("-" * 55)
        print(f"{'Net Pay (m)':<25} {np.sum(pay) * step:.1f}")
        print(f"{'Gross Interval (m)':<25} {depth.max() - depth.min():.1f}")
        print(f"{'Net-to-Gross':<25} {np.sum(pay) / len(pay):.2%}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Formation evaluation from well logs"
    )
    parser.add_argument("input", help="Input LAS file")
    parser.add_argument("output", nargs="?", help="Output LAS file")
    parser.add_argument(
        "--config", "-c",
        help="JSON config file with parameters"
    )
    parser.add_argument(
        "--plot", "-p",
        action="store_true",
        help="Generate summary plot"
    )
    parser.add_argument(
        "--plot-output",
        help="Save plot to file (PNG, PDF)"
    )
    parser.add_argument(
        "--summary", "-s",
        action="store_true",
        help="Print summary table"
    )
    args = parser.parse_args()

    # Load parameters
    params = load_params(args.config)

    # Run formation evaluation
    log = formation_evaluation(args.input, params)

    # Save results
    if args.output:
        log.to_las(args.output)
        print(f"\nSaved: {args.output}")

    # Generate outputs
    if args.summary or not args.output:
        print_summary_table(log, params)

    if args.plot or args.plot_output:
        plot_path = args.plot_output or (
            str(Path(args.input).with_suffix('.png')) if args.plot_output is None else None
        )
        create_summary_plot(log, params, plot_path if args.plot_output else None)


if __name__ == "__main__":
    main()
