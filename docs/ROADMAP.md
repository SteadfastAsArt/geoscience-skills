# Roadmap

Updated **2026-09-14**. Implementation and verification are recorded in
[PR #3](https://github.com/SteadfastAsArt/geoscience-skills/pull/3).
The [verification summary](../README.md#verification-results) links the recorded
implementation and its five passing CI jobs.

## Next priorities

| Priority | Work | Acceptance |
| --- | --- | --- |
| P1 | Test native skill discovery and activation in Codex | Install skills, run a task without directing the agent to the catalog or a skill file, and retain observed activation and numerical checks. |
| P1 | Extend task evaluations to other available agents and workflow branches | Reuse the fixture/grader contracts; record actual CLI/model versions, skill use, outputs and failures. Claude runtime testing is excluded from this round. |
| P1 | Add field well, seismic and inversion datasets | Record source licenses, units, coordinates and missing values; define uncertainty and recovery criteria before evaluating results. |
| P2 | Audit DLIS, GIS/DEM, LoopStructural and configured PetroPy examples | Execute documented APIs with suitable fixtures, verify scientific invariants and shorten entrypoints as working examples are established. |
| P2 | Validate candidate dependency versions | Test proposed pins in isolated environments and rerun relevant science or installer checks before adoption. |
| P3 | Add planned skills and workflows | Provide concise portable entrypoints, meaningful examples and validation after existing correctness coverage improves. |
| P3 | Extend optional platform adapters where needed | Establish why native skill installation is insufficient, and keep the adapter optional for ordinary tasks. |

See [scientific testing](SCIENTIFIC_TESTING.md) for coverage boundaries,
[agent evaluations](AGENT_EVALUATIONS.md) for task evidence,
[compatibility](COMPATIBILITY.md) for installation results, and
[dependency maintenance](DEPENDENCY_MAINTENANCE.md) for the registry report.

## Completed by 2026-09-14

### Scientific correctness

- [x] Preserve SEG-Y absolute sample times when cropping; select geometry by
  trace headers, retaining trace order and offsets.
- [x] Resample LAS curves from their original depth grids, preserve original
  missing intervals, include aligned endpoints, and reject ambiguous depths.
- [x] Pass cleaned well logs into formation evaluation; retain missing intervals,
  guard invalid Archie inputs, and preserve surveyed trajectory coordinates.
- [x] Replace unsupported welly curve operations and record its setuptools constraint.
- [x] Correct sonic units, missing-DTS handling, Bruges calls, and time-domain synthetics.
- [x] Correct disba units/API and preserve seismic coordinates through processing/export.
- [x] Update GemPy model construction and preserve extent, resolution and cell ordering in VTK.
- [x] Make SimPEG and pyGIMLi branches independently usable through shared result/export stages.

### Portability and verification

- [x] Standardize all 36 skills, preserve dependency metadata, extract the
  independent router and generate optional platform manifests.
- [x] Share repository guidance through AGENTS.md with an optional Claude entrypoint.
- [x] Pass installation and resource-preservation checks for all 36 skills across
  nine targets on Linux and Windows.
- [x] Pass 53 lightweight tests, 85 scientific tests and two evaluation-fixture
  readback tests, with separate core/modelling dependency baselines.
- [x] Pass all five remote CI jobs: validation, Linux installation, Windows
  installation, core science and modelling science.
- [x] Record successful Codex LAS QC and SEG-Y tasks with independent output
  checks and observed skill reads. Preserve the first SEG-Y timeout alongside
  its successful controlled retry. Claude compatibility remains available;
  runtime evaluation is excluded from this round.
- [x] Add a published GNSS field-data case with source reconstruction, units,
  spatial holdout and conditional uncertainty checks. The diagnostic explicitly
  rejects an inadequate model; it does not establish field-scale inversion validity.

### Maintenance

- [x] Audit Bruges and disba examples and helpers against executable API tests;
  shorten their entrypoints and load detailed examples conditionally.
- [x] Add the read-only dependency report and weekly workflow configuration.
  Scheduled execution begins after the workflow reaches the default branch;
  dependency upgrades remain a separate validation task.

## Planned Skills

| Library | Domain | Stars | Priority |
|---------|--------|-------|----------|
| flopy | Groundwater Modelling (MODFLOW) | 600+ | High |
| pygmt | Generic Mapping Tools | 800+ | High |
| discretize | Mesh generation for SimPEG | 200+ | Medium |
| segysak | SEG-Y with xarray integration | 100+ | Medium |
| geolime | Mining geology & block models | 50+ | Medium |
| pyleoclim | Paleoclimate time series | 200+ | Medium |
| rockhound | Sample geoscience datasets | 50+ | Low |
| boule | Reference ellipsoids & gravity | 100+ | Low |
| ensaio | Geoscience sample datasets | 50+ | Low |

## Planned workflows and role guides

- Hydrogeological workflow (pastas + well logs)
- Near-surface geophysics workflow (GPR + ERT + MT)
- Climate data analysis workflow (xarray + verde)
- Cross-validation agent for model quality assessment

## Earlier milestones

- v2.3.0: Added GNNWR spatial regression skill (30th skill) to Spatial Analysis & Geostatistics category
- v2.2.0: Added workflow skills, agents, slash commands, and SessionStart hook
- v2.2.0: Enriched all 29 skill frontmatter with complements and workflow_role fields
- v2.0.0: Standardized all 29 skills to Anthropic skill format
- v2.0.0: Added YAML frontmatter with 7 required fields
- v2.0.0: Added workflow checklists and "when to use vs alternatives" sections
- v1.0.0: Initial release with 29 geoscience skills

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to add a new skill.
