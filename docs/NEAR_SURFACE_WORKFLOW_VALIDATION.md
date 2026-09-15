# Near-surface workflow: three independent import-to-export cases

The [workflow](../workflows/near-surface-geophysics/SKILL.md) has separate
executed GPR, ERT and MT branches. **25 tests** exercise actual readers,
processing/inversion APIs and reopened output products: 9 GPR, 8 ERT, 8 MT.
Dependencies are required; missing libraries fail rather than skip validation.
The cases represent different surveys. They do not form a co-located
multi-method experiment or support a joint geological interpretation.

| Branch | Input → actual computation → output | Scope |
|---|---|---|
| GPR | Observed SEG-Y via segyio → GPRPy sample-index processing → NPZ/JSON readback; independent generated native MALA case | Field amplitude/order preservation; separately verified ns/m and scenario depth |
| ERT | Existing licensed Crescentino observations → pyGIMLi two-layer fit, response, residual and grouped holdout → CSV/JSON readback | Explicit flat diagnostic; field model/error assumptions fail the nominal fit criterion |
| MT | Upstream field-derived direct-impedance EDI → MTpy-v2 masks, QC and requested rotation → CSV/JSON/PNG and complete-data EDI readback | Transfer-function processing; independent tensor/impedance algebra |

## GPR observations, source and missing physical calibration

Famiglietti, Gragnaniello, Memmolo, Migliazza, Ritrovato and Vicari (2026),
*Low-Frequency Ground Penetrating Radar (GPR) Dataset Acquired via Ground-Based
and UAV Platforms*, version 1.0, is distributed under **CC BY 4.0** by its
[Zenodo data record](https://zenodo.org/records/18769571).
The exact API response containing `metadata.license.id = cc-by-4.0` is retained
next to the fixture for offline review. This is a dataset license, independent
of the processing software's license.

The complete original `Site_2/ground_cart/p1_75 (1).SGY` member was extracted
without modification from `Site_2.zip`. It has **694,992 bytes**, **312 traces**
and **494 samples per trace**, SHA256
`65a5ab409365aa431fd8d725b5741cf384c778029c18f12d3bb62a500a9c2829`.
The fixed archive URL, release version, archive/member hashes, upstream reader
revision and attribution are recorded in
[GPR provenance](../tests/fixtures/workflows/near_surface/gpr/provenance.json)
and [attribution](../tests/fixtures/workflows/near_surface/gpr/ATTRIBUTION.md).
No trace subset, UAV pairing, padding, coordinate perturbation or resampling
was performed.

The SEG-Y text header is blank. Binary and trace sample intervals both encode
293, but the release and pinned author reader do not establish the radar vendor's
physical time scaling. The trace coordinate-unit code is 0. We preserve those
encoded fields, coordinate scalars, source coordinates and sample/trace order;
we **do not assign ns, µs, metres, an EPSG code or a depth**. Zero amplitudes
remain valid readings, not a guessed NULL marker. Source digital amplitude units
are uncalibrated, and no complete amplitude/timing error model is supplied.
The [sampling sidecar](../tests/fixtures/workflows/near_surface/gpr/field_sampling.json)
records these unknowns explicitly. A supplied gain/depth operation fails while
physical time remains unresolved.

The actual field route uses segyio to decode the raw SEG-Y, then a real
GPRPy profile to subtract each trace's DC mean with a 494-sample dewow argument.
An independent standard-library binary decoder checks **every original int32
sample**, with NumPy checking the resulting mean-removal identity. This is a
reproducible processing diagnostic, not evidence that every removed component
was instrument noise or that field reflectors have known depths.

The [GPR helper](../gprpy/scripts/process_gpr.py) exports `profile.npz` and
`processing.json`. The archive preserves raw and requested intermediate arrays,
processed amplitudes, indices, available physical axes and selected encoded
headers; JSON preserves source/sidecar hashes, operations, version, units and
scope. Reopening uses `allow_pickle=False` and verifies the output checksum.
Existing output directories and corrupt exports fail. CLI failures cannot be
reported as successful requested exports.

## GPR controlled raw-format and formula tests

A separate [project-owned generator](../tests/fixtures/workflows/near_surface/gpr/generate.py)
writes genuine MALA-layout `.rad/.rd3` bytes using Python `struct`, independent
of the reader: 64 samples, 9 traces, 2.5 ns interval, 0.25 m spacing, local
zero-offset geometry and a known impulse at sample 32. These are explicitly
**synthetic**, not additional measurements from the field line.

GPRPy's native import must preserve all values, order and declared coordinates.
After DC removal, the known impulse remains at 80 ns; a separately declared
0.1 m/ns zero-offset scenario yields 4 m because the recorded time is two-way.
Independent convolution checks the interior dewow kernel; a window argument of
4 actually uses five interior samples in the pinned implementation. Special
edge behaviour is reported instead of claimed identical to the interior.
Full-profile background subtraction and time-power gain are checked against
their numerical invariants and retained as separate intermediate products.
Both change amplitude interpretation; no default attenuation compensation,
velocity estimation, migration or automatic interpretation is claimed.

The revised GPR skill removes nonexistent filter/SEG-Y/ASCII APIs and the
incorrect CMP class. It corrects sample versus ns windows and documents native
GPRPy `.gpr` files as pickle sessions, not a MALA vendor format.

## ERT observations through response and residual delivery

This branch reuses the existing **CC BY 4.0** Crescentino electrical survey,
[Zenodo 18183049 version 1](https://zenodo.org/records/18183049), with its
[original fixture provenance](../tests/fixtures/field/ert_survey/provenance.json).
The [field validation guide](FIELD_DATA_VALIDATION.md#crescentino-electrical-survey-fit-holdout-and-separate-recovery)
records archive hashes, signed voltage/current units, electrode positions,
source repeatability and limitations. No third-party bytes or license are
replaced for this workflow.

The [input preparation](../tests/science/near_surface_ert_support.py) verifies
original hashes, selects the first 318 acquisition records by index, renames
columns and retains measured values and source columns. Nominal positions use
metres along the original instrument line. The measured horizontal coordinates
are EPSG:32632 and the source supplies no elevations; the workflow explicitly
uses nominal flat geometry instead of inventing a georeferenced flat surface.
The input/output CSV parsers use round-trip float parsing where needed to
preserve the observed numerical values across normalization and export.

The [ERT helper](../workflows/near-surface-geophysics/scripts/ert_layered_diagnostic.py)
executes real pyGIMLi `VESModelling` with arbitrary four-electrode distances,
positive thickness/resistivities, log data/model transforms, a fixed starting
model and `lam=0`. It is a **flat, isotropic two-layer diagnostic**, not a 2D/3D
ERT tomogram. Two nonpositive apparent resistivities are retained in output
with exclusion reasons and missing predictions; negative voltages alone are
not rejected. The remaining 316 values receive
`log_sigma = hypot(repeatability_pct/100, 0.03)` by explicit assumption.
Reported zero repeatability does not imply perfect measurement accuracy.

`responses.csv` contains all 318 measurement identities and source columns,
inclusion/reason fields, predicted apparent resistivity, normalized log
residual, uncertainty, reciprocal group and holdout prediction where applicable.
`electrodes.csv` retains input nominal positions; `inversion.json` records
source/output hashes, units, assumptions, starting/fitted/training-only models,
chi-square and local convergence/rank diagnostics. Tests reopen these products
and independently reconstruct residuals and their squared sum. The saved model
must regenerate the saved forward response through the actual library.

The fixed geometry-only holdout keeps reciprocal/pair-reversed quadrupoles
together: **74 measurements held out**, **242 used for training**. Changing all
held-out target values by a factor of 1.3 must leave the training-only model
and its held-out predictions unchanged. This additional test checks leakage
through actual recomputation, not just partition labels. The holdout still
shares electrodes and an acquisition station with training.

The three-parameter fit is locally identifiable and stable under an independent
SciPy refinement. Its chi-square is about **15,000**, far above the conditional
99% reference **374.128** for 313 degrees of freedom. The report explicitly
rejects the combined model/error assumptions. Holdout log RMSE is about
**0.234**, versus **0.580** for a training-only log-mean baseline. Improving that
baseline does not undo the failed fit criterion or establish underground truth.
The nominal chi-square interpretation assumes independent Gaussian log errors
and is approximate for this nonlinear model; local checks do not prove global
uniqueness, resolution or total field uncertainty.

A separate controlled recovery test uses an independent converged two-layer
image-source series on the acquisition geometry. The known model is 5 m,
100 Ω m above 300 Ω m, with fixed-seed lognormal noise of log sigma 0.02 and a
different starting model. Actual inversion must recover each parameter within
5%, with a residual statistic inside the nominal 99% chi-square interval.
Synthetic targets are never relabelled as recovered field structure.

## MT transfer functions, units, rotations and missingness

The [MT fixture](../tests/fixtures/workflows/near_surface/mt/ATTRIBUTION.md) is
the field-derived `14-IEB0537A` upstream EDI regression sample from
mt-metadata, pinned to commit `40b897dc977f13ec0cd15f4606aada9f95396b3b` with
its upstream MIT license and SHA256 retained. It is a published processed
transfer-function sample, not original instrument time-series data. The header
declares WGS84, elevation 158 m with unknown vertical datum, mV/km/nT impedance
and positive time convention. The source rotation is 5°.

The [MT helper](../mtpy/scripts/mt_analysis.py) processes 80 frequencies and
all 320 tensor components. An explicitly requested extra 30° clockwise rotation
produces 35° orientation. Tests independently check `R Z Rᵀ`, determinant
invariance, SI apparent-resistivity conversion, source variance/missing masks
and actual EDI write/read. Separately generated EDI data check a known 100 Ω m
response with 45° xy and −135° yx phases. A negative signed phase is not
automatically an invalid measurement.

CSV/JSON and optional PNG are exported and reopened. Original EMPTY values and
unknown uncertainty remain distinguished; the native writer's zero/EMPTY
behaviour is explicitly limited to the complete-data EDI round-trip case.
Neither raw time-series estimation nor an MT field inversion is exercised.
Rotation propagates marginal uncertainties without providing a complete
covariance model. QC thresholds remain recorded diagnostic choices, not a
universal geological interpretation criterion.

## Isolated environments and reproduction

Run from the repository root after installing dependencies in separate
environments. Tests use vendored data and require no network, credentials,
downloads or display. GPRPy is installed from its fixed source commit because
there is no corresponding PyPI release endpoint at the verification date.

```bash
python3.11 -m venv /tmp/near-surface-gpr
/tmp/near-surface-gpr/bin/python -m pip install -r tests/science/requirements-near-surface-gpr.txt
/tmp/near-surface-gpr/bin/python -m pip install https://github.com/NSGeophysics/GPRPy/archive/3b1f75eba820764b2147568fc0cc40f3a47919d5.zip
MPLBACKEND=Agg /tmp/near-surface-gpr/bin/python -m unittest discover -s tests/science -p test_near_surface_workflow_gpr.py -v
```

GPR was executed with Python 3.11.14, GPRPy 1.0.14, NumPy 1.26.4,
SciPy 1.17.1, Matplotlib 3.10.8 and segyio 1.9.14. Upstream optional-migration
messages and syntax/deprecation warnings do not imply those APIs were tested.
The pin refers to
[the official GPRPy source](https://github.com/NSGeophysics/GPRPy/tree/3b1f75eba820764b2147568fc0cc40f3a47919d5).
The downloaded source archive was 4,914,853 bytes with SHA256
`d0820cacbe8dff4e020ff2814755908d16f42c18bb70e2aa28760d44ffc54dab`.
Processing reports retain the installed distribution's `direct_url.json`
metadata, including its fixed source URL, rather than assuming that every
installation with the same version label has identical source.

Use the existing modelling environment from
[SCIENTIFIC_TESTING.md](SCIENTIFIC_TESTING.md) for ERT:

```bash
MPLBACKEND=Agg python -m unittest discover -s tests/science -p test_near_surface_workflow_ert.py -v
```

ERT was executed with Python 3.12.12, pyGIMLi 1.6.0, NumPy 2.5.3,
pandas 3.0.5 and SciPy 1.18.1. The test preparation/CLI sequence creates all
normalized inputs and final response products in temporary directories.

MT uses its own Python 3.12 environment:

```bash
python3.12 -m venv /tmp/near-surface-mt
/tmp/near-surface-mt/bin/python -m pip install -r tests/science/requirements-near-surface-mt.txt
MPLBACKEND=Agg /tmp/near-surface-mt/bin/python -m unittest discover -s tests/science -p test_near_surface_workflow_mt.py -v
```

Its pinned distribution is MTpy-v2 2.1.4 with mt-metadata 1.0.10. All three
branches check actual execution and artifact contents, independently of agent
installation tests or whether a coding agent activates this workflow naturally.
