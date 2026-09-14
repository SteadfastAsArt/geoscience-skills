---
name: geolime
description: Assess and maintain licensed GeoLime geological or mining-model workflows, checking the installed vendor API, drillhole conventions and model validation. Use when a project explicitly uses GeoLime; the public PyPI placeholder does not provide a working modelling API.
license: MIT
metadata:
  version: "1.0.0"
  author: Geoscience Skills
  skill_type: domain
  tags: '["Mining", "Geological Modelling", "Licensed Software"]'
  dependencies: '["geolime"]'
  complements: '["gempy", "geostatspy", "pyvista"]'
  workflow_role: modelling
---

# GeoLime

Start by establishing which licensed distribution and version the project uses.
The public PyPI `geolime==1.4.0` wheel contains a license-contact message and no
modelling API. `pip install geolime` alone does not establish an executable model
environment. This skill provides a preparation and review workflow; its licensed
modelling operations have not been executed in the repository's public tests.

## Environment and API

Inspect project lock files, installed distribution metadata, local vendor docs
and existing code before proposing imports. Use the vendor-provided environment
or wheel only when the user already has access. Record its version and hash in
the project; keep license files and credentials out of reports and source control.
Do not invent class names from an unrelated release's examples.

If the functional package is unavailable, complete format/geometry QC and a
reviewable model specification. State that execution remains unavailable. For an
open-source implementation, assess GemPy or geostatistics tools against the actual
required outputs; they are not drop-in GeoLime replacements.

## Data and model contract

- Keep collar, survey and interval tables linked by stable drillhole identifiers.
  Verify from/to depths, overlaps, gaps, units and survey-angle conventions.
- Establish CRS, elevation datum, downhole versus vertical depth and survey
  desurveying method. Retain missing assays and detection limits distinctly.
- Record compositing, domain boundaries, density assumptions and block dimensions
  before estimating grades, volumes or tonnage. Point samples and block support
  are not interchangeable.
- Keep original assay values and transformation/back-transformation settings.
  Validate grade estimates with spatially separated drillholes and domain-aware
  residuals; random sample splits can leak adjacent intervals.

## Validation and deliverables

Run the installed vendor's smallest documented example first, then validate a
simple project-owned geometry with an independent volume calculation. Check block
ordering and IDs in exports, domain coverage, mass/volume units and sensitivity
to mesh/compositing choices. Label unrun code and unavailable methods explicitly.

Preserve the model specification, QC tables, executed API/version evidence and
the distinction between calculated and assumed resources. Consult the
[vendor documentation](https://geolime-docs.deeplime.io/latest/) and
[public placeholder source](https://github.com/deeplime-io/geolime-pypi-package).
