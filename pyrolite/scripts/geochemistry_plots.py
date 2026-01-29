#!/usr/bin/env python3
"""
Generate common geochemistry plots from CSV data.

Usage:
    python geochemistry_plots.py <data.csv> --plot ree
    python geochemistry_plots.py <data.csv> --plot spider
    python geochemistry_plots.py <data.csv> --plot tas
    python geochemistry_plots.py <data.csv> --plot harker
    python geochemistry_plots.py <data.csv> --plot ternary --cols SiO2,CaO,Na2O
    python geochemistry_plots.py <data.csv> --plot all

Options:
    --norm      Normalization reference (default: Chondrite_McDonough1995)
    --output    Output file path (default: display plot)
    --cols      Columns for ternary plot (comma-separated)
    --group     Column name for grouping/coloring samples
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def load_data(filepath: str) -> pd.DataFrame:
    """Load geochemistry data from CSV."""
    df = pd.read_csv(filepath)
    print(f"Loaded {len(df)} samples with columns: {list(df.columns)}")
    return df


def plot_ree(df: pd.DataFrame, norm_name: str = "Chondrite_McDonough1995",
             group_col: str = None) -> plt.Figure:
    """
    Plot REE spider diagram.

    Args:
        df: DataFrame with REE data in ppm
        norm_name: Normalization reference name
        group_col: Column name for grouping samples by color
    """
    from pyrolite.geochem.norm import get_reference_composition

    # REE elements in order
    ree_cols = ['La', 'Ce', 'Pr', 'Nd', 'Sm', 'Eu', 'Gd',
                'Tb', 'Dy', 'Ho', 'Er', 'Tm', 'Yb', 'Lu']

    # Find available REE columns
    available = [col for col in ree_cols if col in df.columns]
    if len(available) < 3:
        print(f"Error: Need at least 3 REE columns. Found: {available}")
        return None

    print(f"Using REE columns: {available}")

    # Get reference and normalize
    ref = get_reference_composition(norm_name)
    df_ree = df[available].copy()
    df_norm = df_ree.pyrochem.normalize_to(ref, units='ppm')

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))

    if group_col and group_col in df.columns:
        groups = df[group_col].unique()
        colors = plt.cm.tab10(np.linspace(0, 1, len(groups)))
        for group, color in zip(groups, colors):
            mask = df[group_col] == group
            df_norm[mask].pyroplot.REE(ax=ax, unity_line=True, color=color,
                                       label=str(group))
        ax.legend(title=group_col)
    else:
        df_norm.pyroplot.REE(ax=ax, unity_line=True)

    ax.set_title(f'REE Pattern (normalized to {norm_name.split("_")[0]})')
    return fig


def plot_spider(df: pd.DataFrame, norm_name: str = "PM_McDonough1995",
                group_col: str = None) -> plt.Figure:
    """
    Plot trace element spider diagram.

    Args:
        df: DataFrame with trace element data in ppm
        norm_name: Normalization reference name
        group_col: Column name for grouping samples by color
    """
    from pyrolite.geochem.norm import get_reference_composition

    # Common trace element order
    trace_cols = ['Cs', 'Rb', 'Ba', 'Th', 'U', 'Nb', 'Ta', 'K', 'La', 'Ce',
                  'Pb', 'Pr', 'Sr', 'Nd', 'Sm', 'Zr', 'Hf', 'Eu', 'Gd',
                  'Tb', 'Dy', 'Ho', 'Y', 'Er', 'Tm', 'Yb', 'Lu']

    # Find available columns
    available = [col for col in trace_cols if col in df.columns]
    if len(available) < 5:
        print(f"Error: Need at least 5 trace element columns. Found: {available}")
        return None

    print(f"Using trace element columns: {available}")

    # Get reference and normalize
    ref = get_reference_composition(norm_name)
    df_trace = df[available].copy()
    df_norm = df_trace.pyrochem.normalize_to(ref, units='ppm')

    # Create plot
    fig, ax = plt.subplots(figsize=(12, 6))

    if group_col and group_col in df.columns:
        groups = df[group_col].unique()
        colors = plt.cm.tab10(np.linspace(0, 1, len(groups)))
        for group, color in zip(groups, colors):
            mask = df[group_col] == group
            df_norm[mask].pyroplot.spider(ax=ax, unity_line=True, color=color,
                                          label=str(group))
        ax.legend(title=group_col)
    else:
        df_norm.pyroplot.spider(ax=ax, unity_line=True)

    ax.set_title(f'Spider Diagram (normalized to {norm_name.split("_")[0]})')
    return fig


def plot_tas(df: pd.DataFrame, group_col: str = None) -> plt.Figure:
    """
    Plot TAS (Total Alkali-Silica) classification diagram.

    Args:
        df: DataFrame with SiO2, Na2O, K2O columns
        group_col: Column name for grouping samples by color
    """
    from pyrolite.plot.templates import TAS

    required = ['SiO2', 'Na2O', 'K2O']
    missing = [col for col in required if col not in df.columns]
    if missing:
        print(f"Error: Missing required columns: {missing}")
        return None

    # Calculate total alkalis
    df_plot = df.copy()
    df_plot['Na2O_K2O'] = df_plot['Na2O'] + df_plot['K2O']

    # Create TAS diagram
    fig, ax = plt.subplots(figsize=(10, 8))
    ax = TAS(ax=ax)

    if group_col and group_col in df.columns:
        groups = df[group_col].unique()
        colors = plt.cm.tab10(np.linspace(0, 1, len(groups)))
        for group, color in zip(groups, colors):
            mask = df_plot[group_col] == group
            ax.scatter(df_plot.loc[mask, 'SiO2'], df_plot.loc[mask, 'Na2O_K2O'],
                      c=[color], s=50, label=str(group), alpha=0.7, edgecolors='k')
        ax.legend(title=group_col)
    else:
        ax.scatter(df_plot['SiO2'], df_plot['Na2O_K2O'], c='red', s=50,
                   alpha=0.7, edgecolors='k')

    ax.set_title('Total Alkali-Silica (TAS) Diagram')
    return fig


def plot_harker(df: pd.DataFrame, group_col: str = None) -> plt.Figure:
    """
    Plot Harker variation diagrams.

    Args:
        df: DataFrame with major oxide columns
        group_col: Column name for grouping samples by color
    """
    if 'SiO2' not in df.columns:
        print("Error: SiO2 column required for Harker diagrams")
        return None

    # Elements to plot against SiO2
    elements = ['TiO2', 'Al2O3', 'FeO', 'Fe2O3', 'MgO', 'CaO', 'Na2O', 'K2O', 'P2O5']
    available = [col for col in elements if col in df.columns]

    if len(available) == 0:
        print("Error: No major oxide columns found for Harker diagrams")
        return None

    # Calculate grid size
    n_plots = len(available)
    n_cols = min(3, n_plots)
    n_rows = (n_plots + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(4*n_cols, 3.5*n_rows))
    if n_plots == 1:
        axes = [axes]
    else:
        axes = axes.flatten()

    for i, elem in enumerate(available):
        ax = axes[i]

        if group_col and group_col in df.columns:
            groups = df[group_col].unique()
            colors = plt.cm.tab10(np.linspace(0, 1, len(groups)))
            for group, color in zip(groups, colors):
                mask = df[group_col] == group
                ax.scatter(df.loc[mask, 'SiO2'], df.loc[mask, elem],
                          c=[color], s=30, label=str(group), alpha=0.7)
            if i == 0:
                ax.legend(title=group_col, fontsize=8)
        else:
            ax.scatter(df['SiO2'], df[elem], c='blue', s=30, alpha=0.7)

        ax.set_xlabel('SiO2 (wt%)')
        ax.set_ylabel(f'{elem} (wt%)')

    # Hide empty subplots
    for j in range(len(available), len(axes)):
        axes[j].set_visible(False)

    plt.suptitle('Harker Variation Diagrams', fontsize=14)
    plt.tight_layout()
    return fig


def plot_ternary(df: pd.DataFrame, cols: list, group_col: str = None) -> plt.Figure:
    """
    Plot ternary diagram.

    Args:
        df: DataFrame with compositional data
        cols: List of 3 column names for ternary axes
        group_col: Column name for grouping samples by color
    """
    if len(cols) != 3:
        print("Error: Exactly 3 columns required for ternary plot")
        return None

    missing = [col for col in cols if col not in df.columns]
    if missing:
        print(f"Error: Missing columns: {missing}")
        return None

    # Create plot
    fig, ax = plt.subplots(figsize=(8, 8))

    if group_col and group_col in df.columns:
        groups = df[group_col].unique()
        colors = plt.cm.tab10(np.linspace(0, 1, len(groups)))
        for group, color in zip(groups, colors):
            mask = df[group_col] == group
            df.loc[mask, cols].pyroplot.scatter(ax=ax, c=[color], s=50,
                                                 label=str(group), alpha=0.7)
        ax.legend(title=group_col)
    else:
        df[cols].pyroplot.scatter(ax=ax, c='red', s=50, alpha=0.7)

    ax.set_title(f'{cols[0]}-{cols[1]}-{cols[2]} Ternary')
    return fig


def main():
    parser = argparse.ArgumentParser(description="Generate geochemistry plots")
    parser.add_argument("data", help="Path to CSV file with geochemistry data")
    parser.add_argument("--plot", choices=['ree', 'spider', 'tas', 'harker',
                                           'ternary', 'all'],
                        default='all', help="Plot type to generate")
    parser.add_argument("--norm", default=None,
                        help="Normalization reference name")
    parser.add_argument("--output", help="Output file path (optional)")
    parser.add_argument("--cols", help="Comma-separated columns for ternary plot")
    parser.add_argument("--group", help="Column name for grouping/coloring")
    parser.add_argument("--dpi", type=int, default=150, help="Output DPI")

    args = parser.parse_args()

    # Load data
    if not Path(args.data).exists():
        print(f"Error: File not found: {args.data}")
        sys.exit(1)

    df = load_data(args.data)

    # Import pyrolite after loading data to enable accessors
    import pyrolite  # noqa: F401

    plots = []

    if args.plot in ['ree', 'all']:
        norm = args.norm or 'Chondrite_McDonough1995'
        fig = plot_ree(df, norm_name=norm, group_col=args.group)
        if fig:
            plots.append(('ree', fig))

    if args.plot in ['spider', 'all']:
        norm = args.norm or 'PM_McDonough1995'
        fig = plot_spider(df, norm_name=norm, group_col=args.group)
        if fig:
            plots.append(('spider', fig))

    if args.plot in ['tas', 'all']:
        fig = plot_tas(df, group_col=args.group)
        if fig:
            plots.append(('tas', fig))

    if args.plot in ['harker', 'all']:
        fig = plot_harker(df, group_col=args.group)
        if fig:
            plots.append(('harker', fig))

    if args.plot == 'ternary':
        if not args.cols:
            print("Error: --cols required for ternary plot (e.g., --cols SiO2,CaO,Na2O)")
            sys.exit(1)
        cols = [c.strip() for c in args.cols.split(',')]
        fig = plot_ternary(df, cols, group_col=args.group)
        if fig:
            plots.append(('ternary', fig))

    # Save or display
    if args.output:
        for name, fig in plots:
            if len(plots) > 1:
                output_path = Path(args.output)
                out_file = output_path.parent / f"{output_path.stem}_{name}{output_path.suffix}"
            else:
                out_file = args.output
            fig.savefig(out_file, dpi=args.dpi, bbox_inches='tight')
            print(f"Saved: {out_file}")
    else:
        plt.show()

    print(f"\nGenerated {len(plots)} plot(s)")


if __name__ == "__main__":
    main()
