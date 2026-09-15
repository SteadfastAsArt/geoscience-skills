#!/usr/bin/env python3
"""Validate a fixed groundwater hindcast design using Pastas 2.0 and local data."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pastas as ps


DATE_KEYS = ('calibration_start', 'calibration_end', 'holdout_start', 'holdout_end')


def read_series(path):
    table = pd.read_csv(path)
    if table.shape[1] != 2:
        raise ValueError(f'{path}: require exactly one date and one value column')
    dates = pd.DatetimeIndex(pd.to_datetime(table.iloc[:, 0], errors='raise'))
    if dates.hasnans or dates.tz is not None or not dates.equals(dates.normalize()):
        raise ValueError('This daily workflow requires naive date labels; resolve timezone/subdaily semantics explicitly')
    if dates.has_duplicates or not dates.is_monotonic_increasing:
        raise ValueError('Dates must be unique and increasing; do not silently average duplicate observations')
    values = pd.to_numeric(table.iloc[:, 1], errors='raise').to_numpy(dtype=float)
    if np.isinf(values).any() or not np.isfinite(values).any():
        raise ValueError('Series contains infinite values or no finite observations')
    return pd.Series(values, index=dates, name=str(table.columns[1]))


def validate_design(design):
    dates = [pd.Timestamp(design[key]) for key in DATE_KEYS]
    if any(d.tz is not None or d != d.normalize() for d in dates):
        raise ValueError('Design windows must be timezone-naive daily dates')
    start, end, val_start, val_end = dates
    if not start < end < val_start <= val_end or val_start != end + pd.Timedelta(days=1):
        raise ValueError('Require disjoint chronological calibration and contiguous holdout windows')
    warmup = design['warmup_days']
    if not isinstance(warmup, int) or warmup <= 0:
        raise ValueError('warmup_days must be a positive integer')
    if design['head_input_unit'] not in ('ft', 'm') or design['stress_input_unit'] not in ('ft/day', 'mm/day'):
        raise ValueError('Supported explicit input units: ft/m head and ft/day or mm/day stresses')
    if not 0 <= design.get('gap_fill_limit_fraction', .01) <= .01:
        raise ValueError('This bounded example permits at most 1% explicitly imputed stress samples')
    return dates


def prepare_inputs(head, precipitation, evaporation, design):
    start, end, val_start, val_end = validate_design(design)
    sim_start = start - pd.Timedelta(days=design['warmup_days'])
    dates = pd.date_range(sim_start, val_end, freq='D')
    factor_head = .3048 if design['head_input_unit'] == 'ft' else 1.
    factor_stress = 304.8 if design['stress_input_unit'] == 'ft/day' else 1.
    heads = head * factor_head
    head_dates = pd.date_range(head.index.min(), head.index.max(), freq='D')
    heads_qc = pd.DataFrame({'source_value': head.reindex(head_dates), 'head_m': heads.reindex(head_dates)})
    heads_qc['observed'] = heads_qc.head_m.notna()
    heads_qc['partition'] = 'outside'
    heads_qc.loc[start:end, 'partition'] = 'calibration'
    heads_qc.loc[val_start:val_end, 'partition'] = 'holdout'
    train = heads.loc[start:end].dropna()
    validation = heads.loc[val_start:val_end].dropna()
    if len(train) < 365 or len(validation) < 30 or not train.index.intersection(validation.index).empty:
        raise ValueError('Need at least 365 calibration and 30 separate holdout observations')
    stresses, qc, imputation = {}, pd.DataFrame(index=dates), {}
    for name, raw in [('precipitation', precipitation), ('evaporation', evaporation)]:
        if raw.index.min() > sim_start or raw.index.max() < val_end:
            raise ValueError(f'{name}: observations must cover warmup through holdout; no implicit extension')
        scaled = raw * factor_stress
        if (scaled.dropna() < 0).any():
            raise ValueError(f'{name}: negative daily precipitation/reference evaporation requires documented correction')
        reference = scaled.loc[start:end].dropna()
        monthly = reference.groupby(reference.index.month).mean()
        if len(monthly) != 12:
            raise ValueError(f'{name}: calibration data must cover all twelve months')
        original = scaled.reindex(dates)
        mask = original.isna()
        if mask.mean() > design.get('gap_fill_limit_fraction', .01):
            raise ValueError(f'{name}: too many missing stresses for the declared imputation policy')
        filled = original.fillna(pd.Series(dates.month.map(monthly), index=dates)).rename(name)
        if not np.isfinite(filled).all():
            raise ValueError(f'{name}: missing stresses remain after explicit monthly imputation')
        qc[name + '_observed_mm_day'] = original
        qc[name + '_imputed'] = mask
        qc[name + '_used_mm_day'] = filled
        imputation[name] = {'count': int(mask.sum()), 'dates': [d.strftime('%Y-%m-%d') for d in dates[mask]],
                            'training_monthly_means_mm_day': {str(m): float(v) for m, v in monthly.items()}}
        stresses[name] = filled
    return train, validation, heads_qc, stresses, qc, imputation


def fit_calibration(train, stresses, design):
    start, end = design['calibration_start'], design['calibration_end']
    model = ps.Model(train.copy(), name=design.get('model_name', 'groundwater'),
                     metadata={'unit': 'm', 'vertical_reference': design['vertical_reference'],
                               'time_reference': design['timestamp_convention']})
    settings = {'freq': 'D', 'sample_up': 'bfill', 'sample_down': 'mean',
                'fill_nan': None, 'fill_before': None, 'fill_after': None}
    # Fit with calibration stresses only: even data-derived initial guesses
    # and defaults must not depend on holdout stresses or head observations.
    ps.RechargeModel(model, stresses['precipitation'].loc[:end].copy(),
                     stresses['evaporation'].loc[:end].copy(),
                     rfunc=ps.Gamma(cutoff=design['response_cutoff']), recharge=ps.rch.Linear(),
                     name='recharge', settings=(settings.copy(), settings.copy()))
    ps.ArNoiseModel(model)
    ps.solver.LeastSquares(model, max_nfev=design.get('max_nfev', 300))
    model.solve(tmin=start, tmax=end, warmup=design['warmup_days'], report=False)
    if not model.solver.result.success or not np.isfinite(model.parameters.optimal).all():
        raise RuntimeError('Pastas calibration did not converge to finite parameters')
    tail = float(model.get_response_tmax('recharge'))
    if not np.isfinite(tail) or tail > design['warmup_days']:
        raise ValueError('Fitted response extends beyond declared observed warmup; revise the design using calibration only')
    return model


def metrics(observed, predicted):
    aligned = predicted.reindex(observed.index)
    if not np.isfinite(aligned).all():
        raise ValueError('Predictions do not cover every scored observed date')
    residual = observed.to_numpy() - aligned.to_numpy()
    denominator = np.sum((observed.to_numpy() - observed.mean()) ** 2)
    return {'n': len(observed), 'rmse_m': float(np.sqrt(np.mean(residual ** 2))),
            'mae_m': float(np.mean(np.abs(residual))), 'bias_observed_minus_simulated_m': float(np.mean(residual)),
            'nse': None if denominator == 0 else float(1 - np.sum(residual ** 2) / denominator)}


def evaluate_case(head, precipitation, evaporation, design):
    train, validation, heads_qc, stresses, stress_qc, imputation = prepare_inputs(head, precipitation, evaporation, design)
    model = fit_calibration(train, stresses, design)
    parameters_before = model.parameters.optimal.copy()
    end = design['calibration_end']
    calibration_simulation = model.simulate(tmin=design['calibration_start'], tmax=end)
    calibration_residual = train - calibration_simulation.reindex(train.index)
    calibration_noise = model.noise()
    # Carry the fitted response into a continuous hindcast using observed
    # future meteorology. No holdout head or residual updates the model state.
    recharge = model.stressmodels['recharge']
    recharge.set_stress(prec=stresses['precipitation'].copy())
    recharge.set_stress(evap=stresses['evaporation'].copy())
    simulation = model.simulate(tmin=design['calibration_start'], tmax=design['holdout_end'])
    if not np.array_equal(parameters_before.to_numpy(), model.parameters.optimal.to_numpy()):
        raise RuntimeError('Supplying future stresses changed the fitted parameters')
    np.testing.assert_allclose(simulation.loc[:end], calibration_simulation, atol=1e-10, rtol=0)
    monthly_head = train.groupby(train.index.month).mean()
    if len(monthly_head) != 12:
        raise ValueError('Head baseline requires calibration observations in all months')
    table = pd.DataFrame({'head_m': (head * (.3048 if design['head_input_unit'] == 'ft' else 1.)).reindex(simulation.index),
                          'simulated_m': simulation, 'calibration_mean_m': train.mean(),
                          'calibration_monthly_mean_m': simulation.index.month.map(monthly_head),
                          'last_calibration_head_fixed_m': train.iloc[-1]})
    table['partition'] = np.where(table.index <= pd.Timestamp(end), 'calibration', 'holdout')
    table['residual_m'] = table.head_m - table.simulated_m
    table['scored'] = table.head_m.notna()
    report = {}
    columns = ['simulated_m', 'calibration_mean_m', 'calibration_monthly_mean_m', 'last_calibration_head_fixed_m']
    for partition, observed in [('calibration', train), ('holdout', validation)]:
        report[partition] = {name: metrics(observed, table[name]) for name in columns}
    acf_frames = []
    for name, values in [('calibration_residual', calibration_residual), ('calibration_noise', calibration_noise),
                         ('holdout_residual', validation - simulation.reindex(validation.index))]:
        acf = ps.stats.acf(values, lags=[1, 7, 30, 90], bin_method='gaussian',
                          bin_width=.5, min_obs=30, full_output=True)
        if acf.empty or not np.isfinite(acf[['acf', 'conf', 'n']].to_numpy()).all():
            raise RuntimeError('Residual diagnostics returned incomplete values')
        acf.insert(0, 'lag_days', acf.index / pd.Timedelta(days=1))
        acf.insert(0, 'series', name)
        acf_frames.append(acf.reset_index(drop=True))
    diagnostics = pd.concat(acf_frames, ignore_index=True)
    contribution = model.get_contribution('recharge', tmin=design['calibration_start'], tmax=design['holdout_end'])
    np.testing.assert_allclose(contribution + model.parameters.loc['constant_d', 'optimal'], simulation, atol=1e-10, rtol=0)
    report.update({'design': design, 'imputation': imputation,
                   'response_tmax_days': float(model.get_response_tmax('recharge')),
                   'solver_success': bool(model.solver.result.success), 'solver_nfev': int(model.solver.result.nfev),
                   'calibration_observations_stored': len(model.oseries.series),
                   'interpretation': 'Hindcast conditional on observed future meteorology; no holdout-head assimilation',
                   'uncertainty_limit': 'AR innovations retain autocorrelation; parameter stderr is conditional and not a calibrated forecast interval',
                   'software': {package: importlib.metadata.version(package) for package in
                                ('pastas', 'numpy', 'pandas', 'scipy', 'numba', 'tqdm')}})
    return {'model': model, 'report': report, 'simulation': table, 'head_qc': heads_qc,
            'stress_qc': stress_qc, 'diagnostics': diagnostics, 'contribution': contribution}


def run_case(data_dir, output_dir):
    data_dir, output_dir = Path(data_dir), Path(output_dir)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ValueError('Choose a new or empty output directory; existing results are not overwritten')
    provenance = json.loads((data_dir / 'provenance.json').read_text())
    for filename, source in provenance['files'].items():
        actual = hashlib.sha256((data_dir / filename).read_bytes()).hexdigest()
        if actual != source['sha256']:
            raise ValueError(f'Fixture checksum mismatch: {filename}')
    design_path = data_dir / 'design.json'
    design = json.loads(design_path.read_text())
    files = design['data_files']
    result = evaluate_case(read_series(data_dir / files['head']), read_series(data_dir / files['precipitation']),
                           read_series(data_dir / files['evaporation']), design)
    result['report']['provenance'] = provenance
    result['report']['design_sha256'] = hashlib.sha256(design_path.read_bytes()).hexdigest()
    output_dir.mkdir(parents=True, exist_ok=True)
    result['model'].to_file(output_dir / 'model.pas')
    loaded = ps.io.load(output_dir / 'model.pas')
    restored = loaded.simulate(tmin=design['calibration_start'], tmax=design['holdout_end'])
    delta = float(np.max(np.abs(restored.to_numpy() - result['simulation'].simulated_m.to_numpy())))
    if delta > 1e-8:
        raise RuntimeError('Saved model does not reproduce the continuous hindcast')
    result['report']['save_load_max_difference_m'] = delta
    for key in ('simulation', 'head_qc', 'stress_qc', 'diagnostics'):
        result[key].to_csv(output_dir / f'{key}.csv', index=(key != 'diagnostics'), float_format='%.17g')
    result['model'].parameters.to_csv(output_dir / 'parameters.csv', float_format='%.17g')
    result['contribution'].to_csv(output_dir / 'recharge_contribution.csv', float_format='%.17g')
    (output_dir / 'report.json').write_text(json.dumps(result['report'], indent=2, allow_nan=False) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', required=True, help='Directory containing the provenance, fixed design, and raw CSVs')
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    try:
        result = run_case(args.data_dir, args.output_dir)
        print(json.dumps(result['report']['holdout'], indent=2))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
