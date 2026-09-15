# Daily groundwater hindcast recipe

## Fixed public case

The project caches `collenteur_2019` from the official Pastas **data** repository
at commit `dcc1363765c0a40ee9dfb2a418f8589b3a146580`. It contains USGS well
412918071321001 near Kingstown, Rhode Island, precipitation from Kingston
GSOD/WBAN 54796, and estimated reference evaporation. The dedicated data
repository declares GPL-3.0; raw CSVs retain that license and source. They are
not relabeled using the Pastas software's MIT license.

The [published example notebook](https://github.com/pastas/pastas/blob/fe740c1c270be41a95f4a8b8b0965f26c4ef6769/doc/examples/groundwater_paper/Ex1_simple_model/Example1.ipynb)
establishes source units as feet and feet/day. The runner multiplies head by
0.3048 and stresses by 304.8 to obtain metres and mm/day. It preserves negative
relative heads and makes no unsupported conversion to sea-level elevation.
Dates have no supplied timezone or precise daily-accumulation boundary;
preserve those labels instead of asserting that they are UTC instants.

The design is fixed before fitting: calibration 2005-01-01 through 2013-12-31,
holdout 2014-01-01 through 2018-12-25, daily stresses, observed warmup 730 days,
Gamma cutoff 0.999, linear recharge and AR noise. No response-function search or
holdout-based tuning is performed. The model stores only calibration heads.

## Run from a project checkout

Install `tests/science/requirements-hydro-workflow.txt` into a new Python 3.11
environment. The tests and cached data require no runtime network access.
From the repository root, with that environment active:

```bash
python workflows/hydrogeological-analysis/scripts/run_pastas_workflow.py \
  --data-dir tests/fixtures/workflows/hydro --output-dir /tmp/hydro-case-results
```

For a separately installed workflow, resolve `scripts/run_pastas_workflow.py`
relative to its skill directory and supply your own local data/design bundle.
The regression fixture is an optional project artifact, not an assumed
companion-skill resource. The following Python entrypoint likewise resolves
the helper from the explicitly supplied installed workflow directory:

```python
from pathlib import Path
import importlib.util

def run_local_case(workflow_dir, data_dir, output_dir):
    script = Path(workflow_dir) / 'scripts' / 'run_pastas_workflow.py'
    spec = importlib.util.spec_from_file_location('hydro_workflow', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run_case(Path(data_dir), Path(output_dir))
```

## Input bundle and QC

Use three two-column date/value CSVs, `design.json`, and `provenance.json`.
`design.json` declares the four explicit window endpoints, positive integer
`warmup_days`, `response_cutoff`, solver `max_nfev`, model name, units,
`timestamp_convention`, `vertical_reference` and a `data_files` mapping with
`head`, `precipitation`, `evaporation` keys. `head_input_unit` is ft or m;
`stress_input_unit` is ft/day or mm/day. `provenance.json` records source,
license and a `files` mapping with each local file's SHA-256. Use the checked
fixture's JSON as the concrete schema; adapt source metadata honestly.

This runner handles naive daily date labels with observation gaps, at least
365 calibration heads and 30 holdout heads, and twelve months of calibration
data. Non-daily sampling support or timezone-aware timestamps require a separately designed
preprocessing path. Duplicate dates, infinite measurements, negative stresses
and absent warmup coverage fail rather than being silently transformed.

Missing head dates remain NaN and are excluded from scoring. At most 1% of the
required stress interval may be imputed by the explicitly chosen policy:
calendar-month means learned from observed calibration stresses only. The
policy also applies to holdout gaps, never using held-out heads or future
stress statistics. For this case it fills three rainfall dates, including two
in the holdout, and records every replacement. Monthly mean rainfall is an
uncertain approximation, not a recovered observation; retain its flags.

## Interpretation and artifacts

The comparison baselines use only calibration data: one overall mean, twelve
monthly means, and the last calibration head held fixed throughout holdout.
The last baseline is a fixed-origin persistence benchmark, not a rolling model
that sees yesterday's held-out head. Score all predictions at the same observed
dates. Continue the stress-driven simulation through the split; do not restart
state at the first validation date or update it from validation residuals.

Outputs include `model.pas`, `simulation.csv`, head/stress QC tables,
`parameters.csv`, `recharge_contribution.csv`, `diagnostics.csv` and `report.json`.
They record software versions, data/design hashes, imputation, metrics and
model readback error. The output directory must be new or empty. CSV gaps stay
empty; JSON uses strict finite numeric fields. Model serialization can contain
creation metadata, so compare parameters/simulations within numerical tolerance
rather than claiming every serialized byte is reproducible.

The held-out RMSE is about 0.129 m versus 0.269 m for monthly climatology. The
calibration AR innovation ACF at one day is still about 0.36, outside the reported
reference band. This signals remaining dependence despite an improved fit.
Do not claim white residuals, causal recharge estimates, reliable parameter
confidence coverage or future-weather forecast skill. The fitted response tail
at cutoff 0.999 is about 395 days, within the supplied 730-day warmup.

[Dataset repository](https://github.com/pastas/pastas-data/tree/dcc1363765c0a40ee9dfb2a418f8589b3a146580/collenteur_2019),
[data license](https://github.com/pastas/pastas-data/blob/dcc1363765c0a40ee9dfb2a418f8589b3a146580/LICENSE),
[Collenteur et al. (2019)](https://doi.org/10.1111/gwat.12925), checked 2026-09-15.
