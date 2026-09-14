#!/usr/bin/env python3
"""Run configured PetroPy fluid/multimineral calculations on normalized LAS curves."""
import argparse
import hashlib
import inspect
import json
from pathlib import Path
import sys

import lasio
import numpy as np
import petropy as pp

REQUIRED = ('GR_N', 'NPHI_N', 'RHOB_N', 'RESDEEP_N')
UNITS = {'GR_N': {'api', 'gapi'}, 'NPHI_N': {'v/v', 'dec', 'fraction'},
         'RHOB_N': {'g/cc', 'g/cm3', 'g/cm^3'}, 'RESDEEP_N': {'ohmm', 'ohm.m', 'ohm-m'}}
BASE_VOLUMES = ('PHIE', 'BVOM', 'BVCLAY', 'BVPYR')


def resolved_parameters(method, supplied):
    if not isinstance(supplied, dict):
        raise ValueError('Parameter sections must be JSON objects')
    defaults = {key: value.default for key, value in inspect.signature(method).parameters.items()
                if key not in ('self', 'top', 'bottom')}
    unknown = set(supplied) - set(defaults)
    if unknown:
        raise ValueError(f'Unknown parameters: {sorted(unknown)}')
    defaults.update(supplied)
    for key, value in defaults.items():
        if isinstance(value, (int, float)) and not np.isfinite(value):
            raise ValueError(f'Parameter {key} must be finite')
    return defaults


def load_config(path):
    with open(path, encoding='utf-8') as stream:
        config = json.load(stream)
    if not isinstance(config, dict) or not {'interval_ft', 'fluid', 'multimineral'}.issubset(config):
        raise ValueError('Configuration requires interval_ft, fluid and multimineral sections')
    return config


def evaluate(las_path, config):
    """Intervals are [top,bottom); both endpoints must be sampled depths in ft."""
    if config.get('depth_basis') != 'tvd_below_surface' or not str(config.get('depth_datum', '')).strip():
        raise ValueError('Declare depth_basis=tvd_below_surface and a depth_datum; deviated-well MD is unsupported')
    raw = lasio.read(str(las_path))
    missing = set(REQUIRED) - set(raw.keys())
    if missing:
        raise ValueError(f'Supply measured, normalized curves before PetroPy loading: {sorted(missing)}')
    if any(key in raw.keys() for key in ('PHIE', 'SW', 'BVCLAY', 'BVQTZ', 'BVCLC')):
        raise ValueError('Use source curves without previous model outputs; stale calculated rows are unsafe')
    if raw.curves[0].unit.strip().lower() not in ('ft', 'feet', 'foot'):
        raise ValueError('PetroPy correlations require depth in ft; convert depth and interval explicitly first')
    for key in REQUIRED:
        if raw.curves[key].unit.strip().lower() not in UNITS[key]:
            raise ValueError(f'Unexpected unit for {key}: {raw.curves[key].unit!r}')
    depth = raw.index.astype(float)
    if len(depth) < 2 or not np.isfinite(depth).all() or np.any(depth < 0) or not np.all(np.diff(depth) > 0):
        raise ValueError('Depth must be finite, strictly increasing and contain at least two samples')
    interval = np.asarray(config.get('interval_ft', []), dtype=float)
    if interval.shape != (2,) or not np.isfinite(interval).all() or interval[0] >= interval[1]:
        raise ValueError('interval_ft must contain increasing finite top and bottom depths')
    top, bottom = interval
    if not np.any(depth == top) or not np.any(depth == bottom):
        raise ValueError('PetroPy 0.1.6 requires top and bottom to match sampled depths exactly')
    selected = (depth >= top) & (depth < bottom)
    measured = np.column_stack([raw[key] for key in REQUIRED])
    if np.isinf(measured).any():
        raise ValueError('Infinite input values are invalid; document a missing-value conversion first')
    valid = selected & np.isfinite(measured).all(axis=1)
    if not valid.any():
        raise ValueError('No complete raw samples inside the requested interval')
    if np.any(raw['RHOB_N'][valid] <= 0) or np.any(raw['RESDEEP_N'][valid] <= 0):
        raise ValueError('Density and resistivity must be positive')
    if np.any((raw['NPHI_N'][valid] < -.15) | (raw['NPHI_N'][valid] > 1)):
        raise ValueError('Neutron porosity must be a plausible fraction, not percent')
    if 'PE_N' in raw.keys():
        valid &= np.isfinite(raw['PE_N'])
    fluid_input = config.get('fluid', {})
    model_input = config.get('multimineral', {})
    if not {'mast', 'temp_grad', 'press_grad', 'rws', 'rwt', 'rmfs', 'rmft', 'gas_grav', 'oil_api'}.issubset(fluid_input):
        raise ValueError('Supply the documented fluid calibration parameters explicitly')
    if not {'gr_matrix', 'gr_clay', 'include_qtz', 'include_clc', 'include_dol', 'include_x', 'm', 'n', 'a'}.issubset(model_input):
        raise ValueError('Supply mineral selection, GR endpoints and Archie parameters explicitly')
    fluid = resolved_parameters(pp.Log.fluid_properties, fluid_input)
    model = resolved_parameters(pp.Log.multimineral_model, model_input)
    if any(fluid[key] <= 0 for key in ('rws', 'rmfs', 'gas_grav', 'press_grad')) or fluid['temp_grad'] < 0:
        raise ValueError('Fluid resistivities, gas gravity and pressure gradient must be positive')
    if model['gr_clay'] <= model['gr_matrix'] or any(model[k] <= 0 for k in ('m', 'n', 'a')):
        raise ValueError('GR endpoints must increase and Archie a/m/n must be positive')
    minerals = []
    for name, curve in [('qtz', 'BVQTZ'), ('clc', 'BVCLC'), ('dol', 'BVDOL'), ('x', 'BV' + str(model['name_log_x']).upper())]:
        choice = str(model['include_' + name]).upper()
        if choice not in ('YES', 'NO'):
            raise ValueError('Mineral selection must use YES or NO')
        if choice == 'YES':
            if 'rho_' + name not in model_input or 'nphi_' + name not in model_input or model['rho_' + name] <= 0:
                raise ValueError('Explicit positive density and neutron endpoints are required for every selected mineral')
            minerals.append(curve)
    if not minerals:
        raise ValueError('Select at least one matrix mineral')
    weights = [model[k] for k in ('archie_weight', 'indonesia_weight', 'simandoux_weight', 'modified_simandoux_weight', 'waxman_smits_weight')]
    if min(weights) < 0 or sum(weights) <= 0:
        raise ValueError('Saturation weights must be nonnegative with a positive total')
    # Required measured RHOB_N prevents PetroPy's legacy DPHI fallback from
    # synthesizing density from the depth column during preconditioning.
    log = pp.Log(str(las_path))
    log.fluid_properties(top=float(top), bottom=float(bottom), **fluid)
    log.multimineral_model(top=float(top), bottom=float(bottom), **model)
    volume_curves = list(BASE_VOLUMES) + minerals
    arrays = np.column_stack([log[k] for k in volume_curves])
    if not np.isfinite(arrays[valid]).all() or not np.isfinite(log['SW'][valid]).all():
        raise ValueError('Model returned nonfinite results for complete input samples')
    if not np.isnan(log['PHIE'][~valid]).all():
        raise ValueError('Model unexpectedly filled excluded or missing-input samples')
    if np.any(arrays[valid] < -1e-6) or not np.allclose(arrays[valid].sum(axis=1), 1, atol=1e-5):
        raise ValueError('Bulk mineral plus pore volume does not close to one')
    if np.any((log['SW'][valid] < -1e-6) | (log['SW'][valid] > 1 + 1e-6)):
        raise ValueError('Water saturation is outside physical bounds')
    if not np.allclose(log['BVW'][valid] + log['BVH'][valid], log['PHIE'][valid], atol=1e-5):
        raise ValueError('Water plus hydrocarbon pore volumes do not close')
    summary = dict(interval_ft=[float(top), float(bottom)], interval_convention='top inclusive, bottom exclusive',
                   depth_basis=config['depth_basis'], depth_datum=config['depth_datum'],
                   evaluated_samples=int(valid.sum()), missing_samples=int((selected & ~valid).sum()),
                   volume_closure_max_error=float(np.max(np.abs(arrays[valid].sum(axis=1) - 1))),
                   resolved_fluid=fluid, resolved_multimineral=model,
                   source_sha256=hashlib.sha256(Path(las_path).read_bytes()).hexdigest())
    if 'pay' in config:
        pay_config = config['pay']
        if not isinstance(pay_config, dict) or set(pay_config) != {'phi_min', 'sw_max', 'vclay_max'}:
            raise ValueError('Pay requires phi_min, sw_max and vclay_max')
        if any(not np.isfinite(v) or not 0 <= v <= 1 for v in pay_config.values()):
            raise ValueError('Pay thresholds must be fractions in [0,1]')
        pay = np.full(len(depth), np.nan)
        pay[valid] = ((log['PHIE'][valid] >= pay_config['phi_min']) &
                      (log['SW'][valid] <= pay_config['sw_max']) &
                      (log['VCLAY'][valid] <= pay_config['vclay_max'])).astype(float)
        log.add_curve('PAY', pay, unit='flag', descr='Configured left-sample interval flag; NaN means unevaluated')
        widths = np.diff(depth)
        summary['net_pay_ft'] = float(np.sum(widths[pay[:-1] == 1]))
        summary['unknown_interval_ft'] = float(np.sum(widths[selected[:-1] & ~valid[:-1]]))
        summary['pay_convention'] = 'left sample represents [depth[i], depth[i+1]); no extension beyond bottom'
        summary['pay_thresholds'] = pay_config
    return log, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    parser.add_argument('--config', required=True)
    parser.add_argument('--output', '-o', required=True)
    args = parser.parse_args()
    try:
        source, target = Path(args.input), Path(args.output)
        report = target.with_suffix('.json')
        if source.resolve() in (target.resolve(), report.resolve()) or (target.exists() and source.samefile(target)):
            raise ValueError('Output must not overwrite input')
        if target.resolve() == report.resolve():
            raise ValueError('LAS output must not use the .json suffix')
        log, summary = evaluate(source, load_config(args.config))
        steps = np.diff(log.index)
        step = steps[0] if np.allclose(steps, steps[0], rtol=1e-7, atol=1e-9) else 0.
        log.write(str(target), version=2.0, fmt='%.17g', STEP=step)
        report.write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
        print(f'Created {target}; evaluated {summary["evaluated_samples"]} samples')
        return 0
    except (ValueError, OSError, RuntimeError, KeyError, IndexError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
