# 🌍 Geoscience Skills

**AI-powered geoscience assistant capabilities for Claude Code, Cursor, Windsurf, GitHub Copilot, and any agent supporting the [Agent Skills spec](https://github.com/anthropics/skills).**

[![Skills](https://img.shields.io/badge/Skills-30-blue)](SKILLS.md)
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

### Option 1: Clone Repository
```bash
git clone https://github.com/SteadfastAsArt/geoscience-skills.git

# For Claude Code
cp -r geoscience-skills/* ~/.claude/skills/

# For VS Code / GitHub Copilot
cp -r geoscience-skills/* .github/skills/
```

### Option 2: OpenSkills
```bash
npx openskills install geoscience-skills
```

### Python Dependencies
```bash
# Core (most common)
pip install obspy lasio xarray netcdf4 pyvista

# Full installation
pip install obspy segyio lasio welly gempy simpeg verde xarray pyvista pooch
```

> 📋 See [SKILLS.md](SKILLS.md) for domain-specific installation commands.

---

## 🧠 30 Integrated Skills

### By Popularity (GitHub Stars)

| Top Skills | Stars | Use Case |
|------------|-------|----------|
| **xarray** | 4.1k | NetCDF, climate data, multi-dimensional arrays |
| **pyvista** | 3.5k | 3D visualization, mesh analysis |
| **obspy** | 1.3k | Seismology, waveforms, earthquake catalogs |
| **gempy** | 1.2k | 3D implicit geological modelling |
| **devito** | 658 | Finite-difference wave simulation |
| **verde** | 648 | Spatial gridding, ML-style interpolation |
| **simpeg** | 607 | Geophysical inversion framework |

### By Domain

```
Seismic & Seismology     → obspy, segyio, disba
Well Logs & Petrophysics → lasio, welly, dlisio, striplog, petropy
3D Geological Modelling  → gempy, loopstructural, gemgis
Geophysical Inversion    → simpeg, devito, pylops, pygimli
Potential Fields         → harmonica
Rock Physics             → bruges
Geostatistics            → verde, geostatspy, scikit-gstat, gnnwr
Hydrology                → pastas
Surface Processes        → landlab
Structural Geology       → mplstereonet
Geochemistry             → pyrolite
Near-surface Geophysics  → gprpy, mtpy
Data Formats             → xarray (NetCDF/HDF5/Zarr)
Visualization            → pyvista
```

> 📋 Full details: [SKILLS.md](SKILLS.md)

---

## 🔧 Usage

### Slash Commands
```
/seismic-workflow   → Seismic data analysis pipeline
/well-analysis      → Well log evaluation pipeline
/model-3d           → 3D geological modelling pipeline
/inversion-workflow → Geophysical inversion pipeline
/spatial-gridding   → Spatial data gridding pipeline
```

### Domain Skills
```
/obspy      → Seismology workflows
/lasio      → LAS file operations
/gempy      → 3D geological modelling
/xarray     → NetCDF and climate data
/pyvista    → 3D visualization
```

### Natural Language
Just describe what you need:
- *"Process this miniseed file and remove instrument response"*
- *"Create a Bouguer gravity anomaly map"*
- *"Run ordinary kriging with a spherical variogram"*

---

## 📊 Coverage

| Metric | Value |
|--------|-------|
| Total Skills | 30 |
| Domains Covered | 17 |
| Combined GitHub Stars | 18,000+ |
| File Formats Supported | SEG-Y, LAS, DLIS, NetCDF, HDF5, Zarr, GRIB, VTK |

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

## 🤖 Agents

| Agent | Role |
|-------|------|
| data-qc-reviewer | Check well log, seismic, and spatial data quality |
| geoscience-mentor | Guide skill and workflow selection |

---

## 🤝 Contributing

PRs welcome! See **[CONTRIBUTING.md](CONTRIBUTING.md)** for the full guide, including:

- Step-by-step instructions for adding a new skill
- YAML frontmatter requirements (all 7 fields)
- Quality checklist and tag conventions
- Automated validation with `python3 scripts/validate_skills.py`

See **[docs/ROADMAP.md](docs/ROADMAP.md)** for planned skills and infrastructure improvements.

---

## 📚 Resources

- **Source**: [awesome-open-geoscience](https://github.com/softwareunderground/awesome-open-geoscience)
- **Skills Spec**: [anthropics/skills](https://github.com/anthropics/skills)
- **Community**: [Software Underground](https://softwareunderground.org/)

---

## 📄 License

MIT © 2024
