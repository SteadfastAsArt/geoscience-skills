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

To adopt a candidate version, create an isolated environment, install the
proposed baseline and run its [scientific suites](SCIENTIFIC_TESTING.md). For an
installer change, also run `scripts/check_installation.py --cli-version VERSION`
and review its target-directory expectations. Change the pins only after the
relevant checks pass, and record any excluded environments or branches.
