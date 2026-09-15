#!/usr/bin/env python3
"""Observed quadrupoles→two-layer pyGIMLi fit→auditable CSV/JSON artifacts.

This is a flat, isotropic, horizontally layered diagnostic, not a 2D/3D ERT
image. Local nominal electrode x coordinates are explicitly supplied in metres.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pygimli as pg
from pygimli.physics.ves import VESModelling
from scipy.optimize import least_squares
from scipy.stats import chi2


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def load_inputs(observations_path, electrodes_path):
    observations = pd.read_csv(observations_path, float_precision='round_trip')
    electrodes = pd.read_csv(electrodes_path, float_precision='round_trip')
    required = ['measurement_id', 'a', 'b', 'm', 'n', 'rhoa_ohm_m', 'repeatability_pct']
    if not set(required).issubset(observations) or not {'electrode_id', 'x_m'}.issubset(electrodes):
        raise ValueError('Missing standard observation/electrode columns')
    if observations.empty or electrodes.empty or observations[required].isna().any().any():
        raise ValueError('Missing measurements must not be imputed')
    for frame, columns in ((observations, required[1:]), (electrodes, ['electrode_id', 'x_m'])):
        for column in columns:
            frame[column] = pd.to_numeric(frame[column], errors='raise')
        if not np.isfinite(frame[columns].to_numpy(dtype=float)).all():
            raise ValueError('Numeric inputs must be finite')
    for values in (observations[['a', 'b', 'm', 'n']].to_numpy(), electrodes.electrode_id.to_numpy()):
        if not np.equal(values, np.floor(values)).all():
            raise ValueError('Electrode IDs must be integers')
    if (not observations.measurement_id.is_unique or not electrodes.electrode_id.is_unique
            or not electrodes.x_m.is_unique or (observations.repeatability_pct < 0).any()):
        raise ValueError('Unique observation/electrode identities, positions and nonnegative errors are required')
    positions = dict(zip(electrodes.electrode_id, electrodes.x_m))
    try:
        points = np.array([[positions[value] for value in row]
                           for row in observations[['a', 'b', 'm', 'n']].to_numpy()])
    except KeyError as error:
        raise ValueError('Observation references an absent electrode') from error
    if any(len(set(row)) != 4 for row in points):
        raise ValueError('Each quadrupole needs four distinct electrodes')
    a, b, m, n = points.T
    distances = np.stack((abs(a - m), abs(a - n), abs(b - m), abs(b - n)))
    return observations, electrodes, distances


def forward_operator(distances):
    am, an, bm, bn = distances
    return VESModelling(am=am, an=an, bm=bm, bn=bn, nLayers=2)


def fit(distances, observed, sigma, start):
    if len(observed) <= 3 or np.any(observed <= 0):
        raise ValueError('Need more than three positive observations for the three-parameter log fit')
    inversion = pg.Inversion(fop=forward_operator(distances), verbose=False)
    inversion.dataTrans = pg.trans.TransLog()
    inversion.modelTrans = pg.trans.TransLog()
    model = np.asarray(inversion.run(observed, errorVals=sigma, startModel=list(start),
                                     lam=0, maxIter=20, verbose=False))
    predicted = np.asarray(inversion.response)
    if not np.isfinite(model).all() or not np.isfinite(predicted).all() or min(*model, *predicted) <= 0:
        raise ValueError('Inversion returned invalid model or prediction')
    return model, predicted


def geometry_groups(observations):
    result = []
    for a, b, m, n in observations[['a', 'b', 'm', 'n']].to_numpy(dtype=int):
        pairs = sorted((tuple(sorted((a, b))), tuple(sorted((m, n)))))
        result.append('|'.join(str(int(value)) for pair in pairs for value in pair))
    return np.asarray(result)


def run_workflow(observations_path, electrodes_path, output_dir, *, geometry_note,
                 extra_log_sigma=0.03, start=(5.0, 150.0, 50.0)):
    output = Path(output_dir)
    if output.exists():
        raise ValueError('Use a new output directory; previous results must not be overwritten')
    if not geometry_note.strip():
        raise ValueError('Describe nominal geometry, survey/CRS provenance and flat-earth limitations')
    if not np.isfinite(extra_log_sigma) or extra_log_sigma <= 0:
        raise ValueError('A positive finite additional log-error term must be declared')
    start = np.asarray(start, dtype=float)
    if start.shape != (3,) or not np.isfinite(start).all() or np.any(start <= 0):
        raise ValueError('Start model requires positive thickness, top and bottom resistivity')
    observations, electrodes, distances = load_inputs(observations_path, electrodes_path)
    retained = observations.rhoa_ohm_m.to_numpy() > 0
    if retained.sum() <= 6:
        raise ValueError('Too few positive observations for fit and holdout')
    values = observations.rhoa_ohm_m.to_numpy()[retained]
    sigma = np.hypot(observations.repeatability_pct.to_numpy()[retained] / 100., extra_log_sigma)
    geometry = distances[:, retained]
    model, predicted = fit(geometry, values, sigma, start)
    groups = geometry_groups(observations.loc[retained])
    held_out = np.array([sha256(group.encode('ascii')).digest()[0] % 5 == 0 for group in groups])
    if held_out.sum() == 0 or (~held_out).sum() <= 3:
        raise ValueError('Fixed reciprocal-group holdout has insufficient training/test measurements')
    train_model, _ = fit(geometry[:, ~held_out], values[~held_out], sigma[~held_out], start)
    prediction_holdout = np.asarray(forward_operator(geometry[:, held_out]).response(train_model))
    residual = (np.log(predicted) - np.log(values)) / sigma
    statistic, dof = float(residual @ residual), len(values) - 3
    # Independent local optimizer confirms rank and checks early stopping. It is
    # not a global-optimum/uniqueness proof or an additional geological inversion.
    forward = forward_operator(geometry)
    def objective(log_model):
        return (np.log(np.asarray(forward.response(np.exp(log_model)))) - np.log(values)) / sigma
    refined = least_squares(objective, np.log(model), max_nfev=100)
    refined_q = float(refined.fun @ refined.fun)
    rank = int(np.linalg.matrix_rank(refined.jac))
    local_converged = bool(refined.success and rank == 3
                           and abs(refined_q / max(statistic, np.finfo(float).eps) - 1) < 0.001)
    baseline = float(np.average(np.log(values[~held_out]), weights=sigma[~held_out] ** -2))
    result = observations.copy()
    result['included'] = retained
    result['exclusion_reason'] = np.where(retained, '', 'nonpositive apparent resistivity; excluded from log fit only')
    result['group'] = geometry_groups(observations)
    result['holdout'] = False
    for column in ('log_sigma', 'predicted_all_fit_ohm_m', 'normalized_log_residual', 'predicted_holdout_ohm_m'):
        result[column] = np.nan
    result.loc[retained, 'log_sigma'] = sigma
    result.loc[retained, 'predicted_all_fit_ohm_m'] = predicted
    result.loc[retained, 'normalized_log_residual'] = residual
    test_rows = np.flatnonzero(retained)[held_out]
    result.loc[test_rows, 'holdout'] = True
    result.loc[test_rows, 'predicted_holdout_ohm_m'] = prediction_holdout
    report = {'schema_version': 1, 'library': 'pyGIMLi', 'version': pg.__version__,
              'inputs': {'observations_sha256': digest(observations_path), 'electrodes_sha256': digest(electrodes_path)},
              'geometry_note': geometry_note, 'model_assumption': 'Flat isotropic two-layer earth with point surface electrodes',
              'units': {'thickness': 'm', 'resistivity': 'ohm m', 'positions': 'local nominal m'},
              'error_assumption': 'Independent Gaussian log errors; repeatability is not a complete field error budget',
              'extra_log_sigma': extra_log_sigma, 'start_model': start.tolist(), 'regularization_lambda': 0,
              'model_h_rho_top_rho_bottom': model.tolist(), 'training_only_model': train_model.tolist(),
              'counts': {'original': len(result), 'retained': int(retained.sum()), 'holdout': int(held_out.sum())},
              'chi_square': statistic, 'degrees_of_freedom': dof, 'critical_99': float(chi2.ppf(.99, dof)),
              'local_refinement': {'converged': local_converged, 'rank': rank, 'chi_square': refined_q},
              'fit_status': ('combined_model_and_error_assumptions_rejected' if statistic > chi2.ppf(.99, dof)
                             else 'nominal_residual_criterion_met') if local_converged else 'local_convergence_unverified',
              'holdout_log_rmse': float(np.sqrt(np.mean((np.log(prediction_holdout) - np.log(values[held_out])) ** 2))),
              'holdout_baseline_log_rmse': float(np.sqrt(np.mean((baseline - np.log(values[held_out])) ** 2))),
              'ground_truth': None,
              'limitations': 'Quadrupole holdout shares electrodes; not an independent survey, 2D image, resolution test or true underground recovery.'}
    output.mkdir(parents=True)
    result.to_csv(output / 'responses.csv', index=False, float_format='%.17g')
    electrodes.to_csv(output / 'electrodes.csv', index=False, float_format='%.17g')
    report['outputs_sha256'] = {name: digest(output / name) for name in ('responses.csv', 'electrodes.csv')}
    (output / 'inversion.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    return report


def read_result(output_dir):
    output = Path(output_dir)
    report = json.loads((output / 'inversion.json').read_text())
    for name, expected in report['outputs_sha256'].items():
        if digest(output / name) != expected:
            raise ValueError('Export checksum mismatch')
    responses = pd.read_csv(output / 'responses.csv', float_precision='round_trip')
    if len(responses) != report['counts']['original']:
        raise ValueError('Output count does not match report')
    return responses, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observations', required=True)
    parser.add_argument('--electrodes', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--geometry-note', required=True)
    parser.add_argument('--extra-log-sigma', type=float, default=.03)
    args = parser.parse_args()
    try:
        run_workflow(args.observations, args.electrodes, args.output,
                     geometry_note=args.geometry_note, extra_log_sigma=args.extra_log_sigma)
        read_result(args.output)
        print(f'Created and verified {args.output}')
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
