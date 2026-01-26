---
name: simpeg
description: Simulation and Parameter Estimation in Geophysics. Framework for geophysical forward modeling and inversion including EM, DC, IP, magnetics, and gravity.
---

# SimPEG - Geophysical Simulation & Inversion

Help users perform geophysical forward modelling and inversion for various survey types.

## Installation

```bash
pip install simpeg
```

## Core Concepts

### Framework Components
| Component | Description |
|-----------|-------------|
| Mesh | Discretization of model space |
| Survey | Data acquisition geometry |
| Simulation | Forward modelling engine |
| Data | Observed/predicted data |
| Inversion | Parameter estimation |
| Regularization | Model constraints |

### Supported Methods
- DC Resistivity
- Induced Polarization (IP)
- Electromagnetics (EM)
- Magnetotellurics (MT)
- Magnetics
- Gravity
- Seismic (limited)

## Common Workflows

### 1. Create Mesh
```python
from discretize import TensorMesh
import numpy as np

# 1D Mesh
hz = np.ones(50) * 10  # 50 cells, 10m each
mesh1d = TensorMesh([hz], origin='N')  # N = top at 0

# 2D Tensor Mesh
hx = np.ones(100) * 20  # 100 cells, 20m
hz = np.ones(50) * 10   # 50 cells, 10m
mesh2d = TensorMesh([hx, hz], origin='CN')  # Centered in x

# 3D Tensor Mesh
hx = np.ones(50) * 25
hy = np.ones(50) * 25
hz = np.ones(30) * 10
mesh3d = TensorMesh([hx, hy, hz], origin='CCN')
```

### 2. DC Resistivity Forward Model
```python
from simpeg.electromagnetics.static import resistivity as dc
from simpeg import maps
import numpy as np

# Create mesh
hx = np.ones(100) * 5
hz = np.ones(50) * 5
mesh = TensorMesh([hx, hz], origin='CN')

# Define survey (dipole-dipole)
n_electrodes = 20
electrode_spacing = 10
electrode_locs = np.c_[
    np.linspace(-95, 95, n_electrodes),
    np.zeros(n_electrodes)
]

# Create survey
source_list = []
for i in range(n_electrodes - 3):
    # Current electrodes
    a_loc = electrode_locs[i]
    b_loc = electrode_locs[i + 1]

    # Potential electrodes
    m_loc = electrode_locs[i + 2]
    n_loc = electrode_locs[i + 3]

    rx = dc.receivers.Dipole(np.array([m_loc]), np.array([n_loc]))
    src = dc.sources.Dipole([rx], a_loc, b_loc)
    source_list.append(src)

survey = dc.Survey(source_list)

# Create model (resistivity)
model = np.ones(mesh.nC) * 100  # 100 ohm-m background
# Add anomaly
anomaly_inds = (mesh.cell_centers[:, 0] > -20) & \
               (mesh.cell_centers[:, 0] < 20) & \
               (mesh.cell_centers[:, 1] > -50) & \
               (mesh.cell_centers[:, 1] < -20)
model[anomaly_inds] = 10  # 10 ohm-m anomaly

# Create simulation
simulation = dc.Simulation2DNodal(
    mesh,
    survey=survey,
    sigmaMap=maps.ExpMap(mesh),  # Log conductivity
    solver=Solver
)

# Forward model
dpred = simulation.dpred(np.log(1/model))  # Input is log(conductivity)
```

### 3. Magnetic Forward Model
```python
from simpeg.potential_fields import magnetics
from simpeg import maps
import numpy as np

# Create mesh
hx = hy = hz = np.ones(50) * 20
mesh = TensorMesh([hx, hy, hz], origin='CCC')

# Define survey
receiver_locs = np.c_[
    np.linspace(-400, 400, 41),
    np.zeros(41),
    np.ones(41) * 50  # 50m above ground
]

# Total field anomaly
rx = magnetics.receivers.Point(receiver_locs, components='tmi')
src = magnetics.sources.UniformBackgroundField(
    receiver_list=[rx],
    amplitude=50000,  # nT
    inclination=60,
    declination=10
)
survey = magnetics.Survey(src)

# Create susceptibility model
model = np.zeros(mesh.nC)
# Add anomaly
sphere_inds = np.sqrt(
    mesh.cell_centers[:, 0]**2 +
    mesh.cell_centers[:, 1]**2 +
    mesh.cell_centers[:, 2]**2
) < 100
model[sphere_inds] = 0.05  # SI susceptibility

# Create simulation
simulation = magnetics.Simulation3DIntegral(
    mesh,
    survey=survey,
    chiMap=maps.IdentityMap(nP=mesh.nC)
)

# Forward model
dpred = simulation.dpred(model)
```

### 4. Run Inversion
```python
from simpeg import (
    data_misfit, regularization, optimization,
    inverse_problem, inversion, directives
)

# Observed data (with noise)
dobs = dpred + np.random.randn(len(dpred)) * 0.01 * np.abs(dpred)

# Data object
data = data.Data(survey, dobs=dobs, standard_deviation=0.01*np.abs(dobs))

# Data misfit
dmis = data_misfit.L2DataMisfit(data=data, simulation=simulation)

# Regularization
reg = regularization.WeightedLeastSquares(
    mesh,
    alpha_s=1e-4,
    alpha_x=1,
    alpha_y=1,
    alpha_z=1
)

# Optimization
opt = optimization.InexactGaussNewton(maxIter=20)

# Inverse problem
inv_prob = inverse_problem.BaseInvProblem(dmis, reg, opt)

# Directives
beta_schedule = directives.BetaSchedule(coolingFactor=2, coolingRate=1)
target_misfit = directives.TargetMisfit()

# Run inversion
inv = inversion.BaseInversion(inv_prob, directiveList=[beta_schedule, target_misfit])

# Starting model
m0 = np.zeros(mesh.nC)

# Invert
mrec = inv.run(m0)
```

### 5. Gravity Forward Model
```python
from simpeg.potential_fields import gravity
from simpeg import maps

# Survey setup
rx_locs = np.c_[X.flatten(), Y.flatten(), np.zeros(X.size)]
rx = gravity.receivers.Point(rx_locs, components='gz')
src = gravity.sources.SourceField(receiver_list=[rx])
survey = gravity.Survey(src)

# Density model (g/cc)
model = np.zeros(mesh.nC)
model[anomaly_inds] = 0.5  # Density contrast

# Simulation
simulation = gravity.Simulation3DIntegral(
    mesh,
    survey=survey,
    rhoMap=maps.IdentityMap(nP=mesh.nC)
)

# Forward model
gz = simulation.dpred(model)
```

### 6. 1D EM Forward Model
```python
from simpeg.electromagnetics import time_domain as tdem
from simpeg import maps

# 1D layered model
thicknesses = np.array([10, 20, 50])  # Layer thicknesses
resistivities = np.array([100, 10, 100, 1000])  # Including halfspace

# Create simulation
times = np.logspace(-5, -2, 31)
rx = tdem.receivers.PointMagneticFluxTimeDerivative(
    np.array([[0, 0, 0]]),
    times,
    orientation='z'
)
src = tdem.sources.MagDipole([rx], location=np.array([0, 0, 0]))
survey = tdem.Survey([src])

# Run forward model
simulation = tdem.Simulation1DLayered(
    survey=survey,
    thicknesses=thicknesses,
    sigmaMap=maps.ExpMap(nP=len(resistivities))
)

dpred = simulation.dpred(np.log(1/resistivities))
```

### 7. Tree Mesh for Efficiency
```python
from discretize import TreeMesh

# Create tree mesh
h = np.ones(64) * 25
mesh = TreeMesh([h, h, h], origin='CCC')

# Refine around points of interest
mesh.refine_points(receiver_locs, levels=3)
mesh.refine_box(
    [-100, -100, -200],
    [100, 100, 0],
    levels=2
)
```

## Key Maps

| Map | Description |
|-----|-------------|
| `IdentityMap` | No transformation |
| `ExpMap` | Exponential (log parameters) |
| `LogMap` | Logarithmic |
| `ReciprocalMap` | 1/x (resistivity to conductivity) |
| `Wires` | Split model into components |

## Tips

1. **Use log parameters** for positive quantities (resistivity, susceptibility)
2. **Start with coarse mesh** - refine after initial tests
3. **Check data fit** - plot observed vs predicted
4. **Tune regularization** - balance data fit and model smoothness
5. **Use TreeMesh** for 3D efficiency

## Common Parameters

| Property | Typical Range | Units |
|----------|---------------|-------|
| Resistivity | 1-10000 | ohm-m |
| Conductivity | 0.0001-1 | S/m |
| Susceptibility | 0-0.1 | SI |
| Density | -1 to 1 (contrast) | g/cc |

## Resources

- Documentation: https://simpeg.xyz/
- GitHub: https://github.com/simpeg/simpeg
- Examples: https://simpeg.xyz/gallery/
- Tutorials: https://simpeg.xyz/tutorials/
