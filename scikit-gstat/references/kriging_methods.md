# Ordinary kriging and spatial validation

The examples below are fragments requiring finite, unique local projected
`coords` of shape `(n, 2)`, `values` of shape `(n,)`, and prediction coordinates
in the same CRS and units. Preserve the original input and its missingness mask.

## Predictions and conditional variance

```python
import numpy as np
import skgstat as skg

V = skg.Variogram(coords, values, model="spherical", n_lags=10)
ok = skg.OrdinaryKriging(V, min_points=3, max_points=15)
predictions = ok.transform(*grid_coords.T)
variance = ok.sigma.copy()
```

Each `transform` overwrites `ok.sigma`. For chunked prediction, collect both
arrays before starting the next chunk. `min_points` and integer `max_points`
limit the neighbours within the model's effective range. Unsupported points
remain NaN; report their count rather than replacing them with zero.

The variance has squared value units. It is conditional on the specified model,
neighbourhood and mean assumptions. Low variance does not guarantee an accurate
or unbiased field prediction, and it does not include fitted-parameter
uncertainty. A prediction interval requires additional distributional assumptions
and a calibration check. Material negative variances require investigation;
do not silently take absolute values or clip them to make a plot.

The built-in class is `OrdinaryKriging`. Use an appropriate external library or
adapter for simple/universal kriging and external drift. Duplicate locations,
conflicting measurements and singular systems require an explicit data/error
model. A nugget should have a scientific justification; adding one solely to
suppress a numerical failure can change the estimand.

## Spatial holdout

Define a boolean `test_mask` from spatial blocks, survey identity or the intended
prediction setting before fitting. Use a separate validation set for tuning.
This fragment fixes the model and fits its variogram on training observations
only; any trend, scaling or imputation would also need training-only fitting.
Repeat it for predeclared folds, preserving target identities.

```python
import numpy as np
import skgstat as skg

train = ~test_mask
if not train.any() or not test_mask.any():
    raise ValueError("A holdout needs both training and test observations")
V_train = skg.Variogram(coords[train], values[train], model="spherical",
                        n_lags=10, maxlag="median", use_nugget=False)
ok_train = skg.OrdinaryKriging(V_train, min_points=3, max_points=15)
prediction = ok_train.transform(*coords[test_mask].T)
variance = ok_train.sigma.copy()
supported = np.isfinite(prediction) & np.isfinite(variance)
observed = values[test_mask]
baseline = float(values[train].mean())
report = {
    "targets": int(test_mask.sum()),
    "predicted": int(supported.sum()),
    "unsupported": int((~supported).sum()),
    "coverage": float(supported.mean()),
    "rmse_on_supported": None,
    "baseline_rmse_on_same_targets": None,
}
if supported.any():
    report["rmse_on_supported"] = float(np.sqrt(np.mean(
        (prediction[supported] - observed[supported]) ** 2)))
    report["baseline_rmse_on_same_targets"] = float(np.sqrt(np.mean(
        (baseline - observed[supported]) ** 2)))
```

Changing held-out values must not change `V_train`, the predictions, variance or
baseline. It should change only the observed residuals and their scores.
Neighbouring random folds answer a different question from prediction in a new
area. Report block geometry, any separation buffer and coverage with the score.
No supported predictions means no RMSE, rather than a passing or zero-error run.

`V.cross_validate()` offers a leave-one-out diagnostic conditional on an already
fitted variogram; it does not refit that variogram per held-out observation.
Do not label it an independent assessment of the complete model-fitting pipeline.
`cross_val_score(ok, ...)` is invalid because `OrdinaryKriging` has no `fit` method.

## Sources

- [Kriging API](https://scikit-gstat.readthedocs.io/en/latest/reference/kriging.html)
- [Variance example](https://scikit-gstat.readthedocs.io/en/latest/userguide/kriging.html)
- [Variogram API](https://scikit-gstat.readthedocs.io/en/latest/reference/variogram.html)
