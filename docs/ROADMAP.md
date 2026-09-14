# Roadmap

## Current priorities

### P0 — Correct scientific results

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

### P1 — Establish repeatable evidence

- [x] Complete the first synthetic scientific regression suites for the audited
  scripts and five workflows; add isolated CI jobs with tested dependency versions.
- [x] Add a task-evaluation runner, private numerical oracles, observed skill-read
  evidence and recorded Codex LAS/SEG-Y runs. See [results and limits](AGENT_EVALUATIONS.md).
  Claude runtime evaluation is outside this round; its compatibility support remains.
- [x] Add a published GNSS field-data case with source reconstruction, units,
  spatial holdout and conditional uncertainty checks. The diagnostic explicitly
  rejects an inadequate model; it does not establish field-scale inversion validity.
- [ ] Evaluate native skill discovery/activation and extend recorded tasks to
  other available agents and workflow branches.
- [ ] Add field well/seismic/inversion datasets and recovery criteria, including
  realistic noise and model uncertainty.

### P2 — Maintain and extend the collection

- [x] Audit Bruges and disba examples and helpers against executable API tests;
  shorten their entrypoints and load detailed examples conditionally.
- [ ] Continue domain audits with DLIS, GIS/DEM, LoopStructural and configured
  PetroPy examples; shorten their entrypoints as each audit establishes safe examples.
- [x] Add a weekly read-only report of scientific-library and installer versions.
- [ ] Test candidate dependency versions in isolated environments before changing
  verified baselines; a registry version difference does not establish compatibility.
- [ ] Add the planned skills and workflows below after correctness and evaluation coverage improve.

See [scientific testing](SCIENTIFIC_TESTING.md) for reproducible commands and
coverage boundaries, [compatibility](COMPATIBILITY.md) for installation evidence,
and [dependency maintenance](DEPENDENCY_MAINTENANCE.md) for the registry report.

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

## Infrastructure

### Planned
- Expand field-data coverage beyond the first GNSS case
- Native skill activation and additional agent task evaluations (see P1)
- Validate candidate installer and scientific library versions (see P2)
- Expand platform adapters only where native skills installation is insufficient

### Future Workflows & Agents
- Hydrogeological workflow (pastas + well logs)
- Near-surface geophysics workflow (GPR + ERT + MT)
- Climate data analysis workflow (xarray + verde)
- Cross-validation agent for model quality assessment

### Completed
- Recorded Codex tasks, independent numerical graders and free evaluation-fixture tests
- Published GNSS fixture with source hashes, attribution and uncertainty diagnostics
- Bruges/disba domain audits and shorter, conditional entrypoints
- Read-only dependency version monitoring workflow
- Synthetic scientific regressions for LAS/SEG-Y scripts and the audited workflow examples
- Separate core/modelling dependency baselines and scientific CI configuration
- Portable Agent Skills metadata and neutral descriptions across all 36 skills
- Independent discovery skill and recursive workflow discovery
- Shared repository guidance in AGENTS.md with an optional Claude entrypoint
- Generated platform manifests and pinned upstream installer checks
- v2.3.0: Added GNNWR spatial regression skill (30th skill) to Spatial Analysis & Geostatistics category
- v2.2.0: Added workflow skills, agents, slash commands, and SessionStart hook
- v2.2.0: Enriched all 29 skill frontmatter with complements and workflow_role fields
- v2.0.0: Standardized all 29 skills to Anthropic skill format
- v2.0.0: Added YAML frontmatter with 7 required fields
- v2.0.0: Added workflow checklists and "when to use vs alternatives" sections
- v1.0.0: Initial release with 29 geoscience skills

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to add a new skill.
