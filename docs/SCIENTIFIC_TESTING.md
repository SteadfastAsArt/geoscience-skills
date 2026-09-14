# Scientific checks

Portable format and installation checks cannot establish correct numerical
results. The suites in `tests/science/` execute the repository's scripts or the
Python blocks in its skill documents using generated data. A separate field-data
suite checks vendored, published GNSS station estimates and uncertainty
diagnostics. The tests run offline after dependencies have been installed.

## Reproduce locally

Use Python 3.11 in isolated environments. Keep the core and modelling stacks
separate: the tested core stack uses NumPy 1.26, while pgcore 1.6 requires NumPy 2.
These requirement files are test baselines, not instructions to change an
agent's global Python environment.

```bash
python3.11 -m venv /tmp/geoscience-core-tests
/tmp/geoscience-core-tests/bin/python -m pip install -r tests/science/requirements-core.txt
MPLBACKEND=Agg /tmp/geoscience-core-tests/bin/python tests/science/test_io_scripts.py -v
MPLBACKEND=Agg /tmp/geoscience-core-tests/bin/python tests/science/test_seismic_examples.py -v
MPLBACKEND=Agg /tmp/geoscience-core-tests/bin/python tests/science/test_well_log_examples.py -v
MPLBACKEND=Agg /tmp/geoscience-core-tests/bin/python tests/science/test_domain_examples.py -v
/tmp/geoscience-core-tests/bin/python evals/tests/test_fixture_readback.py -v

python3.11 -m venv /tmp/geoscience-model-tests
/tmp/geoscience-model-tests/bin/python -m pip install -r tests/science/requirements-models.txt
MPLBACKEND=Agg /tmp/geoscience-model-tests/bin/python tests/science/test_model_examples.py -v
MPLBACKEND=Agg /tmp/geoscience-model-tests/bin/python tests/science/test_field_data.py -v
```

Use a fresh environment path if these names already exist. On Windows, use the
venv's `Scripts/python.exe` and the shell's environment-variable syntax. The
scientific CI currently targets Linux; Windows installation checks remain a
separate job.

Welly 0.5.2 and Bruges 0.5.4 import `pkg_resources`, which is absent from newer
setuptools; the core baseline includes setuptools 80.9.0. This compatibility pin does not
remove upstream deprecation warnings. When updating dependencies, rerun the
scientific examples before changing the baseline.

## What the suites check

| Suite | Evidence |
| --- | --- |
| `test_io_scripts.py` | Reopen generated LAS/SEG-Y outputs and verify curve values, missing-data handling, sample times, and trace geometry. |
| `test_seismic_examples.py` | Execute rock physics and seismic code blocks with synthetic inputs, checking units, supported library APIs, and spatial/sample coordinates. |
| `test_well_log_examples.py` | Execute the LAS → QC → formation evaluation → lithology → trajectory sequence; verify analytic porosity/saturation, retained missing intervals, and exported coordinates. |
| `test_model_examples.py` | Compute a small GemPy model, run short synthetic SimPEG and pyGIMLi inversions independently, and verify model-result handling and exported grid coordinates. |
| `test_domain_examples.py` | Execute Bruges and disba examples and helpers against real library APIs; check elastic relations, wavelets, dispersion, sensitivity, and exported results. |
| `test_field_data.py` | Reconstruct all 186 published GNSS rows from original source tables; check units, weighted fitting, spatial holdout and conditional error propagation. |
| `evals/tests/` | Read the independently generated agent-evaluation fixtures with real lasio and segyio. These checks do not invoke an agent model. |

The tests intentionally do not import every scientific dependency in the
structural test suite. Run `python3 -m unittest discover -s tests -v` for the
lightweight structural checks and the commands above for the scientific checks.
Missing scientific dependencies fail their suite rather than silently skipping it.

## Recorded verification

On **2026-09-14**, local Linux runs with Python **3.11.14** and the two dependency
baselines passed **85 scientific tests with no skips**: 18 I/O, 10 seismic/rock
physics, 9 well-log, 8 modelling, 30 Bruges/disba domain, and 10 field-data tests.
Two additional evaluation-fixture readback tests passed in the core environment.
The separate lightweight suite passed 53 tests, and the skill validator reported
36 skills with no errors or warnings.

The modelling suite executed GemPy's synthetic inclined contact and both
frameworks' short forward/inversion runs. Its checks include an analytic contact
plane, reduced SimPEG data misfit, homogeneous-earth pyGIMLi recovery, and real
VTK file readback. The scientific CI workflow uses the same core/modelling
separation and also checks the field-data and agent-evaluation fixtures.

## Remaining validation

- Extend the first [GNSS field-data case](FIELD_DATA_VALIDATION.md) to well,
  seismic and inversion datasets with documented licenses, units, coordinate
  systems, uncertainty, and expected outputs. The GNSS diagnostic detects model
  inadequacy; passing its regression suite does not validate a deformation model.
- Exercise GIS/DEM preparation, DLIS loading, the LoopStructural alternative,
  and configured PetroPy multimineral models. These branches require separate
  fixtures and are not covered by the first synthetic suites.
- Check full inversion recovery and interpretation quality; validating a tiny
  example is not evidence that a field-scale inversion is well constrained.
- Extend the recorded [Codex task evaluations](AGENT_EVALUATIONS.md) to native
  skill activation, more tasks and other available agents. An ordinary Python
  test is not an agent task evaluation; Claude runtime testing is outside this round.
- Exercise additional Python and operating-system versions before claiming
  those combinations are supported.

See [compatibility](COMPATIBILITY.md) for the distinction between installation
evidence and actual agent task execution, and [the roadmap](ROADMAP.md) for
remaining priorities.
