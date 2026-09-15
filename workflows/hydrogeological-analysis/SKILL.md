---
name: hydrogeological-analysis
description: >-
  Combine groundwater observations, well logs, and meteorological stresses into
  a checked hydrogeological interpretation or groundwater-level model. Use for
  aquifer monitoring and recharge/pumping response analysis, with spatial flow
  modelling only when its geometry and boundary data are available.
license: MIT
metadata:
  version: "1.0.1"
  author: Geoscience Skills
  skill_type: workflow
  tags: '["Hydrogeology", "Groundwater", "Time Series", "Well Logs"]'
  dependencies: '["pastas>=2.0,<2.1", "tqdm", "lasio", "welly", "pandas", "numpy", "flopy"]'
  complements: '["pastas", "lasio", "welly", "flopy", "xarray", "verde"]'
  workflow_role: modelling
---

# Hydrogeological Analysis

Produce a traceable groundwater interpretation, then fit only the model the
available observations can support. One agent can complete this workflow;
companion skills provide optional detail. Install only the packages used by
the chosen branch; FloPy is an optional spatial-flow branch.

## Choose the branch

| Available information and question | Appropriate route |
| --- | --- |
| Logs, screen depths and construction records; no groundwater time series | Use `lasio` / `welly` for QC and a conceptual aquifer framework; do not invent a head calibration dataset. |
| Observed heads with precipitation, evaporation or pumping series | Use `pastas` for time-series response modelling and withheld-period validation. |
| Distributed heads, geometry, hydraulic properties, stresses and boundary conditions | Consider a FloPy/MODFLOW flow model; first specify the conceptual model and available executable. |
| Only sparse spatial observations | Map measurements with their observation dates and uncertainty; a `verde` interpolation is not a groundwater-flow solution. |

## Establish observations and reference systems

1. Identify each well, screen interval, measurement method, timestamp/timezone,
   pumping status, missing-value codes, units and quality flags. Preserve the
   original observations and a separate table of corrections/exclusions.
2. Distinguish measured depth in a log, depth to water below a measuring point,
   and hydraulic head relative to a vertical datum. Convert depth to water using
   the surveyed measuring-point elevation and its reference; never treat a log
   depth column or well bottom as an observed head. Use trajectory and datum
   information before aligning deviated logs with aquifer elevations.
3. Bring well positions, geology and model grids into a documented CRS. Record
   vertical datum and units separately. Do not merge different screened aquifers
   into one time series merely because their wells are nearby.
4. Inspect stress coverage and sampling support. Distinguish accumulated rainfall
   from rates, and observed evaporation from the quantity expected by the chosen
   recharge model. Missing rainfall is not zero rainfall. Record any infilling
   and its source; require stress coverage through calibration and model warmup.

## Build and test the selected model

For a Pastas model, start with the simplest physically plausible stress-response
structure. Match APIs, units and parameter bounds to the installed version;
consult its [versioned calibration API](https://github.com/pastas/pastas/blob/fe740c1c270be41a95f4a8b8b0965f26c4ef6769/pastas/model.py).
Choose calibration and validation windows before fitting. Fit normalisation,
response parameters and noise models on calibration data only; carry model
state into validation using available stresses, not held-out head observations.
Compare against a suitable persistence or seasonal baseline, inspect residual
autocorrelation and examine wet/dry and pumping regimes separately.

For the optional spatial-flow branch, use the [FloPy documentation](https://flopy.readthedocs.io/en/latest/)
for the installed MODFLOW version. Specify layers, active cells, hydraulic
property units, recharge/pumping, time discretisation, boundary conditions and
initial heads before building inputs. Check solver termination, water balance,
dry/inactive cells and sensitivity to grid/boundary choices. FloPy does not make
an absent MODFLOW executable or unconstrained boundary condition valid: retain
prepared inputs and clearly mark simulation as not run when these are missing.

## Interpretation and deliverables

- Export the observation/QC table, units and reference-system metadata,
  conceptual aquifer assumptions, fitted configuration and software versions.
- Report calibration and held-out metrics in head units, validation dates,
  residual diagnostics, and uncertainty from parameters, stress inputs and
  alternative plausible conceptual models. Keep extrapolation separate from
  tested prediction.
- Use logs to constrain stratigraphic hypotheses, not to assign hydraulic
  conductivity or connectivity from an uncalibrated curve. Electrical
  resistivity, lithology and permeability are not interchangeable quantities.
- For spatial predictions, withhold wells or spatial blocks; for forecasts,
  withhold future periods. Tune model choices inside the training partition and
  keep the final evaluation observations untouched.

## Executed daily groundwater case

The bundled [Pastas runner](scripts/run_pastas_workflow.py) completes a daily
recharge hindcast from locally supplied raw CSVs, a fixed design and provenance:
QC and explicit unit conversion, calibration-only stress infilling/initialization,
Gamma + linear recharge + AR noise fitting, three calibration-only baselines,
held-out metrics, residual/noise ACF, model save/load and CSV/JSON readback.
It disables implicit stress filling and history extension. Each output records
the unchanged date labels and unresolved vertical/time reference.

Read [the public field-case recipe](references/field_case.md) for the cached
USGS/GSOD source, exact calibration/holdout dates, commands, input schema and
observed limitations. The script is local to this installed workflow; the
licensed regression data are separately stored in the project checkout.

## Verification boundary

Executed with Pastas 2.0.0 using a fixed public Kingstown, Rhode Island, record:
2005–2013 calibration and 2014–2018 holdout. The head source is USGS; rainfall is
GSOD and reference evaporation is a published estimate. Held-out RMSE is about
0.129 m against about 0.269 m for the training-month climatology. This is a
hindcast conditional on observed meteorology, not a forecast with unknown weather.

Innovations still show autocorrelation, so parameter standard errors are not
validated prediction intervals. Missing rainfall days use flagged
calibration-month means; missing heads remain unscored. Absolute head datum,
screen information and timestamp timezone are unresolved by the cached CSVs.
No field MODFLOW calibration, aquifer-property truth, logging interpretation or
cross-well spatial validation is inferred from this time-series test. Keep the
optional FloPy branch's separate solver/water-balance checks and limitations.
