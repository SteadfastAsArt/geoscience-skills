# Climate workflow validation

The `climate-analysis` workflow now has an executed path from real NOAA station
observations to checked aggregation, descriptive anomalies, spatial holdout,
model-grid area summaries and a reopened NetCDF file. Fourteen offline tests
exercise the actual xarray/cftime, Verde and pyproj implementations. This
validates a small fixed case, not every climate workflow branch.

## Observations and source contract

The fixture contains the complete NCEI access-service response for twelve
preselected Northeast/Mid-Atlantic US stations, daily **TMAX**, 2018–2020:
13,152 rows and 1,491,604 original CSV bytes, compressed losslessly to 60,144
bytes. The source is
[GHCN-Daily Version 3, DOI 10.7289/V5D21VHZ](https://doi.org/10.7289/V5D21VHZ).
The [US government dataset catalog](https://catalog.data.gov/dataset/global-historical-climatology-network-daily-ghcn-daily-version-3)
specifies data-level [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).
Attribution and the exact query, selection, compression and SHA256 records are
in the [fixture provenance](../tests/fixtures/workflows/climate/provenance.json).
The original decompressed CSV hash is
`8f3c60133f21efb7936d72d2850fd0c90bbe4e8138e2f857ed8fba024ffef1d3`.

The API explicitly requests `units=metric`, `dataTypes=TMAX`, station locations
and attributes. These temperature values are Celsius, unlike raw GHCN `.dly`
tenths of Celsius. The script adds 273.15 to produce kelvin and preserves both
raw converted and quality-masked values. **A mean of daily maximum temperatures
is not daily mean air temperature.**
[NCEI API documentation](https://www.ncei.noaa.gov/support/access-data-service-api-user-documentation),
[GHCN field and flag definitions](https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt).

All returned attributes are `,,W`: empty measurement and quality flags, with
WBAN/ASOS summary-of-day source code W. No observation-time attribute is present.
Dates are observing-date labels; exact UTC observation intervals are unknown.
Calendar-day weighting therefore counts represented observing days, not measured
SI-second exposure. No timezone, midnight UTC acquisition or observation-hour
correction is invented. The actual snapshot has no missing TMAX or failed quality
flags. Tests apply clearly labelled in-memory faults to exercise those paths;
the stored source bytes remain unchanged.

The CSV supplies latitude/longitude in degrees and elevation in metres without
an explicit datum. WGS84 is a declared working assumption for a local
azimuthal-equidistant fit centred at 41.5° N, 75° W. Coordinates are transformed
with `always_xy=True`; metre coordinates enter Verde. This does not establish
the actual source datum, station-history stability or elevation corrections.
The official station inventory describes the most recent station location;
historic station moves are outside this demonstration.

## Temporal aggregation and reference periods

The dates are retained as proleptic-Gregorian `cftime` objects. Monthly means
require at least 90% valid observing days. Counts and coverage remain in the
export; rejected months stay NaN. Later means weight each accepted month by
its represented valid-day count, while coverage uses all expected calendar days.
All-missing periods never become zero. Independent tests verify 29-day February
2020 and compare every month with a separate standard-library CSV reader.

The 2018–2019 reference and 2020 evaluation were fixed before fitting. The export
distinguishes two quantities:

- `station_local_annual_anomaly`: each station's duration-weighted 2020 departure
  from its own 2018–2019 monthly reference. This is descriptive and never enters
  the spatial holdout calculation.
- `station_annual_anomaly` and `model_anomaly`: departures from a common monthly
  station-network reference. The final product estimates this reference from
  all twelve stations in 2018–2019. A network-reference departure includes
  between-station climatological differences; it is not each location's
  temporal change.

This two-year reference is deliberately short and **not a 30-year climate
normal**. Changing 2020 values cannot affect reference values. The source is not
homogenized here; station moves, urban effects, elevation dependence and long-term
trends are not estimated.

## Spatial fit, validation and area meaning

Three predeclared longitude strips have boundaries −77° and −74°, yielding
holdout sizes 4, 2 and 6. Each station is withheld once. Each fold recalculates
the 2018–2019 network reference using only training stations, then fits a fixed
degree-one `verde.Trend` to training 2020 station anomalies. The comparison
constant also uses training data only. The report records training/held-out
station IDs, the twelve fitted reference values, predictions and target values.

The leakage test changes **all years** of held-out station values by +80 K and
requires identical reference, coefficients, predictions and comparison constant.
A separate NumPy least-squares solution must reproduce actual Verde predictions.
No model degree, reference period or block boundaries are tuned to these errors.
Some folds extrapolate at the regional edges. They share year and region and
have no spatial buffer; error values are descriptive, without an independence
or confidence-interval claim.

The final grid is produced from a model fitted to all twelve stations. It is
explicitly labelled a **model estimate**, not a resampled observation grid.
Its 0.25° cells are retained only when all four projected corners lie inside
the station convex hull. This is a discrete support rule; curved geographic
cell edges are not traced. Unsupported cells remain NaN.

Cell areas are computed from latitude/longitude bounds as
`R² Δlongitude (sin(latitude_north) - sin(latitude_south))`, with radians and
the declared spherical radius 6,371,008.8 m. This is exact on that sphere, not
an ellipsoidal geoid area. Independent numerical quadrature and the global
`4πR²` identity verify the formula. Area weighting uses a fixed model-support
mask and tracks valid area; missing coverage and all-NaN regions are tested
separately. The regional mean is cell-centre quadrature over supported model
cells. **The support area is not measured observational coverage**, and the
regional model anomaly is not known regional climate truth.

## Recorded result and export

The [machine-readable result](../tests/fixtures/workflows/climate/recorded-report.json)
records the source hash, script hash, protocol version, complete fold membership,
actual library versions and generated NetCDF SHA256.

| Diagnostic | Observed result | Meaning |
| --- | ---: | --- |
| Spatial holdout RMSE | 1.18518 K | Unseen station network-reference anomalies |
| Training-only constant RMSE | 2.36064 K | Same folds and targets |
| Supported model cells | 423 | All-corners convex-hull criterion |
| Supported model area | 243,200.81 km² | Spherical cell area, not observation coverage |
| Regional model anomaly | 0.588512 K | Relative to the short station-network reference |

The NetCDF retains original observing dates, raw/accepted temperatures and
source flags, monthly counts and coverage, both kinds of reference/anomaly,
station IDs and locations, projection/datum assumptions, cell bounds/areas,
support masks and source/license metadata. Actual xarray reopening compares all
arrays with the in-memory product, then tests calendar, units, CRS, reference
period and NaN support explicitly. Byte hashes record this execution; other
library/platform encoders may write different bytes and must pass the numerical
and metadata checks instead of being mistaken for changed observations.

Separate synthetic `360_day` and `noleap` examples verify duration weighting
against known month lengths and preserve their calendars through NetCDF
write/read. They are not relabelled as NOAA calendar observations.

## Reproduce offline

Use a new Python 3.12 environment; this case has a separate
[requirements file](../tests/science/requirements-climate-workflow.txt). It does
not require a display, credentials, a download service or global package updates.

```bash
python3.12 -m venv /path/to/new-climate-venv
/path/to/new-climate-venv/bin/python -m pip install -r tests/science/requirements-climate-workflow.txt
/path/to/new-climate-venv/bin/python tests/science/test_climate_workflow.py -v
/path/to/new-climate-venv/bin/python workflows/climate-analysis/scripts/station_pipeline.py \
  --source tests/fixtures/workflows/climate/ghcnd-tmax-2018-2020.csv.gz \
  --provenance tests/fixtures/workflows/climate/provenance.json \
  --output /path/to/new-climate-results
```

Dependencies are mandatory; absent packages fail instead of skipping tests.
The workflow refuses a populated output directory. CI can run the test file
directly or discover only `test_climate_workflow.py` in `tests/science`.

Forecasting, precipitation/rate integration, homogenization, standard climate
normals, arbitrary regridding and calibrated predictive uncertainty remain
outside the executed scope. This case validates its stated transformations and
model diagnostics, without claiming independent climate truth.
