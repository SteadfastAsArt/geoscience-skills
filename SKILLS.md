# Complete Skills Reference

Detailed list of all 29 geoscience skills with GitHub stars and descriptions.

## Skills by Category

### Seismic & Seismology
| Skill | Stars | Description |
|-------|-------|-------------|
| [obspy](obspy/) | 1.3k | Seismological data processing, waveforms, events, FDSN services |
| [segyio](segyio/) | 557 | SEG-Y file reading and writing for seismic data |
| [disba](disba/) | 178 | Surface wave dispersion computation (Rayleigh, Love waves) |

### Well Log Analysis
| Skill | Stars | Description |
|-------|-------|-------------|
| [lasio](lasio/) | 381 | LAS file reading and writing |
| [welly](welly/) | 356 | Well data analysis and visualization |
| [dlisio](dlisio/) | 132 | DLIS/LIS file parsing for modern well logs |
| [striplog](striplog/) | 220 | Lithological and stratigraphic log display |
| [petropy](petropy/) | 197 | Petrophysical analysis and formation evaluation |

### Geological Modelling
| Skill | Stars | Description |
|-------|-------|-------------|
| [gempy](gempy/) | 1.2k | 3D structural geological modelling (implicit surfaces) |
| [loopstructural](loopstructural/) | 242 | 3D implicit modelling with faults and folds |
| [gemgis](gemgis/) | 285 | Spatial data processing for GemPy |

### Geophysical Simulation & Inversion
| Skill | Stars | Description |
|-------|-------|-------------|
| [simpeg](simpeg/) | 607 | Simulation and inversion (EM, DC, magnetics, gravity) |
| [devito](devito/) | 658 | Symbolic PDE solver for wave propagation |
| [pylops](pylops/) | 503 | Linear operators for inverse problems |
| [pygimli](pygimli/) | 456 | Multi-method geophysical inversion (ERT, SRT, IP) |

### Potential Fields
| Skill | Stars | Description |
|-------|-------|-------------|
| [harmonica](harmonica/) | 273 | Gravity and magnetic data processing and forward modelling |

### Rock Physics
| Skill | Stars | Description |
|-------|-------|-------------|
| [bruges](bruges/) | 300 | Geophysical equations, AVO, Gassmann fluid substitution |

### Spatial Analysis & Geostatistics
| Skill | Stars | Description |
|-------|-------|-------------|
| [verde](verde/) | 648 | Spatial data gridding and interpolation (ML-style API) |
| [geostatspy](geostatspy/) | 554 | Geostatistics, variograms, kriging (GSLIB-style) |
| [scikit-gstat](scikit-gstat/) | 246 | Geostatistics with scikit-learn style API |

### Hydrology
| Skill | Stars | Description |
|-------|-------|-------------|
| [pastas](pastas/) | 416 | Groundwater time series analysis and modelling |

### Surface Processes
| Skill | Stars | Description |
|-------|-------|-------------|
| [landlab](landlab/) | 414 | Landscape evolution and surface process modelling |

### Structural Geology
| Skill | Stars | Description |
|-------|-------|-------------|
| [mplstereonet](mplstereonet/) | 201 | Stereonet plots for orientation data |

### Geochemistry
| Skill | Stars | Description |
|-------|-------|-------------|
| [pyrolite](pyrolite/) | 152 | Geochemical data analysis, REE patterns, spider diagrams |

### Ground-Penetrating Radar
| Skill | Stars | Description |
|-------|-------|-------------|
| [gprpy](gprpy/) | 259 | GPR data processing and visualization |

### Magnetotellurics
| Skill | Stars | Description |
|-------|-------|-------------|
| [mtpy](mtpy/) | 155 | Magnetotelluric data processing and modelling |

### Scientific Data Formats
| Skill | Stars | Description |
|-------|-------|-------------|
| [xarray](xarray/) | 4.1k | NetCDF, multi-dimensional arrays, climate/ocean data |

### Visualization
| Skill | Stars | Description |
|-------|-------|-------------|
| [pyvista](pyvista/) | 3.5k | 3D visualization and mesh analysis |

### Utilities
| Skill | Stars | Description |
|-------|-------|-------------|
| [pooch](pooch/) | 714 | Data file fetching and caching |

---

## Skills by Star Count

| Rank | Skill | Stars | Category |
|------|-------|-------|----------|
| 1 | xarray | 4,100 | Data Formats |
| 2 | pyvista | 3,500 | Visualization |
| 3 | obspy | 1,300 | Seismology |
| 4 | gempy | 1,200 | 3D Modelling |
| 5 | pooch | 714 | Utilities |
| 6 | devito | 658 | Simulation |
| 7 | verde | 648 | Geostatistics |
| 8 | simpeg | 607 | Inversion |
| 9 | segyio | 557 | Seismic |
| 10 | geostatspy | 554 | Geostatistics |

---

## Installation by Domain

```bash
# Full installation (all skills)
pip install obspy segyio disba lasio welly dlisio striplog petropy \
    gempy LoopStructural gemgis simpeg devito pylops pygimli \
    harmonica bruges verde geostatspy scikit-gstat pastas landlab \
    mplstereonet pyrolite gprpy mtpy xarray netcdf4 pyvista pooch
```

### Domain-specific

```bash
# Seismic & Seismology
pip install obspy segyio disba

# Well Logs & Petrophysics
pip install lasio welly dlisio striplog petropy

# 3D Geological Modelling
pip install gempy LoopStructural gemgis pyvista

# Geophysical Inversion
pip install simpeg devito pylops pygimli

# Potential Fields & Rock Physics
pip install harmonica bruges

# Geostatistics & Spatial
pip install verde geostatspy scikit-gstat

# Climate & Ocean Data
pip install xarray netcdf4 h5netcdf dask

# Hydrology & Surface
pip install pastas landlab

# Structural Geology & Geochemistry
pip install mplstereonet pyrolite

# Near-surface Geophysics
pip install gprpy mtpy pygimli
```
