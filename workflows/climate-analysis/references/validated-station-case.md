# NOAA daily maximum temperature case

Use this example for a complete, inspectable station-analysis path. It is a
small fixed case, not a general climate-normal calculation.

The project fixture contains the complete NOAA NCEI GHCN-Daily API response for
twelve Northeast/Mid-Atlantic US stations, 2018–2020, requested with metric units
and source attributes. The source variable is **daily maximum temperature**.
Monthly means therefore summarize daily maxima, not daily mean temperature.

Obtain `ghcnd-tmax-2018-2020.csv.gz` and `provenance.json` from the full project's
`tests/fixtures/workflows/climate/` directory. These test data are not installed
automatically with the skill. Their data-level CC0 evidence, original and gzip
hashes, station selection and exact API query are recorded beside the fixture.
Use the isolated Python 3.12 pins in the project's
`tests/science/requirements-climate-workflow.txt`.

Run the script relative to this skill's directory, with explicit data locations:

```bash
python /path/to/climate-analysis/scripts/station_pipeline.py \
  --source /path/to/ghcnd-tmax-2018-2020.csv.gz \
  --provenance /path/to/provenance.json \
  --output /path/to/new-output-directory
```

The script performs no downloads. A populated output directory is rejected.
Completion means both `climate-workflow.nc` and `report.json` exist and the
NetCDF has been reopened and compared with the in-memory product.

## Interpretation decisions

- Convert metric API Celsius values to kelvin; preserve original attributes and
  a separate raw converted array. An empty quality flag passes source QA; it
  does not prove an error-free instrument. Mask nonempty quality flags and missing
  observations without filling them. The actual snapshot has neither defect;
  tests exercise these paths on explicitly altered in-memory copies.
- Dates label observing days. The source does not supply exact UTC observation
  intervals. Weights count represented **calendar days**, not measured SI-second
  exposure. A month requires 90% coverage; later weights use accepted days and
  retain coverage. A period with no support remains NaN.
- Set the 2018–2019 monthly reference and 2020 evaluation before fitting. This
  short reference is not a 30-year normal. Each station's own reference anomaly
  is a descriptive output only.
- For spatial testing, use three longitude strips separated at −77° and −74°.
  Recompute the station-network reference from training stations in each fold,
  then fit a fixed first-degree Verde trend to training 2020 anomalies. Compare
  with the training-only constant. No station value from any held-out year
  enters the fit; no parameters are tuned to the reported error.
- Station coordinates have no named datum in this CSV. WGS84 is an explicit
  working assumption for a local azimuthal-equidistant projection; it is not a
  newly established datum. Elevation and station-history effects are not fitted.
- The final grid is a model prediction. Its fixed support admits only cells
  whose four projected corners lie inside the station convex hull; this discrete
  rule does not trace curved geographic cell edges. Cell areas use explicit
  latitude/longitude bounds on a sphere of radius 6,371,008.8 m. The area mean is
  a cell-centre quadrature over supported model cells, not observed regional truth.

The repository's `docs/CLIMATE_WORKFLOW_VALIDATION.md` records numerical results,
dependency versions and independent checks. Future-time prediction, calibrated
uncertainty, homogenization and a standard climate-normal product are outside
this example's validation scope.
