---
name: pastas
description: |
  Groundwater time series analysis and modelling using transfer function noise
  models. Use when the agent needs to: (1) Analyze groundwater level time series,
  (2) Model well responses to precipitation/pumping, (3) Calibrate aquifer
  parameters from head data, (4) Forecast or hindcast groundwater levels,
  (5) Decompose hydrological signals into components, (6) Compare response
  functions, (7) Perform model diagnostics and uncertainty analysis.
license: MIT
metadata:
  version: "1.0.2"
  author: Geoscience Skills
  tags: '["Groundwater", "Hydrology", "Time Series", "Transfer Function", "Well Response"]'
  dependencies: '["pastas>=2.0,<2.1", "pandas>=2.2,<4", "scipy>=1.16,<2", "tqdm"]'
  complements: '["xarray"]'
  workflow_role: analysis
  skill_type: domain
---

# Groundwater response models with Pastas

Use Pastas for a well's response to time-varying stresses. Fitted response
parameters are effective model parameters; they do not by themselves establish
transmissivity, aquifer geometry or hydraulic connectivity. Use FloPy/MODFLOW
for a supported spatial-flow question.

This entrypoint targets **Pastas 2.0**. Its component constructors accept the
owning model and register themselves; older `add_stressmodel` patterns are
being retired. Use the tested dependency baseline for reproducible work. The
2.0 package also needs `tqdm` for its imported solver timer in the checked environment.

## Prepare data and reserve evaluation dates

Record the head unit and vertical reference, well/screen, timestamp convention,
stress units and whether evaporation is measured or estimated reference
potential evaporation. A negative relative head or depth-to-water series is
not automatically elevation above sea level. Preserve the original datum.

For daily recharge models use consistently converted head (m), precipitation
and reference evaporation (mm/day). Preserve daily accumulation labels; do not
invent a timezone or shift dates without knowing the observation support.
Missing rainfall is not zero. Keep head gaps unfilled, check stress coverage
through the model warmup, and record any stress infilling with its calibration
source. Pastas defaults can fill and extend stresses, so make these choices
explicit before constructing the model.

Fix calibration and holdout dates before fitting. Construct the model using
calibration heads and stresses only, including data-derived initial values.
Future observed stresses may support a hindcast; future observed heads must
not adjust fitted parameters or simulated state. A forecast additionally needs
specified future stress scenarios and uncertainty.

## Calibrate a checked recharge model

This function expects unique, ordered daily-date Series, complete nonnegative
stresses covering the requested observed warmup, and at least three finite
calibration heads. Those input checks are enforced by the bundled helper.

```python
import pastas as ps

def fit_recharge(calibration_head, calibration_precip, calibration_evap,
                 start, end, warmup_days):
    model = ps.Model(calibration_head, name='well')
    settings = {'freq': 'D', 'sample_up': 'bfill', 'sample_down': 'mean',
                'fill_nan': None, 'fill_before': None, 'fill_after': None}
    ps.RechargeModel(model, calibration_precip, calibration_evap,
                     rfunc=ps.Gamma(), recharge=ps.rch.Linear(), name='recharge',
                     settings=(settings.copy(), settings.copy()))
    ps.ArNoiseModel(model)
    model.solve(tmin=start, tmax=end, warmup=warmup_days, report=False)
    if not model.solver.result.success:
        raise RuntimeError('Calibration did not converge')
    return model
```

The [calibration helper](scripts/groundwater_model.py) validates CSV shape,
dates, explicit calibration windows and stress coverage, then saves `.pas`
with `model.to_file(...)`. Plotting is optional. It assumes already normalized
units; it does not guess them from column names or perform missing-stress fills.

```bash
python scripts/groundwater_model.py head_m.csv rain_mm_day.csv evap_mm_day.csv \
  --calibration-start 2005-01-01 --calibration-end 2013-12-31 \
  --warmup-days 730 --noise --output fitted.pas
```

Resolve the script relative to this installed skill directory. A calibrated
file is not a completed holdout evaluation: report baselines, independent
observed-date metrics and residuals using the fixed evaluation period.

## Contributions, diagnostics and persistence

`model.get_contributions()` returns a list of Series, possibly split into
precipitation and evaporation components. Iterate the list or request one
combined contribution with `model.get_contribution('recharge')`; do not call
`.items()` on it. Add the fitted constant when checking the total simulation.
A block response represents a finite-duration stress block, not an instantaneous
impulse. Use `model.get_step_response` and `model.get_block_response` accordingly.

Save with `model.to_file('model.pas')`, reload with `ps.io.load('model.pas')`,
and compare simulations on the same date window. There is no `Model.to_json`
method in the checked API. Adding `ps.ArNoiseModel(model)` is distinct from
merely passing a `noise=True` solver flag.

Use `ps.stats.acf(residuals, lags=[1, 7, 30], bin_method='gaussian')` when
observations have gaps; specify lag units in days and inspect pair counts.
Residual and noise-series diagnostics answer different questions. AIC/BIC
comparison requires the same observations/objective, and a universal EVP>70%
threshold is not a validation criterion. Persistent innovation correlation
limits confidence in conventional parameter standard errors.

Read [stress configuration](references/stress_models.md) for pumping/river
inputs and nonlinear recharge, or [response interpretation](references/response_functions.md)
for parameter signs, units and response tails. These conditional structures
need their own data and diagnostics.

## Executed scope

The project's hydrogeological workflow runs a fixed public USGS/GSOD recharge
hindcast with Pastas 2.0: QC, calibration-only fitting, three baselines, residual
ACF, continuous holdout simulation and save/load readback. The helper's daily
recharge path and pumping-response sign also have real-library checks. This
does not validate every nonlinear, multiwell or uncertainty configuration.

[Official Pastas 2.0 release](https://github.com/pastas/pastas/releases/tag/v2.0.0),
[versioned model API source](https://github.com/pastas/pastas/blob/fe740c1c270be41a95f4a8b8b0965f26c4ef6769/pastas/model.py),
checked 2026-09-15.
