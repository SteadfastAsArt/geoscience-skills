# Dependency maintenance

Run the read-only registry report from a checkout:

```bash
python3 scripts/check_dependency_updates.py --output /tmp/geoscience-dependency-versions.json
```

It reads the exact pins in `tests/science/requirements-*.txt` and the installer
version in `scripts/check_installation.py`. It queries the public
[PyPI JSON API](https://docs.pypi.org/api/json/) and
[npm registry](https://github.com/npm/registry/blob/main/docs/REGISTRY-API.md).
No package-manager command, install, update, or skill activation is involved.

The report distinguishes matching versions, different registry versions, and
lookup errors. A different version is a candidate for review; it may be
incompatible with the baseline's Python version or other dependencies. Network
or malformed-response errors fail the command instead of appearing up to date.
This reports direct test dependencies, not transitive vulnerability coverage or
compatibility of every library mentioned in every skill.

The weekly `Dependency Version Report` workflow stores its JSON as a workflow
artifact. It also supports manual dispatch. Scheduled runs become active only
when this workflow is present on the repository's default branch.

PR #3 was merged into `main` on **2026-09-14**. The first
[manual run on main](https://github.com/SteadfastAsArt/geoscience-skills/actions/runs/34854160260)
completed successfully and uploaded its report. The Monday 03:19 UTC schedule
is configured; that manual result is not evidence of a scheduled invocation.

To adopt a candidate version, create an isolated environment, install the
proposed baseline and run its [scientific suites](SCIENTIFIC_TESTING.md). For an
installer change, also run `scripts/check_installation.py --cli-version VERSION`
and review its target-directory expectations. Change the pins only after the
relevant checks pass, and record any excluded environments or branches.

## Candidate validation on 2026-09-14

Fresh Python 3.12 environments were created separately from all existing core,
modelling and user-level environments. No user-level package or installed skill
was upgraded. The original report identified NumPy, pandas, SciPy, setuptools
and the skills CLI as candidates.

| Candidate | Observed result | Decision |
| --- | --- | --- |
| NumPy 2.5.3 + SciPy 1.18.1 | Passed core scientific suites after retaining compatible pandas/setuptools; modelling examples and GNSS diagnostics also passed. Both releases require Python 3.12+. | Adopt in the Python 3.12 core/modelling test baselines. Historical Python 3.11 runs retain their original versions. |
| pandas 3.0.5 | Welly's trajectory branch failed with `Index` lacking `is_numeric`; modelling and new-collection suites passed. | Keep core pandas 2.3.3; adopt 3.0.5 in modelling/new collection. |
| setuptools 84.0.0 | Welly 0.5.2 and Bruges 0.5.4 could not import because `pkg_resources` was absent. | Keep core setuptools 80.9.0. Do not mask the import failure. |
| skills CLI 1.5.26 | All 48 skills installed for each of nine target directories on local Linux, with matching upstream inventory and preserved resources. | Adopt the tested installer pin; Linux/Windows CI repeats the check. |

The rejected core trial ran **66 of 67 existing scientific tests successfully**
after restoring setuptools; the remaining Welly trajectory failure caused the
pandas 3 trial to be rejected. After restoring pandas 2.3.3 as well, **81 core
scientific tests and 3 evaluation-fixture tests passed** in the candidate
environment, including the new field well and waveform suites. The separate
model candidate passed the existing 18 model/GNSS tests and 7 new ERT checks.
The final read-only registry report covered all five Python baseline files and
the installer pin: 53 matching rows, 14 different-version rows and zero lookup
errors. Retained older pins remain visible as differences; this is intentional.

New domain-audit constraints, including the older lasio needed by configured
PetroPy, are documented in [domain audits](DOMAIN_AUDITS.md). New collection
and external-executable checks are in [collection validation](COLLECTION_VALIDATION.md).
The registry script monitors exact Python pins in `requirements-*.txt` and the
skills CLI; the separate conda GMT/Ghostscript environment and MODFLOW binary
hashes are reviewed through their dedicated tests, not that registry report.
