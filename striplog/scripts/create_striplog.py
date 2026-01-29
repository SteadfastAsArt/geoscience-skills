#!/usr/bin/env python3
"""
Create striplog from CSV file or text description.

Usage:
    python create_striplog.py --csv lithology.csv --output well_log.png
    python create_striplog.py --text "0-10: sandstone, 10-20: shale" --output well_log.png
    python create_striplog.py --csv lithology.csv --export output.json
"""

import argparse
import sys
from pathlib import Path

from striplog import Striplog, Interval, Component, Lexicon, Legend, Decor


# Default lexicon for common lithologies
DEFAULT_LEXICON = {
    'lithology': {
        'sandstone': {
            'synonyms': ['sand', 'ss', 'sst', 'sandst', 'arenite'],
            'colour': '#FFFF00',
            'hatch': '...'
        },
        'shale': {
            'synonyms': ['sh', 'clay', 'mudstone', 'claystone', 'argillite'],
            'colour': '#808080',
            'hatch': '---'
        },
        'limestone': {
            'synonyms': ['ls', 'lime', 'calcaire', 'carbonate'],
            'colour': '#00BFFF',
            'hatch': '+++'
        },
        'dolomite': {
            'synonyms': ['dol', 'dolostone'],
            'colour': '#00FFFF',
            'hatch': 'xxx'
        },
        'siltstone': {
            'synonyms': ['silt', 'slst', 'sltst'],
            'colour': '#D2B48C',
            'hatch': '...'
        },
        'conglomerate': {
            'synonyms': ['cgl', 'congl', 'gravel'],
            'colour': '#FFA500',
            'hatch': 'ooo'
        },
        'coal': {
            'synonyms': ['c', 'lignite'],
            'colour': '#000000',
            'hatch': ''
        },
    }
}


def create_legend() -> Legend:
    """Create default legend for common lithologies."""
    decors = []
    for lith, props in DEFAULT_LEXICON['lithology'].items():
        decors.append(Decor({
            'component': lith,
            'colour': props['colour'],
            'hatch': props['hatch'],
            'width': 3
        }))
    return Legend(decors)


def create_from_csv(filepath: str) -> Striplog:
    """
    Create striplog from CSV file.

    Expected CSV format:
        top,base,lithology
        0,10,sandstone
        10,25,shale
        ...

    Additional columns are added as component properties.
    """
    import pandas as pd

    df = pd.read_csv(filepath)

    # Validate required columns
    required = ['top', 'base', 'lithology']
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Build intervals
    intervals = []
    extra_cols = [c for c in df.columns if c not in ['top', 'base']]

    for _, row in df.iterrows():
        props = {col: row[col] for col in extra_cols}
        comp = Component(props)
        interval = Interval(top=row['top'], base=row['base'], components=[comp])
        intervals.append(interval)

    return Striplog(intervals)


def create_from_text(text: str) -> Striplog:
    """
    Create striplog from text description.

    Supports formats like:
        0-10: sandstone
        0.0 - 5.5 m: fine sandstone
    """
    lexicon = Lexicon(DEFAULT_LEXICON)
    return Striplog.from_description(text, lexicon=lexicon)


def print_summary(strip: Striplog) -> None:
    """Print striplog summary."""
    print(f"\nStriplog Summary")
    print(f"{'='*40}")
    print(f"Depth range: {strip.start:.1f} - {strip.stop:.1f}")
    print(f"Total intervals: {len(strip)}")
    print(f"Unique lithologies: {strip.unique('lithology')}")
    print()

    # Statistics by lithology
    print("Thickness by lithology:")
    for lith in strip.unique('lithology'):
        ntg = strip.net_to_gross(pattern={'lithology': lith})
        thickness = ntg * (strip.stop - strip.start)
        print(f"  {lith}: {thickness:.1f} ({ntg*100:.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description="Create striplog from CSV or text description"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--csv', help='Path to CSV file')
    group.add_argument('--text', help='Text description of lithology')

    parser.add_argument('--output', '-o', help='Output image file (PNG)')
    parser.add_argument('--export', '-e', help='Export to file (CSV, JSON, or LAS)')
    parser.add_argument('--no-legend', action='store_true', help='Plot without legend')
    parser.add_argument('--title', help='Plot title')

    args = parser.parse_args()

    # Create striplog
    try:
        if args.csv:
            strip = create_from_csv(args.csv)
            print(f"Loaded {len(strip)} intervals from {args.csv}")
        else:
            strip = create_from_text(args.text)
            print(f"Parsed {len(strip)} intervals from text")
    except Exception as e:
        print(f"Error creating striplog: {e}")
        sys.exit(1)

    # Print summary
    print_summary(strip)

    # Export if requested
    if args.export:
        export_path = Path(args.export)
        suffix = export_path.suffix.lower()

        if suffix == '.csv':
            strip.to_csv(str(export_path))
        elif suffix == '.json':
            strip.to_json(str(export_path))
        elif suffix == '.las':
            strip.to_las(str(export_path))
        else:
            print(f"Unknown export format: {suffix}")
            sys.exit(1)

        print(f"Exported to {export_path}")

    # Plot if output requested
    if args.output:
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(3, 10))

        legend = None if args.no_legend else create_legend()
        strip.plot(ax=ax, legend=legend)

        if args.title:
            ax.set_title(args.title)

        plt.tight_layout()
        plt.savefig(args.output, dpi=150, bbox_inches='tight')
        print(f"Saved plot to {args.output}")


if __name__ == "__main__":
    main()
