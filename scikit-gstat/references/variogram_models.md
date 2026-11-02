# Variogram parameter conventions

SciKit-GStat uses effective range `r`, partial sill `c0` and nugget `b`.
The plateau is `c0 + b`. Range has coordinate-distance units; partial sill and
nugget have squared observation units. Parameters from another library need an
explicit convention conversion before reuse.

## Parameter order

| Model | `V.parameters` order |
| --- | --- |
| spherical, exponential, gaussian | effective range, partial sill, nugget |
| matern | effective range, partial sill, smoothness, nugget |
| stable | effective range, partial sill, shape, nugget |

Use `V.describe(short=True)` for named fields, and `V.transform(lags)` to evaluate
the fitted function. Truncating the parameter list to its first three entries
can omit a fitted nugget or mislabel a shape parameter.

## Effective range

For positive separation `h`, the implemented conventions are:

```text
spherical:  gamma(h) = b + c0 * (1.5*h/r - 0.5*(h/r)^3), for h <= r
                       b + c0, for h > r
exponential: gamma(h) = b + c0 * (1 - exp(-3*h/r))
gaussian:    gamma(h) = b + c0 * (1 - exp(-4*(h/r)^2))
```

The exponential reaches about 95% of its partial sill at `r`; the Gaussian
implementation uses a scale of `r/2`. Neither asymptotic model reaches a sharp
correlation cutoff. Matérn and stable use their own shape-dependent conventions;
retain the named shape parameter and consult the upstream function before
transferring a model. Do not identify `r` with a universal correlation length.

## Named parameters and evaluation

This fragment assumes a fitted `V` and an array of nonnegative `lags`:

```python
parameters = V.describe(short=True)
effective_range = parameters["effective_range"]
partial_sill = parameters["sill"]
nugget = parameters["nugget"]
total_sill = partial_sill + nugget
shape = {name: parameters[name] for name in ("smoothness", "shape")
         if name in parameters}
semivariance = V.transform(lags)
```

The default `use_nugget=False` fixes the nugget at zero. Set `use_nugget=True`
when the data and intended model justify estimating it. Fitted nugget and
microscale variance cannot automatically be separated from measurement error.
There is no universal acceptable nugget/sill ratio.

## Comparing models

Variogram-bin RMSE measures agreement with the empirical semivariances used for
fitting. It does not establish out-of-sample interpolation quality. More flexible
models can improve this score without better predictions. Inspect bin pair
counts, sampling support, trends and directional coverage. Choose/tune within
training data and evaluate on independent holdouts using the
[training-only example](kriging_methods.md#spatial-holdout).

The diagnostic script's `best_model` means lowest in-sample bin RMSE among the
successful candidate fits. Its `model_failures` records rejected fits; failure
of every candidate is an error. Compare uncertainty only under clearly stated
model and sampling assumptions.

[Upstream model definitions](https://scikit-gstat.readthedocs.io/en/latest/reference/models.html)
and [parameter API](https://scikit-gstat.readthedocs.io/en/latest/reference/variogram.html),
checked with SciKit-GStat 1.0.24 on 2026-10-25.
