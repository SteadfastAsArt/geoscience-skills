# Groundwater workflow validation

Validated 2026-09-15 with Python 3.11 and Pastas 2.0.0. The
[`hydrogeological-analysis` workflow](../workflows/hydrogeological-analysis/SKILL.md)
now executes a complete public-data groundwater hindcast: immutable input
verification, unit conversion and QC, fixed calibration/holdout, recharge and
noise-model fitting, three baseline comparisons, residual diagnostics, and
model/CSV/JSON readback. Thirteen scientific regression tests pass with no
skipped dependencies or examples.

## Reproduce

From the repository root, create a dedicated environment. The exact direct
dependency baseline is
[`requirements-hydro-workflow.txt`](../tests/science/requirements-hydro-workflow.txt):
Pastas 2.0.0, NumPy 2.4.6, pandas 3.0.5, SciPy 1.17.1, Matplotlib 3.11.2,
Numba 0.67.0, llvmlite 0.49.0 and tqdm 4.70.1. The explicit tqdm pin is
necessary because Pastas 2.0 imports it through `SolveTimer` without declaring
it in the base installation requirements.

```bash
python3.11 -m venv /tmp/geoscience-hydro-env
/tmp/geoscience-hydro-env/bin/python -m pip install -r tests/science/requirements-hydro-workflow.txt
MPLBACKEND=Agg NUMBA_THREADING_LAYER=workqueue OPENBLAS_NUM_THREADS=1 \
  /tmp/geoscience-hydro-env/bin/python -m unittest discover \
  -s tests/science -p 'test_hydro_workflow.py' -v
MPLBACKEND=Agg NUMBA_THREADING_LAYER=workqueue OPENBLAS_NUM_THREADS=1 \
  /tmp/geoscience-hydro-env/bin/python \
  workflows/hydrogeological-analysis/scripts/run_pastas_workflow.py \
  --data-dir tests/fixtures/workflows/hydro --output-dir /tmp/hydro-case-results
```

Choose a new or empty result directory. `workqueue` avoids dependence on the
host's optional TBB installation; all scientific packages are installed only
inside the new environment. The test run and runner require no runtime network
access once dependencies are installed. Missing dependencies raise import
errors. The suite directly executes the Python block in the workflow's field
recipe and the calibration block in `pastas/SKILL.md`, as well as both actual
CLI helpers. It does not substitute mocks for Pastas.

## Source, units and fixed design

The [fixture](../tests/fixtures/workflows/hydro/README.md) preserves exact raw
CSVs and upstream settings from the dedicated
[Pastas data repository](https://github.com/pastas/pastas-data/tree/dcc1363765c0a40ee9dfb2a418f8589b3a146580/collenteur_2019)
at commit `dcc1363765c0a40ee9dfb2a418f8589b3a146580` (2025-07-29). Its GPL-3.0
data-license declaration is retained separately in `LICENSE.upstream`, together
with source URLs and SHA-256 values in `provenance.json`. This license is taken
from the data repository, not inferred from the software license.

The published record comprises USGS well 412918071321001 near Kingstown,
Rhode Island; Kingston GSOD/WBAN 54796 precipitation; and temperature-derived
reference evaporation. The
[original notebook](https://github.com/pastas/pastas/blob/fe740c1c270be41a95f4a8b8b0965f26c4ef6769/doc/examples/groundwater_paper/Ex1_simple_model/Example1.ipynb)
and [paper](https://doi.org/10.1111/gwat.12925) establish provenance and source
units. Head is converted from feet to metres; rainfall and estimated reference
evaporation are converted from feet/day to mm/day. Absolute head datum, screen
metadata, timezone and the precise stress accumulation boundary remain
unresolved. The workflow preserves negative relative heads and naive date
labels; it does not invent sea-level elevations or UTC instants.

| Design choice | Fixed value |
| --- | --- |
| Calibration | 2005-01-01–2013-12-31; 3,232 observed heads |
| Holdout | 2014-01-01–2018-12-25; 1,811 observed heads |
| Observed stress warmup | 730 days, beginning 2003-01-02 |
| Model | Gamma response, cutoff 0.999; linear recharge; AR noise |
| Fit | Deterministic least squares, at most 300 evaluations; no model search |
| Missing stresses | At most 1%; calibration calendar-month mean, flagged |
| Baselines | Calibration overall mean, monthly means and fixed last head |

The design was specified before the first fit. The Pastas model is initially
constructed using only calibration heads and stresses through calibration end,
so data-derived parameter initializations cannot use holdout observations or
future stress statistics. After fitting, the runner extends precipitation and
evaporation separately and carries the same response into a continuous
hindcast. It never incorporates held-out head residuals. The persistence
baseline holds the final training observation fixed throughout holdout rather
than seeing new validation observations each day.

The full head calendar retains 101 missing dates. Within the required stress
period, three missing rainfall dates are filled explicitly: 2008-11-11,
2014-07-26 and 2014-07-27. The last two use observed calibration July rain only.
Missing heads remain NaN and unscored; no synthetic head enters calibration or
the evaluation denominator. The runner disables implicit stress filling and
history extension and rejects duplicate dates, infinities, negative stresses,
absent warmup coverage and excessive gaps. Monthly mean rain is an uncertain
approximation, not an observation or a recovered storm sequence.

## Measured results

| Predictor | Calibration RMSE (m) | Holdout RMSE (m) |
| --- | ---: | ---: |
| Pastas recharge model | 0.132611 | 0.128636 |
| Calibration mean | 0.375103 | 0.374236 |
| Calibration monthly means | 0.300087 | 0.269231 |
| Last calibration head, held fixed | 0.478987 | 0.385670 |

Holdout NSE is 0.864370; mean observed-minus-simulated head is 0.002942 m.
The optimizer reports success after 21 evaluations. The fitted response tail
at cutoff 0.999 is 395.009 days, within the supplied 730-day history. Save/load
reproduced simulation with maximum absolute difference about `1.91e-12` m;
the acceptance tolerance is `1e-8` m. Parameters and simulations, rather than
serialization timestamps or byte-identical files, define repeatability.

| Calibration diagnostic | One-day ACF |
| --- | ---: |
| Head residual | 0.994968 |
| AR innovation | 0.359150 |

Diagnostics use Pastas's irregular-observation ACF with explicit day lags,
Gaussian bin width and pair-count output; they do not replace missing residuals
with interpolated values. The one-day innovation ACF remains outside the
reported reference band (about 0.040748). The fitted noise model reduces
dependence but does not make innovations white. Conventional parameter
standard errors are conditional summaries, not validated prediction intervals.

The tests independently recompute holdout error and baseline comparisons,
check source hashes and unit conversion, retain missing-value masks, and
verify contribution-plus-constant closure and model/CSV readback. Re-fitting
after adding 100 ft to every held-out head leaves parameters and simulation
unchanged. Adding 1 mm/day to observed future rainfall changes the hindcast
while leaving fitted parameters, calibration predictions and imputation
statistics unchanged. These perturbations test information flow through the
actual implementation, not a copied response formula. CLI tests also verify
optional plot creation and preservation of existing output.

## API corrections and scope

Pastas 2.0 attaches components through `RechargeModel(model, ...)`,
`StressModel(model, ...)` and `ArNoiseModel(model)`. The domain guide and helper
now use these actual interfaces, `get_contributions()` as a list, and
`model.to_file(...)` with `ps.io.load(...)`; there is no checked
`Model.to_json` method. The runner uses `ps.solver.LeastSquares` and extends
precipitation and evaporation with separate `set_stress` calls. Reference
guides distinguish the fitted negative evaporation coefficient, pumping sign,
finite block response and optional/non-core response implementations. The
helper's pumping-response sign is tested using a real Hantush component;
this does not constitute field pumping-parameter validation.

These APIs were verified against the official
[Pastas 2.0 release](https://github.com/pastas/pastas/releases/tag/v2.0.0),
[model source](https://github.com/pastas/pastas/blob/fe740c1c270be41a95f4a8b8b0965f26c4ef6769/pastas/model.py)
and [stress-model source](https://github.com/pastas/pastas/blob/fe740c1c270be41a95f4a8b8b0965f26c4ef6769/pastas/stressmodels.py),
checked 2026-09-15.

This result establishes one reproducible recharge hindcast conditional on
observed future meteorology. It does not establish forecast skill under
unknown weather, causal recharge attribution, calibrated uncertainty coverage,
wet/dry-regime robustness, multiwell transferability or aquifer-property truth.
No field MODFLOW calibration, well-log interpretation or spatial validation
was performed here; the optional FloPy branch retains its separate executable,
water-balance and conceptual-model requirements.
