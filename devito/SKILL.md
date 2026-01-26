---
name: devito
description: Finite-difference PDE solver with automatic code generation. Define PDEs symbolically in Python and run optimized kernels on CPUs/GPUs for wave propagation and more.
---

# Devito - Symbolic PDE Solver

Help users solve partial differential equations using symbolic definitions and automatic code generation.

## Installation

```bash
pip install devito
```

## Core Concepts

### Key Classes
| Class | Purpose |
|-------|---------|
| `Grid` | Computational domain definition |
| `Function` | Spatial field on grid |
| `TimeFunction` | Time-dependent field |
| `SparseFunction` | Point sources/receivers |
| `Operator` | Compiled computation kernel |

### Workflow
1. Define Grid (domain)
2. Create Functions (fields)
3. Write equations symbolically
4. Create Operator (auto-generates code)
5. Run Operator

## Common Workflows

### 1. Create Computational Grid
```python
from devito import Grid

# 2D Grid
grid = Grid(
    shape=(101, 101),     # nx, nz
    extent=(1000., 1000.) # Physical size in meters
)

# 3D Grid
grid3d = Grid(
    shape=(101, 101, 51),
    extent=(1000., 1000., 500.)
)

# Access properties
print(f"Spacing: {grid.spacing}")
print(f"Dimensions: {grid.dimensions}")
```

### 2. Define Spatial Functions
```python
from devito import Function

# Velocity model
v = Function(name='v', grid=grid, space_order=2)

# Initialize with values
import numpy as np
v.data[:] = 1500.  # m/s background

# Add anomaly
v.data[40:60, 40:60] = 2000.  # Higher velocity block
```

### 3. Define Time-Dependent Functions
```python
from devito import TimeFunction

# Pressure field (wavefield)
p = TimeFunction(
    name='p',
    grid=grid,
    time_order=2,   # 2nd order in time
    space_order=4   # 4th order in space
)

# Access time indices
# p[t], p[t-1], p[t+1] for time stepping
```

### 4. 2D Acoustic Wave Equation
```python
from devito import Grid, TimeFunction, Function, Eq, solve, Operator
import numpy as np

# Setup
grid = Grid(shape=(101, 101), extent=(1000., 1000.))
v = Function(name='v', grid=grid, space_order=4)
v.data[:] = 1500.

# Wavefield
p = TimeFunction(name='p', grid=grid, time_order=2, space_order=4)

# Wave equation: d²p/dt² = v² * (d²p/dx² + d²p/dz²)
pde = p.dt2 - v**2 * p.laplace

# Solve for p[t+1]
stencil = Eq(p.forward, solve(pde, p.forward))

# Create operator
op = Operator([stencil])
```

### 5. Add Source and Receivers
```python
from devito import SparseTimeFunction

# Source wavelet
t0 = 0.05  # Start time
f0 = 10.   # Dominant frequency

time_range = TimeAxis(start=0., stop=1., step=grid.stepping_dim.spacing)

src = RickerSource(
    name='src',
    grid=grid,
    f0=f0,
    npoint=1,
    time_range=time_range
)
src.coordinates.data[0, :] = [500., 20.]  # Source location

# Receivers
nreceivers = 101
rec = Receiver(
    name='rec',
    grid=grid,
    npoint=nreceivers,
    time_range=time_range
)
rec.coordinates.data[:, 0] = np.linspace(0., 1000., nreceivers)
rec.coordinates.data[:, 1] = 20.  # Receiver depth
```

### 6. Complete Forward Modeling
```python
from devito import Grid, TimeFunction, Function, Eq, solve, Operator
from examples.seismic import RickerSource, Receiver, TimeAxis
import numpy as np

# Grid and model
grid = Grid(shape=(101, 101), extent=(1000., 1000.))
v = Function(name='v', grid=grid, space_order=4)
v.data[:] = 1500.
v.data[40:60, 40:60] = 2000.

# Time setup
dt = 0.5  # ms
nt = 1000
time_range = TimeAxis(start=0., stop=nt*dt, step=dt)

# Source
src = RickerSource(name='src', grid=grid, f0=10., npoint=1, time_range=time_range)
src.coordinates.data[0, :] = [500., 20.]

# Receivers
rec = Receiver(name='rec', grid=grid, npoint=101, time_range=time_range)
rec.coordinates.data[:, 0] = np.linspace(0., 1000., 101)
rec.coordinates.data[:, 1] = 20.

# Wavefield
p = TimeFunction(name='p', grid=grid, time_order=2, space_order=4)

# Equations
stencil = Eq(p.forward, solve(p.dt2 - v**2 * p.laplace, p.forward))
src_term = src.inject(field=p.forward, expr=src * dt**2 * v**2)
rec_term = rec.interpolate(expr=p)

# Operator
op = Operator([stencil] + src_term + rec_term)

# Run
op(time_M=nt-1, dt=dt)

# Shot record
shot_data = rec.data
```

### 7. 3D Wave Propagation
```python
# 3D Grid
grid = Grid(shape=(101, 101, 51), extent=(1000., 1000., 500.))

# 3D velocity
v = Function(name='v', grid=grid, space_order=4)
v.data[:] = 1500.

# 3D wavefield
p = TimeFunction(name='p', grid=grid, time_order=2, space_order=4)

# Same equation works for 3D (Laplacian adapts automatically)
stencil = Eq(p.forward, solve(p.dt2 - v**2 * p.laplace, p.forward))
```

### 8. Absorbing Boundary Conditions
```python
from devito import Function, Eq
import numpy as np

# Create damping function
damp = Function(name='damp', grid=grid)

# Set damping in boundary regions
nbl = 20  # Boundary layer thickness
damp_val = 0.05

# Apply damping
damp.data[:nbl, :] = damp_val * np.linspace(1, 0, nbl)[:, np.newaxis]
damp.data[-nbl:, :] = damp_val * np.linspace(0, 1, nbl)[:, np.newaxis]
damp.data[:, :nbl] = np.maximum(damp.data[:, :nbl], damp_val * np.linspace(1, 0, nbl))
damp.data[:, -nbl:] = np.maximum(damp.data[:, -nbl:], damp_val * np.linspace(0, 1, nbl))

# Modified wave equation with damping
pde = p.dt2 + damp * p.dt - v**2 * p.laplace
```

### 9. Elastic Wave Equation
```python
from devito import VectorTimeFunction, TensorTimeFunction

# Particle velocity (vector)
v = VectorTimeFunction(name='v', grid=grid, time_order=1, space_order=4)

# Stress tensor
tau = TensorTimeFunction(name='tau', grid=grid, time_order=1, space_order=4)

# Elastic parameters
lam = Function(name='lam', grid=grid)  # Lambda
mu = Function(name='mu', grid=grid)     # Shear modulus
rho = Function(name='rho', grid=grid)   # Density

# Elastic wave equations (simplified)
# dv/dt = (1/rho) * div(tau)
# dtau/dt = C : grad(v)  # C is stiffness tensor
```

### 10. GPU Execution
```python
from devito import configuration

# Set GPU backend
configuration['platform'] = 'nvidiaX'  # or 'amdgpuX'
configuration['compiler'] = 'pgcc'     # or appropriate compiler

# Create operator (will generate GPU code)
op = Operator([stencil])

# Run on GPU
op(time_M=nt-1)
```

### 11. Save Snapshots
```python
from devito import TimeFunction

# Create wavefield with save option
p = TimeFunction(
    name='p',
    grid=grid,
    time_order=2,
    space_order=4,
    save=nt  # Save all timesteps
)

# After running, access snapshots
snapshot_100 = p.data[100, :, :]
```

## Key Symbolic Operations

| Operation | Syntax |
|-----------|--------|
| Time derivative | `p.dt`, `p.dt2` |
| Spatial derivative | `p.dx`, `p.dy`, `p.dz` |
| Laplacian | `p.laplace` |
| Forward in time | `p.forward` |
| Backward in time | `p.backward` |

## Tips

1. **Start simple** - 2D before 3D
2. **Check stability** - CFL condition: `dt < dx / (v_max * sqrt(ndim))`
3. **Use absorbing boundaries** - Avoid reflections
4. **Higher space_order** - More accurate but slower
5. **Profile first** - Use Devito's built-in profiling

## Space Order vs Accuracy

| Order | Points | Error |
|-------|--------|-------|
| 2 | 3 | O(h²) |
| 4 | 5 | O(h⁴) |
| 8 | 9 | O(h⁸) |

## Resources

- Documentation: https://www.devitoproject.org/
- GitHub: https://github.com/devitocodes/devito
- Examples: https://github.com/devitocodes/devito/tree/master/examples
- Tutorials: https://www.devitoproject.org/tutorials
