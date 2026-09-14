---
name: using-geoscience-skills
description: |
  Discover and compose geoscience skills for Python coding tasks. Use when
  choosing a geoscience library, finding a skill for a data format or method,
  or planning work across seismic, well logs, geological modelling, inversion,
  and other geoscience domains.
license: MIT
metadata:
  skill_type: meta
  version: 1.0.1
  author: Geoscience Skills
  tags: '["Geoscience", "Skills", "Routing", "Discovery", "Workflows", "Agents"]'
  dependencies: '[]'
---

# Using Geoscience Skills

Match the user's task to the available domain and workflow skills. Select only
the steps needed for the requested result, and reuse data or code already supplied.

## When to Use and Alternatives

Use this skill when the appropriate geoscience library is unclear, a request spans
multiple domains, or several skills need to work together. For a named library or
one focused operation, use its domain skill directly. For an established multi-step
task, use the matching workflow skill below.

## Routing Procedure

1. Identify the requested deliverable, data format, existing inputs, and environment.
2. Match a focused task with the domain table, or a multi-step task with the workflow
   table. Treat listed chains as available options, not mandatory stages.
3. Check which skills are available in the current host. Read the selected skill's
   `SKILL.md` and only the reference files needed for the task, using the host's
   available file or resource access.
4. If a skill is missing or unavailable, continue with available documentation and
   capabilities where practical. State any material limitation; do not claim to
   have loaded or invoked a skill that was not accessible.
5. Complete the user's requested deliverable with relevant validation. Ask for
   clarification only when missing information materially affects the result;
   continue independent work when possible.

## Domain Routing Table

Match user intent keywords to the appropriate domain skill.

| Keywords / Triggers | Skill | Domain |
|---------------------|-------|--------|
| SEG-Y, seismic traces, trace headers, inline, crossline | `segyio` | Seismic I/O |
| waveform, earthquake, FDSN, seismogram, miniSEED | `obspy` | Seismology |
| surface wave, dispersion, Rayleigh, Love wave | `disba` | Seismology |
| LAS, well logs, wireline, borehole curves | `lasio` | Well Logs |
| DLIS, RP66, array logs, modern well data | `dlisio` | Well Logs |
| well analysis, curve QC, multi-well, despike | `welly` | Well Logs |
| petrophysics, Sw, porosity, formation evaluation | `petropy` | Petrophysics |
| lithology, stratigraphy, striplog, facies log | `striplog` | Stratigraphy |
| 3D model, geology, implicit surface, faults | `gempy` | 3D Modelling |
| fold modelling, structural frame, Loop3D | `loopstructural` | 3D Modelling |
| GIS, spatial data prep, borehole to GemPy | `gemgis` | GIS Preprocessing |
| inversion, DC resistivity, magnetics, gravity, EM | `simpeg` | Inversion |
| ERT, SRT, IP, near-surface inversion | `pygimli` | Inversion |
| PDE, wave equation, finite differences, stencil | `devito` | Simulation |
| linear operator, inverse problem, sparsity | `pylops` | Inverse Problems |
| gravity, magnetic, Bouguer, upward continuation | `harmonica` | Potential Fields |
| AVO, Zoeppritz, Gassmann, fluid substitution, wavelet | `bruges` | Rock Physics |
| gridding, interpolation, spatial, Verde | `verde` | Spatial Analysis |
| variogram, kriging, GSLIB, geostatistics | `geostatspy` | Geostatistics |
| variogram fitting, scikit-learn style geostat | `scikit-gstat` | Geostatistics |
| spatial regression, GWR, GNNWR, non-stationarity, coefficient mapping | `gnnwr` | Spatial Regression |
| groundwater, time series, pumping test | `pastas` | Hydrology |
| landscape, erosion, surface processes, DEM | `landlab` | Surface Processes |
| stereonet, strike, dip, poles, structural | `mplstereonet` | Structural Geology |
| geochemistry, REE, spider diagram, ternary | `pyrolite` | Geochemistry |
| GPR, ground-penetrating radar, radargram | `gprpy` | Near-Surface |
| magnetotellurics, MT, impedance tensor | `mtpy` | Near-Surface |
| NetCDF, xarray, multi-dimensional, climate | `xarray` | Data Formats |
| 3D visualization, mesh, VTK, point cloud | `pyvista` | Visualization |
| data download, sample data, cache, fetch | `pooch` | Utilities |

## Workflow Skills

Use the skill name directly when the host supports skill selection, or read the
available workflow instructions. Natural-language requests can match these tasks.

| Skill Name | Typical Task | Relevant Domain Skills |
|------------|--------------|------------------------|
| `seismic-interpretation` | Process or interpret seismic data; build a seismic-to-well tie | segyio, obspy, bruges, disba, pyvista |
| `well-log-evaluation` | Evaluate formations from LAS or DLIS logs | lasio, dlisio, welly, petropy, striplog, pyvista |
| `geological-modelling` | Build a 3D model from mapping, boreholes, or GIS inputs | gemgis, gempy or loopstructural, pyvista |
| `geophysical-inversion` | Recover physical properties from ERT, EM, gravity, or magnetic data | simpeg or pygimli, verde, pyvista |
| `rock-physics-avo` | Compute elastic properties, fluid substitution, AVO, or synthetics | lasio, welly, bruges, segyio |

## Composition and Data Handoffs

- Start from the inputs already available. Data loading, modelling, plotting, and
  export are needed only when they contribute to the requested task.
- Carry units, coordinates, depth or time basis, array shapes, missing-value masks,
  and provenance across library boundaries. Ensure later stages use the intended
  processed output.
- Check each selected skill's `metadata.dependencies` against the environment.
  Dependency and complement lists are descriptive metadata, not package-installation
  commands or proof that another skill is available.
- Choose compatible libraries and adapters for the selected branch. Do not assume
  alternatives produce interchangeable objects.
- Match validation to the deliverable: a corrected script, explanation, QC report,
  model, plot, or exported dataset may each complete the user's request.

## Optional Role References

The repository's `agents/data-qc-reviewer.md` and `agents/geoscience-mentor.md` are
optional role references for hosts that support them. Ordinary skill installation
may omit these files. Perform QC and explanations with available capabilities;
these roles and host-specific integrations are not requirements for routing or
executing the core skills.

## Common Issues

| Issue | Response |
|-------|----------|
| A recommended skill is not installed | Use available guidance or capabilities and report any material gap. |
| A required Python package is unavailable | Inspect the project environment and dependency guidance before choosing a compatible setup or alternative. |
| Data is already loaded or processed | Begin at the relevant stage and verify the supplied data's assumptions. |
| Several libraries match the request | Choose by data format, required operation, existing environment, and requested result. |
