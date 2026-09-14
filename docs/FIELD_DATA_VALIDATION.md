# Offline validation with real GNSS station data

This scenario uses 186 published GNSS station velocity estimates from the Alpine
region. It checks provenance, original-to-curated data conversion, weighted
trend fitting, spatial holdout, and conditional uncertainty propagation. The
observations are real; the simple planar model is deliberately inadequate and
must be reported as such. Passing these checks does not establish general
scientific validity for the skills, a regional deformation solution, or recovery
of a known subsurface model.

## Data and redistribution

The original data are Sánchez et al. (2018), *Present-day surface deformation of
the Alpine Region inferred from geodetic techniques (data)*,
[PANGAEA DOI 10.1594/PANGAEA.886889](https://doi.pangaea.de/10.1594/PANGAEA.886889),
licensed **CC BY 3.0**. They are observation-derived station solutions, not raw
GNSS receiver recordings. Fatiando's curated
[Alps GPS velocities v1](https://zenodo.org/records/5879163) is **CC BY 4.0** and
retains attribution to the original source. The curated CSV, three original
tables, and upstream license notice are vendored without modification: about
109 KiB in total. Third-party data keep these licenses; the repository's MIT
license does not replace them.

The fixed curation revision is
`123af5d44f4e872300c6eda5455f1fed8f9d5acf`. Every upstream file has its source URL,
byte length, and SHA256 in
[provenance.json](../tests/fixtures/field/alps_gps/provenance.json).
The compressed CSV's SHA256 is
`77f2907c2a019366e5f85de5aafcab2d0e90cc2c378171468a7705cab9938584`.
See [ATTRIBUTION.md](../tests/fixtures/field/alps_gps/ATTRIBUTION.md) for the
full attribution chain and license links.

## Units, coordinates, and reconstruction

| Quantity | Meaning retained from the sources |
|---|---|
| Longitude/latitude | Degrees, IGb08/ITRF2008, GRS80 ellipsoid |
| Reference epoch | 2010-01-01 00:00:00; not an observation timestamp shared by every record |
| Height | Ellipsoidal metres, not elevation above sea level |
| Horizontal velocity | East/north, relative to the Eurasian Plate |
| Vertical velocity | Height rate from the IGb08/ITRF2008 NEH solution |
| Velocity values/errors | Original m/year converted to mm/year |
| Position errors | Metres, including latitude and longitude errors |
| NULL handling | No numerical NULLs in the selected table; missing/nonfinite values and nonpositive errors fail loading |

No EPSG:4326 label or metric distance is inferred. The diagnostic uses centred
longitude and latitude as polynomial predictors in degrees. The resulting
slopes have units mm/year/degree and must not be interpreted as strain. A model
that uses distances or strains needs an appropriate geodetic treatment.

The [fixed upstream recipe](https://github.com/fatiando-data/alps-gps-velocity/blob/123af5d44f4e872300c6eda5455f1fed8f9d5acf/prepare.ipynb)
starts with the 186 Eurasia-relative stations. It corrects `CH1Z` to `CHIZ` and
`IE1G` to `IENG`, joins the first solution for each station from the coordinate
and vertical-velocity tables, converts velocities and their errors to mm/year,
normalizes source longitudes above 300 degrees, and rounds the published
columns. Later station solution segments are not averaged. Some original rows
omit the DOMES identifier; this does not represent a missing observation.

[field_support.py](../tests/science/field_support.py) independently rebuilds all
13 columns for every station from the original files and compares them exactly
to the curated values. It checks the two corrected station names against the
horizontal table's coordinate reporting precision. All 186
published rows are retained; no project-specific subsampling, imputation,
outlier removal, or target-based selection is performed. Reproduction compares
table values, because XZ bytes can depend on compressor versions.

The source audit also exposes two coordinate disagreements: `WTZR` and `ZIMM`
have maximum REP-versus-NEH differences of 0.0024111 and 0.0002781 degrees,
respectively. These exceed one REP reporting unit (0.0001 degree). This screen
does not imply that smaller differences are a validated coordinate error budget.
Both source files remain unchanged and the report lists these discrepancies.
The vertical diagnostic uses only NEH coordinates and NEH height rates;
horizontal station association needs source review before scientific use.

## Scientific acceptance and uncertainty limits

The real Verde `Trend(degree=1)` estimator fits the vertical component with
weights `1 / sig_Vh**2`. `sig_Vh` is taken from the same original NEH table as
the height rate. The tests check weighted residual orthogonality and full rank,
not just successful library calls. They also reject zero/missing errors and
unidentifiable station geometry.

The uncertainty calculation **conditionally** treats the reported `sig_Vh` as
one-standard-deviation, independent Gaussian errors with coordinates fixed.
The covariance of the three fitted coefficients is `(A.T W A)^-1`. The test
perturbs the real station values 512 times using a fixed random seed, refits
the real Verde estimator, and compares coefficient means and variances to
independent linear-algebra predictions. Six simultaneous mean/variance checks
use Bonferroni-adjusted Gaussian/chi-square bounds with total nominal false
failure probability at most 0.001. These perturbations are explicitly synthetic
noise experiments around real data, not additional field observations.

This conditional covariance does not include spatially correlated deformation,
interstation observation covariance, reference-frame/systematic error, or model
discrepancy. It is not total prediction uncertainty. The source study separates
trend, correlated signal, and noise in its scientific model; our planar
diagnostic does not reproduce that model.
[Sánchez et al., methods and Appendix A](https://essd.copernicus.org/articles/10/1503/2018/).

For supplied errors and three fitted parameters, the residual diagnostic is
`chi_square = sum(((observed - predicted) / sigma)**2)` with `186 - 3 = 183`
degrees of freedom. No residual-based error inflation is used. The test must
report rejection when this exceeds the nominal 99% chi-square threshold. This
rejects the *combined plane plus independent-error assumptions*; it does not
prove that the observations are bad or identify which omitted effect dominates.

Spatial evaluation holds out five fixed longitude strips with boundaries
0, 5, 10, and 15 degrees. Every station is predicted exactly once, with no
station from its strip in training. Edge strips include extrapolation, and
nearby stations across strip boundaries may remain correlated: this is not a
buffered independent validation design. A weighted-mean baseline is fitted
using only each training partition. Conditional holdout intervals include
coefficient variance and the held-out station error; coverage is descriptive,
without a binomial independence claim or parameter tuning on test observations.

Observed results with Verde 1.9.0 / NumPy 2.4.6 / SciPy 1.17.1:

| Diagnostic | Result | Interpretation |
|---|---:|---|
| In-sample chi-square | 2063.941 | Exceeds nominal 99% threshold 230.423 for 183 degrees of freedom |
| Spatial holdout RMSE | 0.8596 mm/year | Five fixed longitude strips |
| Training-only mean baseline RMSE | 0.8228 mm/year | The plane does not improve this holdout baseline |
| Conditional nominal 95% interval coverage | 63.98% | The noise-only intervals omit important variability |

Successful validation means the data lineage and computations agree and the
inadequate model is identified. It must not be presented as calibrated field
prediction accuracy. Geological interpretation, correlated-error models,
additional data types, and validated inversion recovery remain separate work.

## Reproduce offline

Use the isolated **modelling** environment from
[SCIENTIFIC_TESTING.md](SCIENTIFIC_TESTING.md); the core environment does not
include Verde. No network access, data downloader, credentials, user package
updates, or plotting display are needed after dependencies are installed.

```bash
MPLBACKEND=Agg python -m unittest discover -s tests/science -p test_field_data.py -v
MPLBACKEND=Agg python tests/science/field_support.py
```

Tests fail if dependencies are missing. They verify all recorded file hashes
before analysis, reproduce all table values, deliberately corrupt a temporary
fixture to confirm integrity rejection, exercise the real weighted estimator,
check spatial holdout isolation, and validate conditional error propagation.
To re-acquire source bytes, use the exact URLs in the provenance manifest and
verify their SHA256; test execution itself only reads the vendored files.
