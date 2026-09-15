# Scientific checks

The suites in `tests/science/` execute actual library APIs, repository scripts or
Python blocks in skill documents. Generated fixtures have independent numerical
answers; published field fixtures retain source bytes, licenses and conventions.
Passing these tests does not establish skill activation inside an agent: see
[agent evaluations](AGENT_EVALUATIONS.md) for that separate evidence.

## Isolated environments

Use a fresh path for each environment. Do not install this catalog into a user's
global Python environment, or combine all requirements into one lockfile.

| Environment | Python | Baseline | Suites |
| --- | --- | --- | --- |
| Core | 3.12 | [requirements-core.txt](../tests/science/requirements-core.txt) | I/O, seismic, well logs, Bruges/disba, field well/waveform, evaluation-fixture readback |
| Models | 3.12 | [requirements-models.txt](../tests/science/requirements-models.txt) | GemPy/SimPEG/pyGIMLi examples, GNSS, field ERT |
| Domain audits | 3.11 | [requirements-audits.txt](../tests/science/requirements-audits.txt) | DLIS, GIS/DEM, LoopStructural |
| PetroPy | 3.11 | [requirements-audits-petropy.txt](../tests/science/requirements-audits-petropy.txt) | Configured fluid and multimineral examples with compatible lasio |
| New collection | 3.12 | [requirements-collection.txt](../tests/science/requirements-collection.txt) | FloPy/MODFLOW, discretize, SEGY-SAK, Pyleoclim, Boule, Ensaio and legacy RockHound parser |
| PyGMT | 3.12 | [environment-pygmt.yml](../tests/science/environment-pygmt.yml) | Real GMT rendering and grid sampling |
| Hydro workflow | 3.11 | [requirements-hydro-workflow.txt](../tests/science/requirements-hydro-workflow.txt) | Pastas field hindcast, chronological holdout, diagnostics and model readback |
| Climate workflow | 3.12 | [requirements-climate-workflow.txt](../tests/science/requirements-climate-workflow.txt) | NOAA station aggregation, temporal/spatial isolation, calendars and NetCDF readback |
| GPR workflow | 3.11 | [requirements-near-surface-gpr.txt](../tests/science/requirements-near-surface-gpr.txt) plus fixed GPRPy source | Real field raw-format processing/export and controlled physical-unit examples |
| MT workflow | 3.12 | [requirements-near-surface-mt.txt](../tests/science/requirements-near-surface-mt.txt) | MTpy-v2 EDI/QC/rotation/export and independent tensor oracles |

Core retains pandas 2.3.3 because Welly calls an API removed in pandas 3, and
setuptools 80.9.0 because Welly/Bruges still import `pkg_resources`. Modelling and
new-collection environments passed with pandas 3.0.5. PetroPy requires its own
older lasio/NumPy combination. See [dependency validation](DEPENDENCY_MAINTENANCE.md)
and [domain audit constraints](DOMAIN_AUDITS.md) before changing a pin.

## Reproduce core and modelling checks

Run from the repository root. Use fresh paths if these already exist. Set
`MPLCONFIGDIR` to a temporary directory to avoid loading user-specific styles.

```bash
export MPLBACKEND=Agg
export MPLCONFIGDIR=/tmp/geoscience-mpl-tests
export PYVISTA_OFF_SCREEN=true
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1

python3.12 -m venv /tmp/geoscience-core-tests
/tmp/geoscience-core-tests/bin/python -m pip install -r tests/science/requirements-core.txt
/tmp/geoscience-core-tests/bin/python tests/science/test_io_scripts.py -v
/tmp/geoscience-core-tests/bin/python tests/science/test_seismic_examples.py -v
/tmp/geoscience-core-tests/bin/python tests/science/test_well_log_examples.py -v
/tmp/geoscience-core-tests/bin/python tests/science/test_domain_examples.py -v
/tmp/geoscience-core-tests/bin/python tests/science/test_field_well_logs.py -v
/tmp/geoscience-core-tests/bin/python tests/science/test_field_seismic_waveform.py -v
/tmp/geoscience-core-tests/bin/python evals/tests/test_fixture_readback.py -v

python3.12 -m venv /tmp/geoscience-model-tests
/tmp/geoscience-model-tests/bin/python -m pip install -r tests/science/requirements-models.txt
/tmp/geoscience-model-tests/bin/python tests/science/test_model_examples.py -v
/tmp/geoscience-model-tests/bin/python tests/science/test_field_data.py -v
/tmp/geoscience-model-tests/bin/python tests/science/test_field_ert_survey.py -v
/tmp/geoscience-model-tests/bin/python tests/science/test_near_surface_workflow_ert.py -v
```

For the domain audits, create separate Python 3.11 environments and run the
commands in [DOMAIN_AUDITS.md](DOMAIN_AUDITS.md). Their PetroPy and main-audit
requirements must not be installed over one another.

## New collection and external executables

```bash
python3.12 -m venv /tmp/geoscience-collection-tests
/tmp/geoscience-collection-tests/bin/python -m pip install -r tests/science/requirements-collection.txt
python3 scripts/install_modflow_test.py --directory /tmp/geoscience-modflow-tests/bin
MODFLOW_EXE=/tmp/geoscience-modflow-tests/bin/mf6 /tmp/geoscience-collection-tests/bin/python tests/science/test_collection_examples.py -v

conda env create --prefix /tmp/geoscience-pygmt-tests --file tests/science/environment-pygmt.yml
conda run --prefix /tmp/geoscience-pygmt-tests python tests/science/test_pygmt_examples.py -v
```

MODFLOW is downloaded from a fixed official release with archive/executable
hashes and written only to the explicit test directory. No user-level FloPy
installation metadata is used. The pinned binary is Linux x86-64; the GMT
shared library and Ghostscript are isolated by conda. Scientific CI currently
runs on Linux; Windows installation tests are separate from scientific execution.

After dependency/executable setup, the suites use offline data. Ensaio exercises
a genuine hash-verified cached dataset; RockHound exercises a synthetic cached
CSV because its legacy PREM download URL failed. Missing Python dependencies,
GMT or MODFLOW **fail** the relevant test; they are never reported as skipped
examples that passed validation.

## End-to-end workflow checks

Four additional environments keep Pastas 2.0, GPRPy, MTpy-v2 and climate
dependencies separate. The new ERT workflow runs in the existing modelling
environment. All data fixtures are local; dependency installation needs network
access, while the scientific execution does not.

```bash
python3.11 -m venv /tmp/geoscience-hydro-workflow
/tmp/geoscience-hydro-workflow/bin/python -m pip install -r tests/science/requirements-hydro-workflow.txt
/tmp/geoscience-hydro-workflow/bin/python tests/science/test_hydro_workflow.py -v

python3.12 -m venv /tmp/geoscience-climate-workflow
/tmp/geoscience-climate-workflow/bin/python -m pip install -r tests/science/requirements-climate-workflow.txt
/tmp/geoscience-climate-workflow/bin/python tests/science/test_climate_workflow.py -v

python3.11 -m venv /tmp/geoscience-gpr-workflow
/tmp/geoscience-gpr-workflow/bin/python -m pip install -r tests/science/requirements-near-surface-gpr.txt
/tmp/geoscience-gpr-workflow/bin/python -m pip install https://github.com/NSGeophysics/GPRPy/archive/3b1f75eba820764b2147568fc0cc40f3a47919d5.zip
/tmp/geoscience-gpr-workflow/bin/python tests/science/test_near_surface_workflow_gpr.py -v

python3.12 -m venv /tmp/geoscience-mt-workflow
/tmp/geoscience-mt-workflow/bin/python -m pip install -r tests/science/requirements-near-surface-mt.txt
/tmp/geoscience-mt-workflow/bin/python tests/science/test_near_surface_workflow_mt.py -v
```

Use fresh paths and the environment variables above. GPRPy's fixed source is
installed separately because it has no PyPI release. The MT import name is
`mtpy`, but its distribution is `mtpy-v2`; the old `mtpy` package is not a
substitute. These new suites fail on missing dependencies rather than skipping.

The [hydro](HYDRO_WORKFLOW_VALIDATION.md),
[near-surface](NEAR_SURFACE_WORKFLOW_VALIDATION.md) and
[climate](CLIMATE_WORKFLOW_VALIDATION.md) reports include full CLI commands,
fixture licenses, source hashes, scientific assumptions and recorded results.

## Numerical and field evidence

| Suite | Tests | Main checks |
| --- | ---: | --- |
| `test_io_scripts.py` | 18 | LAS nulls/units/depths and SEG-Y geometry, absolute sample time and file readback |
| `test_seismic_examples.py` | 10 | Sonic units, fluid substitution, synthetic timing and coordinate exports |
| `test_well_log_examples.py` | 9 | QC-to-formation handoff, analytic porosity/saturation, missing intervals and trajectories |
| `test_domain_examples.py` | 30 | Real Bruges/disba APIs, elastic identities, wavelets and analytic dispersion limits |
| `test_model_examples.py` | 8 | GemPy contact plane, independent SimPEG/pyGIMLi branches and VTK grid readback |
| `test_field_data.py` | 10 | Original-source reconstruction of 186 GNSS rows, weighted fit and spatial holdout |
| `test_field_well_logs.py` | 7 | Published log preservation, lasio roundtrip, missing depths, units and held-out interpolation |
| `test_field_seismic_waveform.py` | 7 | Real miniSEED, StationXML response, sampling phase and independent spectral checks |
| `test_field_ert_survey.py` | 7 | Real signed measurements, uncertainty/holdout, rejected simple model and independent synthetic recovery |
| `test_collection_examples.py` | 13 | New library examples, analytic MODFLOW flow and explicit dataset-cache contracts |
| `test_pygmt_examples.py` | 2 | Actual GMT export and coordinate-aware grid sampling |
| Domain-audit suites | 31 | Real DLIS (9), GIS/DEM (10), structural interpolation (6) and configured PetroPy (6); see [audit results](DOMAIN_AUDITS.md) |
| `test_hydro_workflow.py` | 13 | Published groundwater hindcast, unit conversion, training isolation, stress gaps and saved model/CLI outputs |
| `test_climate_workflow.py` | 14 | NOAA TMAX, independent calendar/area aggregation, spatial holdout leakage checks and NetCDF readback |
| `test_near_surface_workflow_gpr.py` | 9 | Field SEG-Y/GPRPy processing, independent raw MALA and documented time/depth scenarios |
| `test_near_surface_workflow_ert.py` | 8 | Complete field layered-fit output, response/residual reconstruction, held-out target perturbation and synthetic recovery |
| `test_near_surface_workflow_mt.py` | 8 | Field-derived EDI, independent impedance/rotation formulas, missingness, plots and CSV/EDI readback |
| `evals/tests/test_fixture_readback.py` | 3 | Independent agent fixtures read with actual LAS/SEG-Y libraries; no model invocation |

The 2026-09-14 Python 3.12 runs passed **81 core, 25 modelling/field, 13 collection
and 2 GMT scientific tests**, plus **3 evaluation-fixture readback tests**, without
skips. The Python 3.11 domain audits passed **31 more scientific tests**. Together
with **61 lightweight tests**, this is **216 automated tests**: 152 scientific,
3 fixture readbacks and 61 lightweight checks. Manual agent tasks are separate.
The **2026-09-15** workflow follow-up passed **52 additional scientific tests**
without skips: 13 hydro, 14 climate, 9 GPR, 8 ERT and 8 MT. The expanded suite
contains **268 automated tests**: 204 scientific across ten isolated
environments, 3 fixture readbacks and 61 lightweight checks. The lightweight
suite also passed after the workflow changes. CI runs all these suites on the
PR revision; consult the run history below for the commit and result.
Historical Python 3.11 results from merged
[PR #3](https://github.com/SteadfastAsArt/geoscience-skills/pull/3) remain valid for
that revision: 85 scientific tests, 2 fixture tests and 53 lightweight tests.
They are not substituted for tests of the new content or dependency versions.

## Scope of the evidence

Read [field-data validation](FIELD_DATA_VALIDATION.md) for source licenses,
uncertainty assumptions and the distinction between fitting field observations
and recovering synthetic truth. The real GNSS and ERT diagnostic models are
explicitly inadequate; a regression test passes when it detects that limitation.

The [new collection report](COLLECTION_VALIDATION.md) records the GeoLime license
restriction, RockHound download failure and subsequent workflow execution.
The named hydrology/GPR/ERT/MT/climate paths now execute and reopen outputs;
their reports distinguish observed data from controlled synthetic benchmarks.
This does not establish site-calibrated MODFLOW, field GPR depth with unknown
sampling units, multidimensional/joint inversion, raw MT time-series processing,
arbitrary climate forecasting/regridding or a licensed GeoLime runtime.
Additional operating systems, library versions and scientific tasks require their
own evidence. The [CI workflow](../.github/workflows/test-science.yml) runs these
isolated suites; use its [run history](https://github.com/SteadfastAsArt/geoscience-skills/actions/workflows/test-science.yml)
to identify the tested revision.
