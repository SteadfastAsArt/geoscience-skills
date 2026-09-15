# Conditional stress-model configuration

## Daily recharge

Pastas 2.0 accepts `ps.RechargeModel(model, prec, evap, ...)`. Pass a recharge
object such as `ps.rch.Linear()` or `ps.rch.FlexModel()`, not the string
`"FlexModel"`. Linear recharge is `P + f*E`: the fitted `f` is normally negative,
so this represents an evaporation loss. Do not apply another minus sign when
interpreting a fitted negative parameter.

Use mm/day for nonlinear recharge models, which include parameters expressed
in millimetres. A daily total in mm is numerically a mean rate in mm/day for a
one-day interval; preserve which date labels that interval. Unequal-duration
accumulations need explicit conversion before use.

Defaults such as `settings="prec"` can fill missing values and extend stress
history. The checked workflow supplies complete daily series and disables
`fill_nan`, `fill_before` and `fill_after`. Its three missing rainfall days are
explicitly imputed from calibration-only monthly means and remain flagged.

## Pumping and river stages

For a single pumping series, use
`ps.StressModel(model, pumping, ps.Hantush(), name="pumping", up=False, settings=...)`.
Positive abstraction with `up=False` produces negative head contributions.
Record the pumping rate unit and extraction/injection sign. Missing pumping
records must not imply that a well was off.

`ps.WellModel(model, stresses, name="wells", distances=...)` uses a
`HantushWellModel` response, not an ordinary `Hantush` instance. Distances,
well identifiers and source-specific stress histories must align. Multiwell
parameter interpretation needs the documented coordinate and distance units;
it is not established by the single-series sign regression.

For river stages, `ps.StressModel(model, river, ps.Exponential(), name="river",
settings="waterlevel")` is the applicable shape of the API. Review its filling
and centering assumptions. Do not use precipitation settings for barometric
pressure simply because both are time series.

## Future stresses

After fitting, `model.stressmodels['recharge'].set_stress(prec=series)` replaces
precipitation. Set evaporation in a separate call: supplying both in one call
is rejected in 2.0. Supply actual warmup through evaluation coverage, keep the
fitted parameter vector fixed, and simulate continuously through the holdout.
Using observed holdout meteorology is a conditional hindcast, not a forecast
with unknown future weather.

[Pastas 2.0 stress models](https://github.com/pastas/pastas/blob/fe740c1c270be41a95f4a8b8b0965f26c4ef6769/pastas/stressmodels.py),
checked 2026-09-15. FlexModel, river and multiwell field calibrations remain
conditional guidance rather than executed branches of this workflow case.
