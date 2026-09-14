# Roadmap

Updated **2026-09-15**. The original portability work was merged in
[PR #3](https://github.com/SteadfastAsArt/geoscience-skills/pull/3).
The [verification summary](../README.md#verification-results) and reports below
record the subsequent P1–P3 work and its validation boundaries.

## P1–P3 delivery

The prior portability PR was merged before this work. The current delivery
tracks each requested priority against concrete evidence.

| Priority | Work delivered | Evidence and scope |
| --- | --- | --- |
| P1 | Native Codex discovery and implicit activation | Three task-only runs each scanned 48 enabled skills, read the appropriate native entrypoint and passed independent output checks. [Recorded runs](AGENT_EVALUATIONS.md). |
| P1 | More agent/workflow coverage | Added a formation-evaluation task and inspected available clients. Claude is excluded by request; OpenClaw is unconfigured and other assessed CLIs are unavailable. [Platform assessment](PLATFORM_ADAPTER_ASSESSMENT.md). |
| P1 | Field well, seismic and inversion data | Three licensed datasets, 21 scientific tests, explicit uncertainty/holdout and separate synthetic recovery. [Field evidence](FIELD_DATA_VALIDATION.md). |
| P2 | DLIS, GIS/DEM, LoopStructural and configured PetroPy audit | Real APIs, independent fixtures, corrected helpers and concise entrypoints. [Audit report](DOMAIN_AUDITS.md). |
| P2 | Candidate dependency validation | Tested isolated Python 3.12 stacks and installer 1.5.26; retained incompatible-branch pins with observed failure reasons. [Dependency decisions](DEPENDENCY_MAINTENANCE.md). |
| P3 | Planned skills, workflows and role guide | Added nine domain skills, three workflows and optional cross-validation guidance. [Collection report](COLLECTION_VALIDATION.md). |
| P3 | Optional adapters | Native installation and Codex scanning establish no need for another content adapter; existing optional manifests were regenerated for 48 skills. [Assessment](PLATFORM_ADAPTER_ASSESSMENT.md). |

## Remaining validation boundaries

These are external requirements or additional coverage, not claims established
by completing the above engineering work:

- **GeoLime runtime — excluded this round (confirmed 2026-09-15):** no licensed
  environment is available, so execution is explicitly skipped and does not
  block the other work. The skill retains its preparation/review guidance and
  limitation notice. Future API testing requires a licensed vendor distribution;
  the public PyPI placeholder is not a functional substitute.
- **Other agent runtimes:** OpenClaw needs model/provider configuration; absent
  clients need a usable environment. Claude runtime testing remains excluded.
  Installation support is not equivalent to model-task execution.
- **Full scientific workflows:** hydrogeology, near-surface and climate guides
  provide decision/validation procedures; their full Pastas/GPR/MT/climate field
  branches have not each been run end to end. Field-scale geological/inversion
  interpretation and additional OS/library combinations need separate evidence.
- **Legacy data availability:** RockHound is archived and its PREM URL returned
  404. Its real parser is tested with synthetic cached bytes; migration needs a
  verified replacement dataset or an existing valid cache for the user's task.

See [scientific testing](SCIENTIFIC_TESTING.md), [agent evaluations](AGENT_EVALUATIONS.md)
and [compatibility](COMPATIBILITY.md) for exact reproducible checks.

## Earlier work merged in PR #3

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
  After merging, its first manual run on main succeeded; validated dependency
  upgrades and rejected combinations are recorded separately.

## Added in v2.5.0

Domain skills: `flopy`, `pygmt`, `discretize`, `segysak`, `geolime`, `pyleoclim`,
`rockhound`, `boule` and `ensaio`.

Workflows: `hydrogeological-analysis`, `near-surface-geophysics` and
`climate-analysis`. Optional role: `cross-validation-reviewer`.

The total is 39 domain skills + 8 workflows + 1 router = **48**. A listed skill
is guidance, not a claim that its entire library is installed or validated.

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
