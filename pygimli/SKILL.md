---
name: pygimli
description: |
  Multi-method geophysical modelling and inversion framework. Use when Claude needs to:
  (1) Perform electrical resistivity tomography (ERT) inversion, (2) Run seismic refraction
  tomography (SRT), (3) Model induced polarization (IP) data, (4) Simulate ground penetrating
  radar (GPR), (5) Create finite element meshes for geophysical problems, (6) Perform joint
  inversions of multiple datasets, (7) Forward model geophysical responses, (8) Analyze
  time-lapse monitoring data.
---

# pyGIMLi - Geophysical Inversion

## Quick Reference

```python
import pygimli as pg
from pygimli.physics import ert, srt

# Load ERT data
data = ert.load("survey.ohm")

# Invert
mgr = ert.ERTManager(data)
model = mgr.invert(lam=20, verbose=True)

# View result
mgr.showResult()
```

## Key Classes

| Class | Purpose |
|-------|---------|
| `pg.Mesh` | Finite element meshes |
| `pg.DataContainer` | Survey data and geometry |
| `pg.Inversion` | Base inversion framework |
| `ert.ERTManager` | ERT processing and inversion |
| `srt.SRTManager` | Seismic refraction inversion |

## Essential Operations

### Load and View ERT Data
```python
import pygimli as pg
from pygimli.physics import ert

data = ert.load("survey.ohm")
print(f"Measurements: {data.size()}")
ert.showData(data)  # Pseudosection
```

### ERT Inversion
```python
from pygimli.physics import ert

mgr = ert.ERTManager(data)
model = mgr.invert(
    lam=20,          # Regularization
    verbose=True
)
mgr.showResult()
resistivity = mgr.model
```

### Seismic Refraction
```python
from pygimli.physics import srt

data = srt.load("traveltimes.sgt")
mgr = srt.SRTManager(data)
model = mgr.invert(lam=30, zWeight=0.3)
mgr.showResult()
```

### Create Custom Mesh
```python
import pygimli as pg
from pygimli.physics import ert

data = ert.load("survey.ohm")
mesh = pg.meshtools.createParaMesh(
    data.sensors(),
    quality=34.0,
    paraMaxCellSize=5,
    boundary=2
)
pg.show(mesh)
```

### Save and Export
```python
# Save mesh and model
mgr.mesh.save("result_mesh.bms")
pg.save(model, "resistivity_model.vector")

# Export to VTK for ParaView
mgr.mesh.exportVTK("result", mgr.model)
```

## Array Types

| Code | Array |
|------|-------|
| `wa` | Wenner-alpha |
| `wb` | Wenner-beta |
| `dd` | Dipole-dipole |
| `pd` | Pole-dipole |
| `pp` | Pole-pole |
| `slm` | Schlumberger |
| `gr` | Gradient |

## Data Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| BERT/pyGIMLi | .ohm | Unified data format |
| Syscal | .txt | IRIS export |
| Res2DInv | .dat | 2D inversion format |
| ABEM | .ohm | ABEM Terrameter |
| SRT | .sgt | Seismic traveltimes |

## Inversion Tips

1. **Start with higher lambda** (50-100) and decrease
2. **Check data quality** - remove outliers before inversion
3. **Use zWeight < 1** for layered structures
4. **Check coverage** - low coverage = poorly resolved
5. **Chi-squared ~ 1** indicates good fit without overfitting

## References

- **[Geophysical Methods](references/methods.md)** - Supported methods and workflows
- **[Mesh Generation](references/mesh.md)** - Mesh creation and quality control

## Scripts

- **[scripts/ert_inversion.py](scripts/ert_inversion.py)** - Complete ERT inversion workflow
