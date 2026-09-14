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
| `evals/tests/test_fixture_readback.py` | 3 | Independent agent fixtures read with actual LAS/SEG-Y libraries; no model invocation |

The 2026-09-14 Python 3.12 runs passed **81 core, 25 modelling/field, 13 collection
and 2 GMT scientific tests**, plus **3 evaluation-fixture readback tests**, without
skips. The Python 3.11 domain audits passed **31 more scientific tests**. Together
with **61 lightweight tests**, this is **216 automated tests**: 152 scientific,
3 fixture readbacks and 61 lightweight checks. Manual agent tasks are separate.
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
restriction, RockHound download failure and the process-only validation of the
three new workflow guides. No full field-scale inversion, arbitrary geology,
licensed GeoLime runtime, or complete hydrology/GPR/MT/climate pipeline is claimed.
Additional operating systems, library versions and scientific tasks require their
own evidence. The [CI workflow](../.github/workflows/test-science.yml) runs these
isolated suites; use its [run history](https://github.com/SteadfastAsArt/geoscience-skills/actions/workflows/test-science.yml)
to identify the tested revision.
