---
name: climate-analysis
description: >-
  Analyse labelled climate time series and gridded or station observations with
  checked calendars, aggregation, climatological baselines and spatial validation.
  Use for climate anomalies, regional summaries or station-to-grid analysis;
  distinguish descriptive analysis from future-time prediction.
license: MIT
metadata:
  version: "1.0.1"
  author: Geoscience Skills
  skill_type: workflow
  tags: '["Climate", "Time Series", "Spatial Analysis", "Validation"]'
  dependencies: '["xarray", "numpy", "pandas", "cftime", "verde", "pyproj", "scipy"]'
  complements: '["xarray", "verde", "pooch"]'
  workflow_role: analysis
---

# Climate Analysis

Use `xarray` for labelled climate arrays and `verde` only when scattered spatial
observations need interpolation. Existing regular grids do not require a new
interpolation stage. Run the relevant stages in one agent; companion skills are
helpful references rather than mandatory registrations.

## Define the data contract

Identify the variable, physical units, spatial support, timestamp meaning,
calendar, time bounds, missing-value encoding and source/version before combining
files. Check coordinate uniqueness and order, longitude convention, latitude
direction, projection, vertical level and ensemble/member dimensions. Preserve
non-Gregorian calendars; do not silently coerce them into ordinary timestamps.

Distinguish an instantaneous value, interval mean, accumulated amount and rate.
For precipitation or energy fluxes, use the time bounds and unit definition to
decide integration or summation. Do not apply the same resampling operation to
temperature means and accumulated rainfall. Record source URLs, licences and
checksums; use the `pooch` skill only when downloading is actually requested.

## Select the analysis

| Deliverable | Main steps | Validation partition |
| --- | --- | --- |
| Climatology/anomalies | Specify baseline years, calendar grouping, coverage and weights | Document baseline overlap; no forecasting claim from descriptive anomalies |
| Regional averages | Use cell areas or justified spatial weights and a fixed mask | Check missing coverage and area/weight normalisation for each period |
| Station-to-grid product | Project coordinates appropriately, fit a spatial model, mask unsupported regions | Withhold spatial blocks or stations before fitting any preprocessing |
| Forecast/downscaling evaluation | Define issue time, lead time and predictor availability, then fit | Withhold future time periods and unseen locations as required by deployment |

## Aggregate without losing meaning

Choose an explicit coverage rule for incomplete months/seasons and retain a
coverage/count variable. Weight monthly means by represented duration, respecting
the dataset's calendar; the [xarray seasonal-mean example](https://docs.xarray.dev/en/stable/examples/monthly-means.html)
illustrates calendar-aware weighting. Renormalise over valid support only when
that matches the stated estimand; never turn an entirely missing region or
period into a zero observation.

Use supplied cell areas for irregular/projected grids. Cosine-latitude weights
are an approximation for suitable regular longitude/latitude grids, not a
general area calculation. Define whether December belongs to the following
winter year before grouping DJF; a long-term seasonal climatology and a sequence
of individual seasonal means are different outputs.

For anomalies, record baseline years and grouping. In prediction experiments,
estimate climatology, trends, scaling, missing-value models and bias corrections
using training data only. Do not allow centred windows, filled gaps or target
aggregation windows to reach into future observations unavailable at issue time.

## Spatial modelling and validation

For station observations, retain station identifiers and repeated-observation
groups. Use a distance-appropriate CRS for a regional planar model; do not feed
unqualified geographic degrees into metre-scale block sizes. Fit trends,
normalisation, hyperparameters and interpolation within each training fold.

Use [Verde spatial block validation](https://www.fatiando.org/verde/latest/api/generated/verde.BlockKFold.html)
when evaluating interpolation away from measured stations. Choose block size
and any buffer from spatial support/dependence and the intended deployment;
randomly splitting neighbouring samples can overstate performance. For future
predictions, also hold out contiguous time periods. A station appearing in both
sets may still be valid for a same-station forecast, but does not test an unseen
location; state which question the split answers.

## Outputs and uncertainty

Export a labelled dataset retaining units, calendar, CRS, baseline, masks and
coverage, plus a record of processing choices and package versions. Reopen the
output and check coordinates, dimensions and selected analytical summaries.
Report errors by location/season and against a suitable climatology or persistence
baseline. Account for temporal/spatial dependence when estimating uncertainty;
model spread is not automatically a calibrated predictive interval, and trend
significance is not causal attribution.

## Executed station case

The [NOAA station example](references/validated-station-case.md) executes the
workflow from real daily maximum temperatures through QC, calendar-aware means,
short-reference anomalies, spatial holdout and a labelled NetCDF export. Its
[offline script](scripts/station_pipeline.py) requires the recorded source and
provenance files and preserves existing output directories.

The example separates each station's descriptive anomaly from a spatial model
relative to a station-network reference. Every spatial fold learns that reference
from training stations alone; the held-out station's past values are also excluded.
The final grid contains model estimates, with a recorded support mask and spherical
cell areas. A regional model mean is not a measured regional climate change.

Tests also cover synthetic `360_day`/`noleap` calendars, missing coverage and
all-NaN periods/regions. This verification does not establish forecasts,
30-year climate normals, homogenization, precipitation integration or arbitrary
regridding accuracy. Use a data-specific validation for those branches.
