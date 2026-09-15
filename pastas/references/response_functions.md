# Response functions and inference limits

## Start with a supportable structure

Gamma has gain `A`, shape `n` and time scale `a`; Exponential has gain `A` and
time scale `a` (two parameters, not one). Time scales are in days in the checked
daily model. The gain's units depend on the head and stress units: for metre
heads and mm/day stress, a steady-state gain is m per mm/day. Numeric gain
ranges cannot be transferred unchanged between m/day and mm/day inputs.

A Gamma response need not have a delayed peak for every shape value. Polder
is not a general-purpose dual-porosity/two-peak model. Choose a response using
the stress mechanism and calibration diagnostics, not a library-name table
that equates each function to a uniquely identified aquifer type.

Hantush and HantushWellModel serve different single/multiwell APIs. Their
parameterization changed in 2.0; consult the versioned source before converting
fitted values to hydraulic quantities. A standalone `ps.Theis()` is not a core
Pastas 2.0 response; additional response classes belong to separately installed
Pastas plugins and need their own verification.

## Warmup and tails

A step response approaches the long-term gain. A block response is the
response to stress applied over a finite interval. Avoid calling it an impulse
unless the finite-block convention is stated. `model.get_response_tmax(name)`
reports the response duration at the configured cutoff. Ensure this fits within
the supplied observed warmup; do not let an automatic mean extension stand in
for unavailable decades of forcing without recording that assumption.

The public workflow fixes Gamma cutoff 0.999 and observed warmup 730 days before
fitting. Its fitted response duration is about 395 days. A case with a longer
fitted tail fails that workflow check and requires revisiting the calibration
design, not consulting holdout heads to choose a more favorable warmup.

## Compare models inside calibration

Compare candidate structures using the same observations and objective on an
internal training/validation split. AIC with correlated unmodelled residuals
and AIC from noise-model fits are not automatically comparable evidence. Keep
the final chronological holdout untouched by response-function selection.

Inspect parameter bounds, covariance and residual/noise diagnostics together.
A low RMSE can coexist with correlated innovations, unidentified parameters,
or omitted pumping/snow/river effects. The checked recharge case still has
innovation autocorrelation; its parameter errors are not validated predictive
coverage or proof of causal aquifer properties.

[Versioned response implementation](https://github.com/pastas/pastas/blob/fe740c1c270be41a95f4a8b8b0965f26c4ef6769/pastas/rfunc.py),
checked 2026-09-15.
