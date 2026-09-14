---
name: geophysical-inversion
description: |
  Geophysical data inversion workflow from data loading through mesh
  creation, forward modelling, inversion, and result visualization.
  Use when inverting ERT, magnetics, gravity, or EM survey data.
license: MIT
metadata:
  skill_type: workflow
  version: 1.0.2
  author: Geoscience Skills
  tags: '["Geophysical Inversion", "ERT", "Magnetics", "Gravity", "EM", "Workflow"]'
  dependencies: '["simpeg==0.25.2", "pygimli==1.6.0", "verde==1.9.0", "pyvista==0.49.0"]'
  complements: '["simpeg", "pygimli", "verde", "pyvista"]'
  workflow_role: modelling
---

# Geophysical Inversion Workflow

End-to-end pipeline for inverting geophysical data, from survey data loading
through mesh creation, forward modelling, inversion, gridding, and 3D
visualization of recovered physical property models.

## Skill Chain

```text
simpeg / pygimli      verde            pyvista
[Mesh + Inversion] --> [Gridding]    --> [3D Visualization]
  |                     |                |
  Survey geometry       Interpolate      Volume render
  Forward model         Grid to raster   Slice views
  Misfit + reg          Trend removal    Overlay data
  Recover model         Cross-validate   Export mesh
```

## Decision Points: SimPEG vs pyGIMLi

| Criterion | SimPEG | pyGIMLi |
|-----------|--------|---------|
| DC resistivity / ERT | Yes | Yes (simpler API) |
| Magnetics | Yes | Limited |
| Gravity | Yes | Limited |
| Electromagnetics (TDEM, FDEM) | Yes | No |
| Seismic refraction (SRT) | No | Yes |
| Induced polarization | Yes | Yes |
| Built-in electrode arrays | Manual setup | Built-in (Wenner, Schlumberger, etc.) |
| Mesh types | TensorMesh, TreeMesh, CurvilinearMesh | Triangular, tetrahedral, structured |
| Joint inversion | Yes (Wires maps) | Limited |
| API complexity | More boilerplate, more flexible | Less boilerplate, opinionated |

**Rule of thumb**: Use pyGIMLi for standard near-surface ERT/SRT surveys with
conventional arrays. Use SimPEG for multi-physics, EM methods, potential fields,
or research-grade custom inversions.

## Step-by-Step Orchestration

Choose **one** inversion branch. Each branch explicitly produces
`cell_centers_xz_m`, `resistivity_ohm_m` and `model_vtk` for the shared stages.
X is distance along the profile in metres, Z is elevation in metres (negative
below the surface); resistivity is in ohm metres. These short synthetic runs
check API and data flow, not survey resolution or field-model reliability.

### Stage 1a: Inversion with SimPEG (DC Resistivity Example)

```python
# example: simpeg-inversion
import numpy as np
from discretize import TensorMesh
from simpeg.electromagnetics.static import resistivity as dc
from simpeg import maps, data, data_misfit, regularization
from simpeg import optimization, inverse_problem, inversion, directives

# 1. Small synthetic 2D mesh. SimPEG's second coordinate represents elevation.
hx = np.full(24, 5.0)
hz = np.full(12, 5.0)
mesh = TensorMesh([hx, hz], origin='CN')

# 2. Build survey (dipole-dipole)
n_electrodes = 8
electrode_spacing = 5.0
elec_x = (np.arange(n_electrodes) - (n_electrodes - 1) / 2) * electrode_spacing
elec_locs = np.c_[elec_x, np.zeros(n_electrodes)]

source_list = []
for i in range(n_electrodes - 3):
    rx = dc.receivers.Dipole(elec_locs[[i+2]], elec_locs[[i+3]])
    src = dc.sources.Dipole([rx], elec_locs[i], elec_locs[i+1])
    source_list.append(src)
survey = dc.Survey(source_list)

# 3. Forward model (for synthetic test)
sigma_true = np.ones(mesh.nC) * 0.01  # 100 ohm-m background
sigma_true[mesh.cell_centers[:, 1] < -20] = 0.1  # Conductive layer
simulation = dc.Simulation2DNodal(
    mesh, survey=survey, sigmaMap=maps.ExpMap(mesh)
)
clean_data = simulation.dpred(np.log(sigma_true))
# Voltage / unit-current uncertainties: fractional term plus nonzero floor.
standard_deviation = 0.02 * np.abs(clean_data) + 1e-6
rng = np.random.default_rng(42)
dobs = clean_data + standard_deviation * rng.standard_normal(survey.nD)

# 4. Set up inversion
obs_data = data.Data(survey, dobs=dobs, standard_deviation=standard_deviation)
dmis = data_misfit.L2DataMisfit(data=obs_data, simulation=simulation)
reg = regularization.WeightedLeastSquares(
    mesh, alpha_s=1e-4, alpha_x=1, alpha_y=1
)
opt = optimization.InexactGaussNewton(maxIter=3)
inv_prob = inverse_problem.BaseInvProblem(dmis, reg, opt)
dir_list = [
    directives.BetaEstimate_ByEig(beta0_ratio=1.0, random_seed=42),
    directives.BetaSchedule(coolingFactor=2),
    directives.TargetMisfit()
]
inv = inversion.BaseInversion(inv_prob, directiveList=dir_list)

# 5. Run inversion
m0 = np.log(np.ones(mesh.nC) * 0.01)  # Starting model
mrec = inv.run(m0)
sigma_rec = np.exp(mrec)  # Recovered conductivity
```

Convert this branch's result on its **own mesh**. `RectilinearGrid` also
preserves nonuniform cell widths if padding cells are added later. VTK uses
coordinates `(x, 0, z)` for this vertical section; SimPEG's cell order already
has X varying fastest.

```python
# example: simpeg-result
import numpy as np
import pyvista as pv

cell_centers_xz_m = mesh.cell_centers.copy()
resistivity_ohm_m = 1.0 / np.asarray(sigma_rec)
if resistivity_ohm_m.shape != (mesh.nC,) or not np.all(np.isfinite(resistivity_ohm_m) & (resistivity_ohm_m > 0)):
    raise ValueError('Expected one finite positive resistivity per SimPEG cell')
model_vtk = pv.RectilinearGrid(mesh.nodes_x, np.array([0.0]), mesh.nodes_y)
model_vtk.cell_data['resistivity_ohm_m'] = resistivity_ohm_m
```

### Stage 1b: Inversion with pyGIMLi (ERT Example)

Use an existing `ert_survey.dat` with `rhoa` and fractional uncertainty `err`,
or create this small **synthetic homogeneous-earth** survey first:

```python
# example: pygimli-synthetic
import numpy as np
import pygimli as pg
from pygimli.physics import ert

scheme = ert.createData(elecs=np.linspace(0., 35., 8), schemeName='dd')
# Include ERT boundary markers and padding around the parameter domain.
forward_mesh = ert.createInversionMesh(scheme, paraMaxCellSize=10)
synthetic = ert.simulate(
    mesh=forward_mesh, scheme=scheme, res=100.0,
    noiseLevel=0.03, noiseAbs=1e-6, seed=42, verbose=False,
)
synthetic.save('ert_survey.dat')
```

```python
# example: pygimli-inversion
import numpy as np
import pygimli as pg
from pygimli.physics import ert

# 1. Load and validate positive apparent resistivity and fractional uncertainty.
ert_data = ert.load('ert_survey.dat')
rhoa = np.asarray(ert_data['rhoa'])
relative_error = np.asarray(ert_data['err'])
valid = np.isfinite(rhoa) & (rhoa > 0) & np.isfinite(relative_error) & (relative_error > 0)
ert_data.remove(~valid)
if ert_data.size() == 0:
    raise ValueError('No valid ERT measurements remain')

# 2. Short demonstration inversion; increase iterations for convergence studies.
mgr = ert.ERTManager(ert_data)
mgr.invert(lam=20, paraMaxCellSize=20, maxIter=3, verbose=False)
```

The model belongs to `mgr.paraDomain`, not the forward mesh or a SimPEG mesh.
The following block needs only this branch and never reads `sigma_rec`.

```python
# example: pygimli-result
import numpy as np
import pygimli as pg
import pyvista as pv

parameter_mesh = pg.Mesh(mgr.paraDomain)
cell_centers_xz_m = np.asarray(parameter_mesh.cellCenters())[:, :2]
resistivity_ohm_m = np.asarray(mgr.model)
if resistivity_ohm_m.shape != (parameter_mesh.cellCount(),) or not np.all(np.isfinite(resistivity_ohm_m) & (resistivity_ohm_m > 0)):
    raise ValueError('Expected one finite positive resistivity per pyGIMLi parameter cell')
parameter_mesh['resistivity_ohm_m'] = resistivity_ohm_m
parameter_mesh.exportVTK('pygimli_parameter_model.vtk')
model_vtk = pv.read('pygimli_parameter_model.vtk')
# pyGIMLi's vertical 2D coordinate is Y; map it explicitly to VTK Z.
points = model_vtk.points.copy()
model_vtk.points = np.column_stack((points[:, 0], points[:, 2], points[:, 1]))
```

### Stage 2: Gridding and Interpolation (verde)

```python
# example: inversion-gridding
import numpy as np
import verde as vd

# Both branches supply this common representation.
coordinates = (cell_centers_xz_m[:, 0], cell_centers_xz_m[:, 1])
region = vd.get_region(coordinates)

# Spline gridding
spline = vd.Spline(damping=1e-3)
spline.fit(coordinates, data=np.log10(resistivity_ohm_m))

raster = spline.grid(spacing=2.5, region=region,
                     dims=['elevation_m', 'distance_m'],
                     data_names=['log10_resistivity'])
```

This optional raster is a smoothed display product. Mask areas outside the
parameter domain and poorly constrained cells using the inversion's coverage;
it is not a replacement for the original mesh or a new inversion result.

### Stage 3: Visualization (pyvista)

Export either branch without changing its cell geometry or property association:

```python
# example: inversion-export
exported_model = model_vtk.cast_to_unstructured_grid()
exported_model.save('recovered_resistivity.vtu')
```

```python
import pyvista as pv

plotter = pv.Plotter()
plotter.add_mesh(model_vtk, scalars='resistivity_ohm_m', cmap='Spectral',
                  log_scale=True, clim=[10, 1000])
plotter.add_scalar_bar('Resistivity (ohm-m)')
plotter.view_xz()
plotter.show()
```

## Common Pipelines

### Standard ERT Inversion
```text
- [ ] Load ERT data (electrode positions, configurations, apparent resistivity)
- [ ] QC data: remove negative rhoa, check reciprocals, filter by error threshold
- [ ] Choose framework: pyGIMLi for standard arrays, SimPEG for custom setups
- [ ] Create mesh appropriate for electrode layout and target depth
- [ ] Set up forward simulation with survey geometry
- [ ] Configure inversion: data misfit, regularization weight, starting model
- [ ] Run inversion, monitor convergence (target chi-squared ~ 1)
- [ ] Plot recovered resistivity model
- [ ] Overlay electrode positions and data fit
- [ ] Export model to VTK or gridded raster
```

### Gravity or Magnetics Inversion (SimPEG)
```text
- [ ] Load survey data (station locations, observed field, regional correction)
- [ ] Remove regional trend if needed (polynomial or upward continuation)
- [ ] Create TensorMesh or TreeMesh covering survey area and target depth
- [ ] Build survey object with receiver locations and source field
- [ ] Set up Simulation3DIntegral with appropriate physical property map
- [ ] Configure L2 data misfit and Tikhonov regularization
- [ ] Add depth weighting to counteract resolution decay
- [ ] Run inversion from homogeneous starting model
- [ ] Visualize recovered density/susceptibility with pyvista
- [ ] Validate against known geology or borehole constraints
```

### Synthetic Study (Forward + Inversion)
```text
- [ ] Define true model with target anomaly on mesh
- [ ] Create survey geometry matching planned field layout
- [ ] Run forward simulation to generate synthetic data
- [ ] Add realistic noise (percentage + floor)
- [ ] Run inversion on noisy synthetic data
- [ ] Compare recovered model to true model
- [ ] Test sensitivity to regularization parameters
- [ ] Assess resolution by varying survey design
```

## When to Use

Use the geophysical inversion workflow when:

- Inverting ERT, magnetics, gravity, or EM survey data for subsurface models
- Designing geophysical surveys through synthetic forward-inversion studies
- Processing and visualizing inverted physical property models
- Comparing results from different inversion parameters or methods

Use individual domain skills when:
- Only creating meshes or survey geometries (use `simpeg` or `pygimli` alone)
- Only gridding scattered data (use `verde` alone)
- Only visualizing existing model files (use `pyvista` alone)

## Common Issues

| Issue | Solution |
|-------|----------|
| Inversion does not converge | Check data uncertainties; increase regularization (`lam` or `alpha_s`) |
| Artifacts near surface | Add depth weighting or refine mesh near electrodes |
| Memory error on 3D mesh | Use TreeMesh (SimPEG) with adaptive refinement near sources |
| Negative apparent resistivity | Remove bad data points before inversion |
| Over-fitting (chi-squared << 1) | Increase trade-off parameter; check noise estimates |
| Model too smooth | Reduce regularization weight; try sparse norms (L1) |
| pyGIMLi mesh too coarse | Reduce maximum cell size and inspect `mgr.paraDomain`; quality controls triangle angles |

## API Sources and Verification

- [SimPEG DC resistivity tutorial](https://simpeg.xyz/user-tutorials/inv-dcr-2d/).
- [pyGIMLi ERTManager model export](https://www.pygimli.org/_modules/pygimli/physics/ert/ertManager/)
  associates the recovered model with `paraDomain`.
- [PyVista RectilinearGrid](https://docs.pyvista.org/api/core/_autosummary/pyvista.RectilinearGrid.html)
  preserves the node coordinates of nonuniform tensor meshes.
- `tests/science/test_model_examples.py` executes the marked short synthetic
  inversions, each branch's adapter, the shared gridding and VTK export. This
  verifies API/data-flow and geometry, not field-data convergence, uncertainty,
  depth of investigation, or the interactive renderer.
