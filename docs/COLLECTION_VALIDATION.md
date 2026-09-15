# Added skills and workflows

Recorded **2026-09-14**. The collection now contains 39 domain skills, 8 workflows
and the router: **48 installable skills**. New entrypoints use the shared format
and do not require agent-specific commands, hooks, plugins or delegation.

## Executed examples

The collection environment uses Python **3.12.12** and
[requirements-collection.txt](../tests/science/requirements-collection.txt).
Its **13 tests passed without skips**. An independent conda environment with
PyGMT **0.19.0**, GMT **6.6.0**, Python 3.12 and Ghostscript **10.08.0** passed
**2 additional tests**. These are library/API checks, separate from agent task runs.

| Skill | Actual check | Boundary |
| --- | --- | --- |
| FloPy 3.11.0 | MODFLOW 6 solves a confined aquifer; heads equal the 10→9 m analytic profile, boundary flows are ±2 m³/day and net budget is zero to numerical precision. | Small synthetic steady model; no field calibration or transient recovery claim. |
| discretize 0.12.0 | Nonuniform cell geometry/order, linear-vector-field divergence and independent boundary-flux integral. | TensorMesh example; adaptive tree/PDE convergence needs task-specific checks. |
| SEGY-SAK 0.5.4 | Real SEG-Y→xarray backend, inline/crossline labels, 100–110 ms absolute sample times and every trace compared with segyio. | Complete post-stack cube; irregular/missing-trace geometry needs separate validation. |
| Pyleoclim 1.3.0 | Irregular synthetic 20-year sinusoid recovered at about 20.024 years; original chronology retained and unstable spectral estimates masked explicitly. | Frequency recovery, not statistical significance or age-model uncertainty validation. |
| Boule 0.6.0 | Gravity SI/mGal conversion, equator/pole reference values, coordinate roundtrip and analytic geocentric latitude. | Ellipsoid geometry; no datum, geoid or terrain transformation. |
| Ensaio 0.7.1 | Genuine versioned Alps GNSS bytes seeded into a temporary cache, verified by the actual fetcher and read as 186 CSV rows. | Cached acquisition contract; this test needs no live download. |
| RockHound 0.2.0 | Actual PREM parser and Pooch cache contract with project-owned synthetic rows, including repeated boundary radii and zero shear velocity. | Upstream is archived. Its live PREM URL returned HTTP 404; no successful live PREM fetch or validation of the PREM model is claimed. |
| PyGMT 0.19.0 | Actual GMT PDF export and grid-node sampling with independent coordinate/value checks. | Offline synthetic map/grid; no remote relief or projection-accuracy audit. |
| GeoLime | Public 1.4.0 wheel/source inspected; it contains a license-contact stub and no modelling API. | Runtime testing explicitly excluded this round because no licensed environment is available (confirmed 2026-09-15). No numerical test is counted as passed for it. |

The FloPy benchmark places the 20 m thick aquifer between elevations -20 and
0 m, with every head above its top; it also fails if MODFLOW is absent or the solve fails. The test
installer downloads only from the official
[MODFLOW-ORG release 29.0](https://github.com/MODFLOW-ORG/executables/releases/tag/29.0)
(MODFLOW 6.7.0)
and verifies both archive and executable SHA-256 before writing into an explicit
test directory. It does not update FloPy's user-level installation metadata.
See [install_modflow_test.py](../scripts/install_modflow_test.py) for the pinned
checksums and [scientific testing](SCIENTIFIC_TESTING.md) for reproduction.

RockHound's maintenance-only scope follows its
[archived project notice](https://github.com/fatiando/rockhound). The GeoLime
restriction is visible in the
[public distribution source](https://github.com/deeplime-io/geolime-pypi-package).
A licensed environment is needed before adding version-specific GeoLime API
examples; the current skill remains useful for preparation and review. This
documented exclusion does not block the other P1–P3 work.

## New workflow guidance

| Workflow | Decisions and validation it requires |
| --- | --- |
| [Hydrogeological analysis](../workflows/hydrogeological-analysis/SKILL.md) | Separate downhole depth from groundwater head, align datums/time, test Pastas responses with withheld periods and treat logs as aquifer constraints. |
| [Near-surface geophysics](../workflows/near-surface-geophysics/SKILL.md) | Select available GPR/ERT/MT branches, preserve measurement units and geometry, and compare resolution before interpreting shared structures. |
| [Climate analysis](../workflows/climate-analysis/SKILL.md) | Preserve calendars and missingness, choose anomaly baselines before fitting, and prevent spatial or temporal leakage in validation. |

These three entrypoints provide reviewed process guidance, with no new unexecuted
API snippets presented as tested examples. Their full hydrology/GPR/MT/climate
branches have **not** each been run end to end. Their role is to guide task-specific
work; the executed workflow Agent case is the separate formation-evaluation case
in [agent evaluations](AGENT_EVALUATIONS.md).

The new [cross-validation review guide](../agents/cross-validation-reviewer.md)
can be followed in the same session or used as an optional role. It is not a
49th skill or a portable subagent registration mechanism.
