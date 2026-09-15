#!/usr/bin/env python3
"""Fit an explicitly bounded Pastas 2.0 calibration using already normalized data."""
import argparse
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pastas as ps


def load_series(filepath):
    table = pd.read_csv(filepath, index_col=0, parse_dates=True)
    if table.shape[1] != 1:
        raise ValueError('CSV requires one date column and one numeric value column')
    series = pd.to_numeric(table.iloc[:, 0], errors='raise').astype(float)
    if not isinstance(series.index, pd.DatetimeIndex) or series.index.tz is not None:
        raise ValueError('Resolve timestamps to a documented naive daily index before this helper')
    if series.index.hasnans or series.index.has_duplicates or not series.index.is_monotonic_increasing:
        raise ValueError('Timestamps must be valid, unique and increasing')
    if not series.index.equals(series.index.normalize()) or np.isinf(series).any():
        raise ValueError('Require daily date labels and no infinite values')
    return series


def create_model(head, precip, evap, pumping=None, name='groundwater_model', *,
                 calibration_start, calibration_end, warmup_days=730):
    """Inputs are m head, mm/day rain/evap, positive m3/day abstraction.

    Only calibration head/stresses are included, including data-derived initial
    values. Missing head is excluded; missing/irregular stress must be handled
    explicitly before calling this helper.
    """
    start, end = pd.Timestamp(calibration_start), pd.Timestamp(calibration_end)
    if start >= end or not isinstance(warmup_days, int) or warmup_days <= 0:
        raise ValueError('Specify increasing calibration dates and a positive integer warmup')
    dates = pd.date_range(start - pd.Timedelta(days=warmup_days), end, freq='D')
    train = head.loc[start:end].dropna()
    if len(train) < 3 or not np.isfinite(train).all():
        raise ValueError('Insufficient finite calibration head observations')
    checked = []
    for series in (precip, evap) + (() if pumping is None else (pumping,)):
        if series.index.has_duplicates or not series.index.is_monotonic_increasing:
            raise ValueError('Stress dates must be unique and increasing')
        subset = series.reindex(dates)
        if not np.isfinite(subset).all() or (subset < 0).any():
            raise ValueError('Stresses must be nonnegative and complete through observed warmup/calibration')
        checked.append(subset.copy())
    settings = {'freq': 'D', 'sample_up': 'bfill', 'sample_down': 'mean',
                'fill_nan': None, 'fill_before': None, 'fill_after': None}
    model = ps.Model(train.copy(), name=name)
    ps.RechargeModel(model, checked[0], checked[1], rfunc=ps.Gamma(),
                     recharge=ps.rch.Linear(), name='recharge', settings=(settings.copy(), settings.copy()))
    if pumping is not None:
        ps.StressModel(model, checked[2], rfunc=ps.Hantush(), name='pumping', up=False, settings=settings.copy())
    model.set_settings(tmin=start, tmax=end, warmup=warmup_days)
    return model


def solve_and_report(model, noise=False):
    if noise and model.noisemodel is None:
        ps.ArNoiseModel(model)
    elif not noise and model.noisemodel is not None:
        raise ValueError('Model already has a noise model; choose the objective explicitly')
    model.solve(report=False)
    if not model.solver.result.success:
        raise RuntimeError('Pastas optimizer did not converge')
    return {'evp': float(model.stats.evp()), 'rmse_m': float(model.stats.rmse()),
            'aic': float(model.stats.aic()), 'bic': float(model.stats.bic())}


def plot_results(model, output_path):
    """Plot only when requested; contribution API returns a list of Series."""
    figure, axes = plt.subplots(2, 1, figsize=(10, 6))
    model.plot(ax=axes[0])
    for contribution in model.get_contributions():
        axes[1].plot(contribution.index, contribution.values, label=contribution.name)
    axes[0].set_ylabel('Relative head (m)')
    axes[1].set_ylabel('Contribution (m)')
    axes[1].legend()
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('head', help='Daily-date head CSV in m, with documented vertical reference')
    parser.add_argument('precip', help='Precipitation CSV in mm/day')
    parser.add_argument('evap', help='Reference evaporation CSV in mm/day')
    parser.add_argument('--pumping', help='Positive abstraction in m3/day')
    parser.add_argument('--calibration-start', required=True)
    parser.add_argument('--calibration-end', required=True)
    parser.add_argument('--warmup-days', type=int, default=730)
    parser.add_argument('--name', default='model')
    parser.add_argument('--output', required=True, help='New .pas model file')
    parser.add_argument('--plot', help='Optional new diagnostic plot file')
    parser.add_argument('--noise', action='store_true')
    args = parser.parse_args()
    try:
        sources = [Path(p).resolve() for p in [args.head, args.precip, args.evap] + ([args.pumping] if args.pumping else [])]
        for output in [args.output] + ([args.plot] if args.plot else []):
            path = Path(output)
            if path.exists() or path.resolve() in sources:
                raise ValueError('Choose new output paths; input and existing output files are preserved')
        if Path(args.output).suffix != '.pas':
            raise ValueError('Model output must use the .pas format')
        model = create_model(load_series(args.head), load_series(args.precip), load_series(args.evap),
                              load_series(args.pumping) if args.pumping else None, args.name,
                              calibration_start=args.calibration_start, calibration_end=args.calibration_end,
                              warmup_days=args.warmup_days)
        stats = solve_and_report(model, noise=args.noise)
        model.to_file(args.output)
        if args.plot:
            plot_results(model, args.plot)
        print(stats)
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
