# Devito Operators and Stencils

## Table of Contents
- [Operator Basics](#operator-basics)
- [Equation Types](#equation-types)
- [Stencil Construction](#stencil-construction)
- [Boundary Conditions](#boundary-conditions)
- [Advanced Operators](#advanced-operators)

## Operator Basics

### Creating Operators
```python
from devito import Operator, Eq

# Single equation
op = Operator([stencil])

# Multiple equations
op = Operator([stencil1, stencil2, src_term, rec_term])

# With name for profiling
op = Operator([stencil], name='forward')
```

### Running Operators
```python
# Basic execution
op(time_M=nt-1)

# With explicit time step
op(time_M=nt-1, dt=0.5)

# With time range
op(time_m=100, time_M=500, dt=0.5)
```

## Equation Types

### Eq - Standard Equation
```python
from devito import Eq

# Time-stepping stencil
stencil = Eq(p.forward, solve(pde, p.forward))

# Direct assignment
stencil = Eq(p.forward, 2*p - p.backward + dt**2 * v**2 * p.laplace)
```

### Inc - Incremental Update
```python
from devito import Inc

# Accumulate values (e.g., source injection)
src_inject = Inc(p, src * dt**2)
```

### Conditional Equations
```python
from devito import Eq, ConditionalDimension

# Apply only where condition is true
cond = ConditionalDimension(name='cond', parent=time, condition=time > 10)
eq = Eq(p.forward, expr, implicit_dims=[cond])
```

## Stencil Construction

### Acoustic Wave Equation (2D/3D)
```python
from devito import Grid, TimeFunction, Function, Eq, solve

grid = Grid(shape=(nx, nz), extent=(x_extent, z_extent))
v = Function(name='v', grid=grid, space_order=so)
p = TimeFunction(name='p', grid=grid, time_order=2, space_order=so)

# PDE: d2p/dt2 = v^2 * laplacian(p)
pde = p.dt2 - v**2 * p.laplace
stencil = Eq(p.forward, solve(pde, p.forward))
```

### Variable Density Acoustic
```python
from devito import div, grad

rho = Function(name='rho', grid=grid, space_order=so)  # Density

# PDE: rho * d2p/dt2 = div(rho * v^2 * grad(p))
pde = rho * p.dt2 - div(rho * v**2 * grad(p))
stencil = Eq(p.forward, solve(pde, p.forward))
```

### Elastic Wave Equation
```python
from devito import VectorTimeFunction, TensorTimeFunction, div, grad

# Particle velocity (vector field)
vel = VectorTimeFunction(name='v', grid=grid, time_order=1, space_order=so)

# Stress tensor
tau = TensorTimeFunction(name='tau', grid=grid, time_order=1, space_order=so)

# Elastic parameters
lam = Function(name='lam', grid=grid)   # Lambda (first Lame parameter)
mu = Function(name='mu', grid=grid)     # Shear modulus
rho = Function(name='rho', grid=grid)   # Density

# Velocity update: dv/dt = (1/rho) * div(tau)
v_update = [Eq(vel[i].forward, vel[i] + dt/rho * div(tau[i, :]))
            for i in range(grid.dim)]

# Stress update (isotropic)
# dtau/dt = lam * div(v) * I + mu * (grad(v) + grad(v).T)
```

### First-Order Acoustic System
```python
# Pressure-velocity formulation
p = TimeFunction(name='p', grid=grid, time_order=1, space_order=so)
vx = TimeFunction(name='vx', grid=grid, time_order=1, space_order=so)
vz = TimeFunction(name='vz', grid=grid, time_order=1, space_order=so)

# dp/dt = -K * div(v)
# dv/dt = -(1/rho) * grad(p)
K = Function(name='K', grid=grid)  # Bulk modulus

p_eq = Eq(p.forward, p - dt * K * (vx.dx + vz.dz))
vx_eq = Eq(vx.forward, vx - dt/rho * p.dx)
vz_eq = Eq(vz.forward, vz - dt/rho * p.dz)
```

## Boundary Conditions

### Absorbing Boundary (Damping Layer)
```python
import numpy as np
from devito import Function, Eq

nbl = 40  # Boundary layer thickness

# Create damping function
damp = Function(name='damp', grid=grid)

# Cosine taper (smooth)
def init_damp(damp, nbl, alpha=0.015):
    data = np.zeros(grid.shape)
    for i in range(nbl):
        val = alpha * (1 - np.cos(np.pi * i / nbl)) / 2
        # Left/right boundaries
        data[i, :] = val
        data[-(i+1), :] = val
        # Top/bottom boundaries
        data[:, i] = np.maximum(data[:, i], val)
        data[:, -(i+1)] = np.maximum(data[:, -(i+1)], val)
    damp.data[:] = data

init_damp(damp, nbl)

# Modified wave equation with damping
pde = p.dt2 + damp * p.dt - v**2 * p.laplace
stencil = Eq(p.forward, solve(pde, p.forward))
```

### Perfectly Matched Layer (PML)
```python
# PML auxiliary fields
phi_x = TimeFunction(name='phi_x', grid=grid, time_order=1, space_order=so)
phi_z = TimeFunction(name='phi_z', grid=grid, time_order=1, space_order=so)

# PML damping profiles
sigma_x = Function(name='sigma_x', grid=grid)
sigma_z = Function(name='sigma_z', grid=grid)

# PML equations (CPML formulation)
# phi_x[n+1] = b_x * phi_x[n] + a_x * p.dx
# Modified spatial derivative: p.dx + phi_x
```

### Free Surface
```python
from devito import Eq

# Mirror antisymmetric boundary at z=0
# p(z<0) = -p(z>0)
z = grid.dimensions[-1]
free_surface = Eq(p[t+1, x, 0], -p[t+1, x, 1])
```

## Advanced Operators

### Save Full Wavefield
```python
# Save all timesteps (memory intensive)
p_save = TimeFunction(name='p', grid=grid, time_order=2, space_order=so, save=nt)

# After running
snapshot = p_save.data[100]  # Wavefield at timestep 100
```

### Subsampled Wavefield
```python
from devito import ConditionalDimension, Function

# Save every nth timestep
factor = 10
time_sub = ConditionalDimension('t_sub', parent=time, factor=factor)
p_sub = Function(name='p_sub', grid=grid, shape=(nt//factor,) + grid.shape,
                 dimensions=(time_sub,) + grid.dimensions)

save_eq = Eq(p_sub, p)  # Only executes every `factor` timesteps
```

### Gradient Computation (Adjoint)
```python
# Forward wavefield (saved)
u = TimeFunction(name='u', grid=grid, save=nt, time_order=2, space_order=so)

# Adjoint wavefield
v = TimeFunction(name='v', grid=grid, time_order=2, space_order=so)

# Gradient accumulator
grad = Function(name='grad', grid=grid)

# Imaging condition: correlate forward and adjoint wavefields
grad_eq = Inc(grad, u * v.dt2)
```

### Custom Finite Differences
```python
from devito import Derivative

# Explicit derivative specification
dp_dx = Derivative(p, x, deriv_order=1, fd_order=8)
dp_dz = Derivative(p, z, deriv_order=1, fd_order=8)

# Staggered grids
dp_dx_staggered = p.dx(x0=x + x.spacing/2)  # Half-grid shift
```

## Source and Receiver Operations

### Point Source Injection
```python
from examples.seismic import RickerSource

src = RickerSource(name='src', grid=grid, f0=f0, npoint=1, time_range=time_range)
src.coordinates.data[0, :] = [src_x, src_z]

# Inject into wavefield
src_term = src.inject(field=p.forward, expr=src * dt**2 * v**2)
```

### Multiple Sources
```python
nsrc = 10
src = RickerSource(name='src', grid=grid, f0=f0, npoint=nsrc, time_range=time_range)

# Set coordinates for each source
for i in range(nsrc):
    src.coordinates.data[i, :] = [x_positions[i], z_positions[i]]
```

### Receiver Interpolation
```python
from examples.seismic import Receiver

rec = Receiver(name='rec', grid=grid, npoint=nrec, time_range=time_range)

# Interpolate wavefield at receiver locations
rec_term = rec.interpolate(expr=p)

# Access recorded data after simulation
shot_gather = rec.data  # Shape: (nt, nrec)
```

### Custom Sparse Functions
```python
from devito import SparseTimeFunction

# General sparse function
sparse = SparseTimeFunction(name='sparse', grid=grid, npoint=n, nt=nt)
sparse.coordinates.data[:] = coordinates_array

# Interpolation (wavefield to points)
interp = sparse.interpolate(expr=p)

# Injection (points to wavefield)
inject = sparse.inject(field=p.forward, expr=sparse)
```
