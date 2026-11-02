---
name: scikit-gstat
description: >-
  Estimate and diagnose variograms, perform ordinary kriging, and validate spatial
  interpolation with SciKit-GStat. Use for empirical or directional variograms,
  covariance-model comparison and kriging prediction/variance; use PyKrige or
  GSTools when the task requires universal kriging or external drift.
license: MIT
metadata:
  version: "1.0.2"
  author: Geoscience Skills
  tags: '["Geostatistics", "Variogram", "Kriging", "Spatial Statistics", "Directional Analysis"]'
  dependencies: '["scikit-gstat>=1.0.0", "numpy", "scipy", "scikit-learn", "pandas", "matplotlib"]'
  complements: '["verde", "geostatspy"]'
  workflow_role: analysis
  skill_type: domain
---

# SciKit-GStat

Fit spatial dependence and produce ordinary-kriging estimates with their
conditional variances. A fitted variogram is not itself evidence of predictive
accuracy or calibrated uncertainty.

## Inputs and conventions

Use coordinates shaped `(n, 2)` and one scalar observation per location. Record
the coordinate reference system, distance units, measurement units and sampling
support. For a regional Euclidean-distance model, project longitude/latitude
into a suitable distance-based CRS before fitting. Resolve trends and repeated
locations explicitly; do not silently perturb duplicate coordinates.

Mask missing measurements consistently in coordinates and values. Preserve their
identity in the source data; unknown measurements are not zeros. Variances,
sills and nuggets have squared measurement units. SciKit-GStat's named `sill`
is the partial sill: the plateau is `sill + nugget`. Its `effective_range` uses
the library's model-specific convention, not a universally interchangeable
correlation length.

## Ordinary kriging example

This runnable example uses synthetic measurements and local Cartesian metres.
For real work, replace the inputs and establish an appropriate model and support.

```python
import numpy as np
import skgstat as skg

rng = np.random.default_rng(13)
coords = rng.uniform(0, 100, (90, 2))  # synthetic local x/y, metres
values = np.sin(coords[:, 0] / 25) + np.cos(coords[:, 1] / 30)
values += rng.normal(0, 0.08, len(coords))  # arbitrary measurement units

grid_coords = np.array([[30., 30.], [50., 50.], [70., 60.]])
V = skg.Variogram(coords, values, model="spherical", n_lags=10,
                  maxlag="median", use_nugget=False)
ok = skg.OrdinaryKriging(V, min_points=3, max_points=12)
predictions = ok.transform(*grid_coords.T)
variance = ok.sigma.copy()  # variance for the MOST RECENT transform, not stddev
supported = np.isfinite(predictions) & np.isfinite(variance)
print(predictions, variance, supported)
```

`transform` returns only predictions. `return_variance` does not enable tuple
output. Copy `ok.sigma` before the next transform, including when processing
chunks. Inadequate neighbourhoods may produce NaN; report support and preserve
those gaps. Conditional kriging variance excludes uncertainty in fitted
variogram parameters, trend choice and sampling bias.

## Fit diagnostics and validation

Read parameters by name using `V.describe(short=True)`. Matérn and stable models
place a smoothness/shape parameter before their nugget in `V.parameters`.
Evaluate a fitted model with `V.transform(lags)` so all fitted parameters are
retained. See [model conventions](references/variogram_models.md) for parameter
meaning, effective ranges and diagnostic examples.

Compare variogram-bin RMSE only as an in-sample diagnostic. For predictive
assessment, declare spatial groups or survey holdouts before fitting; refit the
variogram and every preprocessing step using each training fold only. Follow
the [training-only holdout example](references/kriging_methods.md#spatial-holdout)
for this path. `OrdinaryKriging` is not a scikit-learn estimator that can be
passed directly to `cross_val_score`. Report unpredicted targets alongside RMSE;
do not improve a score by quietly dropping poorly supported locations.

`DirectionalVariogram` can compare azimuths, but different directional ranges
alone do not establish significant anisotropy. Inspect pair counts, trends and
sampling geometry before changing the covariance or distance model.

## Alternatives and outputs

Use PyKrige/GSTools for drift-aware kriging, GeostatsPy for GSLIB-style simulation,
and Verde for gridding without a variogram model. SciKit-GStat's built-in
interpolator is ordinary kriging; its adapters do not make every object
scikit-learn-compatible.

Retain prediction locations, units/CRS, missing/support masks, fitted parameters,
training partitions and input provenance. Check outputs against held-out
observations and a training-only baseline. Label uncertainties by what they cover.

## Bundled diagnostic script

Resolve [scripts/variogram_analysis.py](scripts/variogram_analysis.py) relative
to this skill. It reads explicitly selected CSV columns, removes rows missing
any selected field, and rejects infinities, duplicate locations and constant
values. Keep the original CSV to retain dropped-row identities. It compares
in-sample fits and directional diagnostics; it does not run predictive validation.

```bash
python /path/to/scikit-gstat/scripts/variogram_analysis.py samples.csv \
  --x easting --y northing --z porosity --n-lags 15 --maxlag median \
  --output variogram-results
```

The nugget is fixed at zero by default; `--use-nugget` fits it. A numeric
`--maxlag` below 1 means a fraction of maximum pair distance; larger values use
coordinate units. JSON preserves effective range, partial sill, nugget and any
shape parameter separately. Plots evaluate all fitted parameters. Supply the
CRS and units in the surrounding analysis record; this script does not infer
or transform them. Check the exported JSON and figures before interpretation.
