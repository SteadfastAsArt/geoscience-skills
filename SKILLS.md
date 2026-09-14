# Complete Skills Reference

Catalogue of **39 domain skills, 8 workflows and 1 discovery skill** (48 total).

Install selected skills with `npx skills add SteadfastAsArt/geoscience-skills --full-depth`.
See [coding agent compatibility](docs/COMPATIBILITY.md) for target directories and
verification scope. Installing guidance does not install Python libraries or
establish that every scientific operation has been tested.

## Domain skills

| Domain | Skill | Task |
| --- | --- | --- |
| Seismic / seismology | [obspy](obspy/SKILL.md) | Waveforms, event data, instrument responses and FDSN |
| Seismic / seismology | [segyio](segyio/SKILL.md) | Exact SEG-Y trace and header I/O |
| Seismic / seismology | [segysak](segysak/SKILL.md) | Labelled SEG-Y cubes with xarray and Dask |
| Seismic / seismology | [disba](disba/SKILL.md) | Rayleigh/Love dispersion and layered velocity models |
| Well logs | [lasio](lasio/SKILL.md) | LAS curves, headers and depth-aware file processing |
| Well logs | [welly](welly/SKILL.md) | Well-log QC and curve analysis |
| Well logs | [dlisio](dlisio/SKILL.md) | DLIS/LIS parsing, logical-file and channel identities |
| Well logs | [striplog](striplog/SKILL.md) | Lithology and stratigraphic intervals |
| Well logs | [petropy](petropy/SKILL.md) | Configured petrophysical fluid and mineral calculations |
| Geological modelling | [gempy](gempy/SKILL.md) | Implicit geological surfaces and 3D models |
| Geological modelling | [loopstructural](loopstructural/SKILL.md) | Structural interpolation, folds and faults |
| Geological modelling | [gemgis](gemgis/SKILL.md) | GIS, DEM and borehole input preparation |
| Geological modelling | [geolime](geolime/SKILL.md) | Licensed vendor workflow preparation and review; public PyPI is a placeholder |
| Simulation / inversion | [simpeg](simpeg/SKILL.md) | DC, EM, gravity and magnetic forward/inverse problems |
| Simulation / inversion | [pygimli](pygimli/SKILL.md) | ERT, refraction, IP and geophysical inversion |
| Simulation / inversion | [discretize](discretize/SKILL.md) | Finite-volume meshes and location-aware operators |
| Simulation / inversion | [devito](devito/SKILL.md) | Symbolic finite-difference PDE simulation |
| Simulation / inversion | [pylops](pylops/SKILL.md) | Linear operators and inverse problems |
| Gravity / rock physics | [harmonica](harmonica/SKILL.md) | Potential fields, corrections and equivalent sources |
| Gravity / rock physics | [boule](boule/SKILL.md) | Reference ellipsoids, normal gravity and coordinate geometry |
| Gravity / rock physics | [bruges](bruges/SKILL.md) | Elastic properties, AVO, wavelets and fluid substitution |
| Spatial analysis | [verde](verde/SKILL.md) | Spatial interpolation, gridding and validation |
| Spatial analysis | [geostatspy](geostatspy/SKILL.md) | Variograms, kriging and geostatistical simulation |
| Spatial analysis | [scikit-gstat](scikit-gstat/SKILL.md) | Variogram estimation and fitting |
| Spatial analysis | [gnnwr](gnnwr/SKILL.md) | Neural geographically weighted regression |
| Hydrology / surface | [pastas](pastas/SKILL.md) | Groundwater head time series and response models |
| Hydrology / surface | [flopy](flopy/SKILL.md) | MODFLOW flow models, heads and water budgets |
| Hydrology / surface | [landlab](landlab/SKILL.md) | Landscape and surface-process models |
| Geology / geochemistry | [mplstereonet](mplstereonet/SKILL.md) | Structural orientation and stereonets |
| Geology / geochemistry | [pyrolite](pyrolite/SKILL.md) | Geochemical ratios, normalization and diagrams |
| Near-surface | [gprpy](gprpy/SKILL.md) | Ground-penetrating radar processing |
| Near-surface | [mtpy](mtpy/SKILL.md) | Magnetotelluric impedance and models |
| Climate / data | [xarray](xarray/SKILL.md) | Labelled NetCDF/HDF5/Zarr arrays and climate fields |
| Climate / data | [pyleoclim](pyleoclim/SKILL.md) | Paleoclimate proxy spectra and chronology sensitivity |
| Visualization | [pyvista](pyvista/SKILL.md) | 3D meshes, volumes and VTK exports |
| Visualization | [pygmt](pygmt/SKILL.md) | Geographic maps and GMT grid operations |
| Data acquisition | [pooch](pooch/SKILL.md) | Hash-verified downloads and project caches |
| Data acquisition | [ensaio](ensaio/SKILL.md) | Versioned Fatiando datasets and provenance |
| Data acquisition | [rockhound](rockhound/SKILL.md) | Legacy dataset loader maintenance and migration; archived upstream |

## Workflows

Each workflow can run in one session. Start from available inputs, choose the
relevant branches and use available domain guidance; companion skills and optional
role files are not prerequisites. The three new workflows provide process guidance;
they do not claim all Pastas/GPR/MT/climate branches were executed end to end.

| Workflow | Task |
| --- | --- |
| [seismic-interpretation](workflows/seismic-interpretation/SKILL.md) | Seismic processing, rock physics and seismic-to-well ties |
| [well-log-evaluation](workflows/well-log-evaluation/SKILL.md) | LAS/DLIS QC, formation properties and lithology |
| [geological-modelling](workflows/geological-modelling/SKILL.md) | GIS/borehole preparation, implicit modelling and exports |
| [geophysical-inversion](workflows/geophysical-inversion/SKILL.md) | Survey preparation, forward/inverse modelling and uncertainty |
| [rock-physics-avo](workflows/rock-physics-avo/SKILL.md) | Elastic logs, fluid substitution, AVO and synthetics |
| [hydrogeological-analysis](workflows/hydrogeological-analysis/SKILL.md) | Well logs, groundwater head time series and aquifer hypotheses |
| [near-surface-geophysics](workflows/near-surface-geophysics/SKILL.md) | Coordinate- and resolution-aware comparison of GPR, ERT and MT |
| [climate-analysis](workflows/climate-analysis/SKILL.md) | Climate time/space analysis, anomalies and spatial holdouts |

## Discovery and optional review roles

The [router](using-geoscience-skills/SKILL.md) selects domain skills and workflows
from the task. Optional repository role guides are [data QC](agents/data-qc-reviewer.md),
[mentoring](agents/geoscience-mentor.md) and [cross-validation](agents/cross-validation-reviewer.md).
These guides are separate from the 48 installable skills and are not a portable
subagent registration format.

## Scientific environments

Use a task-specific isolated environment. The [tested baselines](docs/SCIENTIFIC_TESTING.md)
are separated because the complete package catalog is not one compatible environment.
In particular, configured PetroPy uses older lasio; current Pyleoclim/PyGMT need
Python 3.12; FloPy needs a MODFLOW executable; and PyGMT needs the GMT shared library.
GeoLime needs a functional vendor distribution and license. RockHound has stopped
development and its legacy PREM download URL failed in the recorded check.

See [new collection validation](docs/COLLECTION_VALIDATION.md),
[domain audits](docs/DOMAIN_AUDITS.md), [field data](docs/FIELD_DATA_VALIDATION.md)
and [dependency maintenance](docs/DEPENDENCY_MAINTENANCE.md) for actual tests and limitations.
