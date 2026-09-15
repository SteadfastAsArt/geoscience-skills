# 🌍 Geoscience Skills

**Portable geoscience skills for Codex, Claude Code, GitHub Copilot, Gemini CLI, Windsurf, OpenCode, Cline, Roo Code, OpenClaw, and other coding agents using the [Agent Skills format](https://agentskills.io/specification).**

39 domain skills + 8 workflows + 1 discovery skill. The same skill files are shared across agents; platform commands, hooks, and subagents are optional. See the [verification results](#verification-results) and [compatibility matrix](docs/COMPATIBILITY.md).

[![Skills](https://img.shields.io/badge/Skills-48-blue)](SKILLS.md)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 Capabilities at a Glance

| Domain | What You Can Do |
|--------|-----------------|
| **🔬 Seismic** | Read SEG-Y files, process waveforms, fetch earthquake data, compute dispersion curves |
| **🛢️ Well Logs** | Parse LAS/DLIS files, calculate porosity & saturation, create striplogs |
| **🏔️ 3D Modelling** | Build implicit geological models with faults and folds |
| **📡 Inversion** | Run ERT, seismic, gravity, magnetic inversions |
| **🗺️ Geostatistics** | Variograms, kriging, spatial interpolation, gridding |
| **🌊 Climate/Ocean** | NetCDF analysis, multi-dimensional arrays, time series |
| **💧 Hydrology** | Groundwater modelling, landscape evolution |
| **🧪 Geochemistry** | REE patterns, spider diagrams, classification plots |
| **📊 Visualization** | 3D mesh rendering, stereonets, publication figures |

---

## ⚡ Quick Examples

```
"Read this SEG-Y file and show the first 10 traces"
"Calculate water saturation from these well logs using Archie equation"
"Build a 3D geological model with two faulted horizons"
"Invert this ERT survey and plot the resistivity section"
"Compute variogram and run kriging on this spatial data"
"Load this NetCDF climate file and compute monthly anomalies"
"Create a chondrite-normalized REE spider diagram"
```

---

## 📦 Installation

### Upstream skills CLI (recommended)

Run from the project where you want to use the skills. The installer supports
multiple coding agents and manages their destination directories.

```bash
# Inspect all domain, workflow, and routing skills
npx skills add SteadfastAsArt/geoscience-skills --full-depth --list

# Select skills and target agents interactively
npx skills add SteadfastAsArt/geoscience-skills --full-depth

# Install a starting set for multiple agents
npx skills add SteadfastAsArt/geoscience-skills --full-depth \
  --skill using-geoscience-skills lasio segyio --agent codex claude-code

# Install the whole collection for one agent
npx skills add SteadfastAsArt/geoscience-skills --full-depth \
  --skill '*' --agent gemini-cli

# Install a workflow and the domain skills needed for it
npx skills add SteadfastAsArt/geoscience-skills --full-depth \
  --skill well-log-evaluation lasio dlisio welly petropy striplog pyvista \
  --agent github-copilot
```

Keep `--full-depth` to include workflows nested under `workflows/`. Add `--global`
for user scope; use `--copy` if you prefer copies to symlinks. Choosing a workflow
does not automatically install its complementary skills or Python dependencies.
Other targets include `windsurf`, `opencode`, `cline`, `roo`, and `openclaw`;
consult the [upstream supported-agent list](https://github.com/vercel-labs/skills#supported-agents).

```bash
npx skills list
# Explicitly update installed skills when desired
npx skills update
```

### From a local checkout

```bash
git clone https://github.com/SteadfastAsArt/geoscience-skills.git
# Run this in your target project; replace the path with your checkout location.
npx skills add /path/to/geoscience-skills --full-depth --agent codex
```

For manual installation, copy each selected **skill directory** to a directory
supported by your agent. Preserve its `SKILL.md`, `references/`, and `scripts/`.
For a workflow, copy `workflows/<name>/` as `<name>/` alongside the domain skills.
Do not copy the whole repository into an agent's skill directory. Platform
configuration and optional role guides are separate from skill installation.
See [platform notes and the manual reading fallback](docs/COMPATIBILITY.md).

### Python dependencies

Install the packages needed for your task in its Python environment. For example:

```bash
# LAS inspection and conversion
python -m pip install lasio pandas

# SEG-Y inspection and subsetting
python -m pip install segyio numpy
```

Skill `metadata.dependencies` records library requirements; installing a skill
does not install or validate those packages. See [SKILLS.md](SKILLS.md) for
additional domain-specific package lists.

---

## 🧠 39 Domain Skills

### By Domain

```
Seismic & Seismology     → obspy, segyio, segysak, disba
Well Logs & Petrophysics → lasio, welly, dlisio, striplog, petropy
3D Geological Modelling  → gempy, loopstructural, gemgis, geolime (licensed)
Geophysical Inversion    → simpeg, devito, pylops, pygimli, discretize
Potential Fields         → harmonica, boule
Rock Physics             → bruges
Geostatistics            → verde, geostatspy, scikit-gstat, gnnwr
Hydrology                → pastas, flopy
Surface Processes        → landlab
Structural Geology       → mplstereonet
Geochemistry             → pyrolite
Near-surface Geophysics  → gprpy, mtpy
Data Formats             → xarray (NetCDF/HDF5/Zarr), pyleoclim
Visualization            → pyvista, pygmt
Datasets                 → pooch, ensaio, rockhound (legacy)
```

> 📋 Full details: [SKILLS.md](SKILLS.md)

---

## 🔧 Usage

Describe the task naturally, or select an installed skill using your agent's
skill interface:

- "Use lasio to inspect the headers and curves in this LAS file."
- "Use well-log-evaluation to evaluate these logs."
- "Use using-geoscience-skills to choose the tools for this task."

The router selects domain and workflow skills by name. Workflows can run within
one agent session and do not require a particular delegation tool. Only the
references and workflow stages needed for the task should be loaded.

Claude Code users working in this checkout can also use the optional aliases
in `.claude/commands/`: `/seismic-workflow`, `/well-analysis`, `/model-3d`,
`/inversion-workflow`, and `/spatial-gridding`. These aliases and the local
SessionStart hook are not installed by the generic skills CLI.

---

## 📊 Coverage

| Metric | Value |
|--------|-------|
| Installable Skills | 48 (39 domain + 8 workflow + 1 router) |
| File Formats Supported | SEG-Y, LAS, DLIS, NetCDF, HDF5, Zarr, GRIB, VTK |

---

## Verification results

Recorded on **2026-09-14**. [PR #3](https://github.com/SteadfastAsArt/geoscience-skills/pull/3)
was merged first; the following P1–P3 work extends that baseline.

| Check | Recorded result |
| --- | --- |
| Native Codex tasks | **LAS QC, SEG-Y subsetting and formation evaluation passed** without task prompts naming skills or catalog paths. Each run discovered all 48 skills and retained successful native skill-read evidence. See [agent evaluations](docs/AGENT_EVALUATIONS.md). |
| Installation | **48 skills × nine targets passed locally** with skills CLI 1.5.26, including bundled resources. Linux/Windows CI runs the same checks; see [compatibility evidence](docs/COMPATIBILITY.md#verification-scope). |
| Automated tests | **216 passed**: 152 scientific checks across six isolated environments, 61 lightweight checks and 3 evaluation-fixture readbacks. See [suite results and reproduction](docs/SCIENTIFIC_TESTING.md). |
| Field data | Published well logs, earthquake waveform and ERT observations now join GNSS, with licenses, units, holdout checks and explicit uncertainty limits. See [field-data validation](docs/FIELD_DATA_VALIDATION.md). |
| Dependencies | Candidate NumPy/SciPy updates passed; incompatible pandas/setuptools combinations were rejected. The [report workflow ran successfully on main](https://github.com/SteadfastAsArt/geoscience-skills/actions/runs/34854160260). See [decisions](docs/DEPENDENCY_MAINTENANCE.md). |

Claude runtime testing is excluded from this round. Other client availability
and optional-adapter decisions are in the [platform assessment](docs/PLATFORM_ADAPTER_ASSESSMENT.md).
Scientific execution is verified on Linux. GeoLime requires a licensed vendor
runtime; RockHound is maintained here for legacy migration, with its failed
upstream PREM URL documented. The [new collection report](docs/COLLECTION_VALIDATION.md)
also distinguishes executable examples from the new workflow process guides.

---

## 🔄 Workflow Skills

Multi-step workflows that chain domain skills together:

| Workflow | Skills Used | Use Case |
|----------|------------|----------|
| Seismic Interpretation | segyio → obspy → bruges → pyvista | Seismic data analysis |
| Well Log Evaluation | lasio/dlisio → welly → petropy → striplog | Formation evaluation |
| Geological Modelling | gemgis → gempy/loopstructural → pyvista | 3D model building |
| Geophysical Inversion | simpeg/pygimli → verde → pyvista | ERT, magnetics, gravity |
| Rock Physics & AVO | lasio/welly → bruges → segyio | AVO feasibility studies |
| Hydrogeological Analysis | well logs + pastas; optional flopy | Groundwater head and aquifer hypotheses |
| Near-surface Geophysics | gprpy + pygimli/simpeg + mtpy | Compare GPR, ERT and MT evidence |
| Climate Analysis | xarray + verde; optional pyleoclim | Time/space analysis without validation leakage |

The audited examples have separate [scientific regression checks](docs/SCIENTIFIC_TESTING.md)
using generated LAS/SEG-Y files, elastic logs, geological/inversion models, and
[published field data](docs/FIELD_DATA_VALIDATION.md). These check numerical
outputs, coordinates and uncertainty assumptions. Recorded [Codex task evaluations](docs/AGENT_EVALUATIONS.md)
separately check skill selection and produced files.

## 🤖 Optional Role Guides

The files in `agents/` provide optional role guidance. A generic skill installation
does not register them as subagents; use them explicitly when available.

| Guide | Role |
|-------|------|
| data-qc-reviewer | Check well log, seismic, and spatial data quality |
| geoscience-mentor | Guide skill and workflow selection |
| cross-validation-reviewer | Review independent holdouts, uncertainty and model comparison |

---

## 🤝 Contributing

PRs welcome! See **[CONTRIBUTING.md](CONTRIBUTING.md)** for the full guide, including:

- Step-by-step instructions for adding a new skill
- Portable frontmatter and project metadata conventions
- Task boundaries, resource loading, and scientific validation guidance
- Recursive skill validation, generated platform manifests, and installation smoke tests

See **[docs/ROADMAP.md](docs/ROADMAP.md)** for completed priorities and remaining validation boundaries.

[Dependency maintenance](docs/DEPENDENCY_MAINTENANCE.md) describes the weekly
registry report and the checks required before adopting new library or installer versions.

---

## 📚 Resources

- **Source**: [awesome-open-geoscience](https://github.com/softwareunderground/awesome-open-geoscience)
- **Skills Spec**: [Agent Skills specification](https://agentskills.io/specification)
- **Community**: [Software Underground](https://softwareunderground.org/)

---

## 📄 License

MIT © 2024

Bundled data retain their own licenses and attribution:

- [Alps GNSS](tests/fixtures/field/alps_gps/ATTRIBUTION.md): original CC BY 3.0 and curated CC BY 4.0.
- [Published well logs](tests/fixtures/field/well_logs/ATTRIBUTION.md): CC BY 4.0.
- [GEOFON waveform and response](tests/fixtures/field/seismic_waveform/ATTRIBUTION.md): CC BY 4.0.
- [Crescentino ERT](tests/fixtures/field/ert_survey/ATTRIBUTION.md): CC BY 4.0.

Project-generated audit fixtures are explicitly synthetic and do not represent
field observations.
