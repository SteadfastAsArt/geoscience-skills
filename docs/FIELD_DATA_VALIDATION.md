# Offline validation with published field data

The repository includes four licensed field-data cases. Their observations or
published observational solutions are real. Controlled perturbations and the
ERT recovery model are labelled synthetic and checked separately. Each case
verifies the vendored source hashes before analysis; passing a case validates
its stated computations and diagnostic boundaries, not all scientific uses of
a library or skill. Third-party data retain their own licenses.

| Case | Actual library path | Checks | Environment |
|---|---|---:|---|
| Alpine GNSS station solutions | Verde weighted trend and holdout | 10 | Modelling |
| FDB-1 measured wireline logs | lasio conversion and readback | 7 | Core |
| GE.MATE recorded waveform | ObsPy miniSEED and instrument response | 7 | Core |
| Crescentino electrical survey | pyGIMLi geometry, VES fitting and controlled recovery | 7 | Modelling |

## Alpine GNSS station solutions

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

## FDB-1 wireline logs: source-preserving LAS conversion

Shibutani and Lin (2021), *Wireline logging data from Hole FDB-1 penetrated
throughof the Futagawa fault, SW Japan*, provides actual borehole measurements
under **CC BY 4.0**, explicitly stated in the
[PANGAEA data record](https://doi.pangaea.de/10.1594/PANGAEA.933467).
The complete published text table is retained, including its attribution,
metadata and remarks: 298,754 bytes, 3,646 rows, SHA256
`1834fbb42939f03c54ec3869d02ef3bbcca84f7c142f7ff182436809366e89d7`.
The exact text-export URL and release information are in
[well provenance](../tests/fixtures/field/well_logs/provenance.json).

This case creates a labelled LAS 2 conversion with actual lasio; the source was
a text table, not an instrument LAS file. It preserves all 3,508 rows with a
published depth. The other 138 rows remain in the original table; their missing
depths are not reconstructed from a nominal sampling increment. Source empty
numeric fields become NaN and LAS `NULL=-999.25`. `STEP=0` retains the resulting
irregular depth sequence without resampling. A source-row curve and a separate
sonic-remark flag retain traceability; all original remark text remains in the
vendored table. A remark does not automatically mean a faulty measurement.

| Quantity | Retained meaning or explicit conversion |
|---|---|
| Depth | Original borehole depth in m; no TVD or elevation conversion |
| Location | 32.8062° latitude, 130.8601° longitude; source does not name a horizontal CRS |
| Vertical datum | Not explicitly supplied; no invented sea-level datum |
| Sonic velocity | Published km/s multiplied by 1,000 to produce VP in m/s |
| Derived sonic slowness | `DT_us_ft = 304800 / VP_m_s`; derived, not separately measured |
| Calipers, temperature, gamma | mm, °C, API units |

An independent standard-library CSV reader checks every exported caliper,
temperature and gamma value, depth and source-row identity after actual LAS
write/read. Sonic unit checks use the exact
international-foot definition, 0.3048 m. For a separate interval diagnostic,
only consecutive source samples 0.1 m apart with positive finite velocity and
no sonic remark contribute to trapezoidal slowness integration. No missing or
remarked interval is bridged. This assumes local sonic velocity along the
published depth coordinate; it is not an observed seismic travel time, a
complete surface-to-depth time curve, or a calibrated seismic well tie.

The accepted 3,126 intervals cover 312.6 m, with summed one-way interval time
0.1120428203 s. Independent velocity extrema bound each interval's integral.
The source's five decimal places in km/s provide a **quantization-only**
velocity half-increment of 0.005 m/s; propagating it bounds the sum between
0.1120426115 and 0.1120430292 s. The source supplies no per-sample measurement
errors, so these bounds are not total accuracy or confidence intervals.

Every fifth original row is reserved before interpolation. Only held-out
samples bracketed by valid immediate 0.1 m neighbours are scored, and a held-out
target cannot be used in its predictor. The 621 eligible predictions have RMSE
35.9729 m/s. This describes local interpolation on a densely sampled log,
not independent geological prediction. Tests additionally reject duplicated
depths and verify that gaps and flags survive conversion.

Run offline in the **core** environment:

```bash
MPLBACKEND=Agg python -m unittest discover -s tests/science -p test_field_well_logs.py -v
MPLBACKEND=Agg python tests/science/field_well_log_support.py
```

## GE.MATE waveform: timestamps and physical response

The real `GE.MATE..BHZ` channel snapshot comes from the GEOFON Seismic Network,
GEOFON Data Centre (1993), DOI **10.14470/TR560404**. Redistribution is permitted
by the network's explicit **CC BY 4.0**
[data-license notice](https://geofon.gfz.de/waveform/archive/network.php?ncode=GE).
This claim concerns the GE data release, not a software or website license.
The original miniSEED and StationXML responses total 39,732 bytes; exact FDSN
query URLs, both SHA256 values and retrieval date are recorded in
[waveform provenance](../tests/fixtures/field/seismic_waveform/provenance.json).
They are pinned snapshots: an FDSN service is not an immutable repository
revision, and a fresh StationXML response may have a new `Created` timestamp or
revised metadata even when the query is identical.

The 2016-08-24 01:35–01:40 UTC query returns whole archive records: 6,047 integer
samples at 20 Hz, beginning **01:34:57.895 UTC**. A contained crop must preserve
the real 0.05 s phase; its first sample after 01:35:00 is 01:35:00.045, not the
requested boundary. Independent integer-nanosecond arithmetic checks this
against ObsPy trimming, and a miniSEED round trip preserves all sample values
and original timing. Gaps, masks and requests beyond observed data are rejected.

StationXML identifies latitude 40.64907°, longitude 16.70442°, elevation 494 m
above sea level, channel depth 5 m below the local surface, azimuth 0° and dip
−90°. The absent datum attribute uses the StationXML **WGS84 default**;
no projected CRS is inferred. The standard specifies latitude/longitude in
degrees and times in UTC.
[FDSN StationXML reference](https://docs.fdsn.org/projects/stationxml/en/latest/reference.html).
The source supplies no named geoid realization or position-error budget.

The waveform is digital counts. Actual ObsPy full response removal requests
velocity in m/s, a fixed `(0.05, 0.1, 4, 5)` Hz prefilter, mean removal, a 5%
cosine taper and no water-level clipping. The sensor input/output units and
overall sensitivity are checked from independently parsed XML. An independent
complex pole-zero formula checks the sensor stage against ObsPy evaluation;
this is a stage-specific check, not an independently calibrated replacement
for the complete response chain. Separately, the one-sided periodogram obeys
the discrete Parseval energy identity for the recorded samples.

Instrument-corrected RMS for the fixed 01:35:10–01:36:10 window is
`3.78959e-7 m/s`; for 01:37:00–01:38:00 it is `2.04027e-5 m/s`.
These are descriptive band-limited amplitudes. The fixture does not supply a
complete amplitude or timing uncertainty model, event catalogue or labelled
arrival. It validates neither an event identification nor source inversion;
endpoint transients and out-of-band motion are outside the claimed scope.

Run offline in the **core** environment:

```bash
MPLBACKEND=Agg python -m unittest discover -s tests/science -p test_field_seismic_waveform.py -v
MPLBACKEND=Agg python tests/science/field_waveform_support.py
```

## Crescentino electrical survey: fit, holdout and separate recovery

Vergnano, Comina, Socco, Chieppa and Arato's *Database of a 4-km seismic and
electric streamer survey: the embankment of the Po River near Crescentino,
Piedmont, Italy*, version 1, includes actual electrical measurements acquired
in March 2025. The fixed
[Zenodo record, DOI 10.5281/zenodo.18183049](https://zenodo.org/records/18183049)
and its [API metadata](https://zenodo.org/api/records/18183049) assign
**CC BY 4.0**. The narrative's less specific "No restriction" statement is not
treated as a public-domain dedication.

The 2,331,221-byte `Electrical_Tomography_Data.7z` source archive has SHA256
`d7257a1d24a3f52e0f807739f1b23e975bbb32561091abf9cb87b5b412051891`.
Its complete measurement and electrode-position CSV members are preserved as
two gzip files, about 2.84 MiB combined. Extraction does not change CSV bytes,
column order, decimal precision or line endings; `gzip.compress(bytes, mtime=0)`
only changes their container. Both compressed and decompressed hashes,
archive-member names, source URL and upstream checksum are recorded in
[ERT provenance](../tests/fixtures/field/ert_survey/provenance.json).
Offline tests need no archive extractor or download service. Rebuilding gzip
with another zlib version may change compressed bytes; verify the recorded
decompressed hashes before treating such a difference as changed source data.

The full CSVs contain 164,724 measurements and 6,734 electrode positions. The
small computational case selects **the first acquisition station**, its first
318 measurements and 13 electrode IDs, before fitting. Published units are
apparent resistivity in Ω m, potential difference in mV, current in mA, and
instrument repeatability standard deviation in percent. Surveyed horizontal
coordinates are metres in **EPSG:32632**, as explicitly named in the CSV header;
the source provides no electrode elevations in that table. The self-potential
column is not used because the source warns about its acquisition limitations.

The instrument's nominal linear electrode positions are
`[0, 8, 14, 18, 20, 22, 24, 26, 28, 30, 34, 40, 48]` m.
An independent 3D surface point-electrode formula computes signed geometric
factors and verifies `rhoa = K * V_mV / I_mA` within the source's decimal-rounding
bounds. This also checks the mV/mA cancellation and electrode orientation.
Actual `pygimli.DataContainerERT` conversion preserves the signed resistance
and converts source one-based IDs to library zero-based indices; library
geometric factors agree with the independent formula. Negative voltage alone
does not cause rejection: 239 such values remain in the positive-resistivity
fit. The two nonpositive apparent resistivities remain in the source and are
excluded only from the log-domain inversion.

The declared diagnostic is a flat, isotropic two-layer earth with positive
thickness and resistivities, fitted by actual pyGIMLi `VESModelling` and
log-domain inversion with no regularization (`lam=0`). It uses nominal
instrument geometry, not a fabricated zero-elevation georeferenced surface.
The surveyed endpoint distance is 47.3256 m versus the nominal 48 m; this
simplification, unknown elevation, and potential lateral structure constrain
interpretation.

For fitting, log-error sigma is assigned as
`hypot(reported_repeatability_percent / 100, 0.03)`. The additional log-scale
term is an explicit assumption; the 64 source values with zero repeatability
do not imply zero total error. Conditional independent Gaussian log errors and
three fitted parameters yield the nominal diagnostic
`sum(((log(predicted) - log(observed)) / sigma)**2)` with `316 - 3 = 313`
degrees of freedom. This nonlinear-model chi-square reference is approximate;
it is not a measured complete field uncertainty model. No residual-based error
inflation is applied to force acceptance.

A separate SciPy local least-squares refinement of the same pyGIMLi response
must converge, retain a Jacobian of rank three, and change the objective by less
than 0.1%. It still fails the fit criterion. This checks local convergence and
identifiability; it does not prove a global optimum or uniqueness.

| Real-data diagnostic | Observed result | Boundary |
|---|---:|---|
| Fitted thickness, top/bottom resistivity | 4.91485 m, 313.344 / 37.4798 Ω m | Diagnostic parameters; no known field ground truth |
| Conditional chi-square | 15000.224 | Far above nominal 99% threshold 374.128; combined model/error assumptions rejected |
| Geometry-group holdout | 74 measurements | Current/potential reversals and reciprocal pairs remain in the same split |
| Holdout log RMSE | 0.23424 | Better than training-only log-mean baseline 0.57957 |

The fixed holdout hashes canonical quadrupole geometry, never target values.
Training fits and the baseline use only training measurements. It still shares
electrodes and an acquisition station with training, so it is not an independent
survey or evidence of geological recovery. A lower holdout error does not
override the failed conditional model-fit diagnostic or identify which omitted
physical/error source is responsible.

A **separate controlled synthetic recovery** uses an independently implemented
two-layer image-source series for thickness 5 m, top resistivity 100 Ω m and
bottom resistivity 300 Ω m. Its reflection coefficient is 0.5. Agreement between
80 and 160 terms checks truncation; agreement with pyGIMLi at relative tolerance
`1e-7` checks the forward response, and the homogeneous limit returns its known
resistivity. Fixed-seed lognormal noise with log sigma 0.02 is added only to
these synthetic values. Inversion starts from a different model and must recover
all three parameters within 5%, with residual statistic inside the nominal
99% chi-square interval. These generated values never replace the real survey.
This one geometry/contrast/noise case does not establish uniqueness, resolution
or recovery for arbitrary heterogeneous field models.

Run offline in the **modelling** environment:

```bash
MPLBACKEND=Agg python -m unittest discover -s tests/science -p test_field_ert_survey.py -v
MPLBACKEND=Agg python tests/science/field_ert_support.py
```

The observed new-case results above use lasio 0.32, ObsPy 1.5.1 and pyGIMLi
1.6.0 with the isolated environments described in
[SCIENTIFIC_TESTING.md](SCIENTIFIC_TESTING.md). Their 21 tests fail when required
dependencies are unavailable. Acquisition, licensing and scientific boundaries
are also retained next to each fixture in its `ATTRIBUTION.md` and provenance
manifest.
