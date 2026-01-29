# Devito Performance Optimization

## Table of Contents
- [Backend Configuration](#backend-configuration)
- [GPU Execution](#gpu-execution)
- [Memory Optimization](#memory-optimization)
- [Operator Tuning](#operator-tuning)
- [Profiling](#profiling)
- [Best Practices](#best-practices)

## Backend Configuration

### Environment Variables
```bash
# CPU threading
export OMP_NUM_THREADS=16
export OMP_PROC_BIND=close
export OMP_PLACES=cores

# Devito settings
export DEVITO_LOGGING=DEBUG      # Logging level
export DEVITO_ARCH=gcc           # Compiler (gcc, icc, pgcc)
export DEVITO_LANGUAGE=openmp    # Parallelization
```

### Python Configuration
```python
from devito import configuration

# View current settings
print(configuration)

# Set options
configuration['log-level'] = 'DEBUG'
configuration['openmp'] = True
configuration['mpi'] = False
```

## GPU Execution

### NVIDIA GPUs
```bash
# Environment setup
export DEVITO_PLATFORM=nvidiaX
export DEVITO_LANGUAGE=openacc
export DEVITO_ARCH=nvc

# Or for CUDA
export DEVITO_LANGUAGE=cuda
```

```python
from devito import configuration

configuration['platform'] = 'nvidiaX'
configuration['language'] = 'openacc'
configuration['compiler'] = 'nvc'

# Create operator (generates GPU code)
op = Operator([stencil])
op.apply(time_M=nt-1)
```

### AMD GPUs
```bash
export DEVITO_PLATFORM=amdgpuX
export DEVITO_LANGUAGE=hip
export DEVITO_ARCH=hipcc
```

### GPU Memory Management
```python
# Data already on GPU - avoid transfers
# Use Devito's data management

# For explicit control
from devito import switchconfig

with switchconfig(platform='nvidiaX'):
    # Operations run on GPU within this context
    op.apply(time_M=nt-1)
```

## Memory Optimization

### Reduce Time Levels
```python
# Default: 3 time levels for time_order=2
p = TimeFunction(name='p', grid=grid, time_order=2, space_order=4)
# Memory: 3 * nx * nz * 8 bytes

# Save full wavefield (expensive!)
p_save = TimeFunction(name='p', grid=grid, time_order=2, space_order=4, save=nt)
# Memory: nt * nx * nz * 8 bytes
```

### Checkpointing for Adjoint
```python
from devito import TimeFunction
from devito.checkpointing import DevitoCheckpoint, CheckpointOperator

# Without checkpointing: O(nt * grid_size) memory
# With checkpointing: O(sqrt(nt) * grid_size) memory

# Setup checkpointing
cp = DevitoCheckpoint([u])
wrap_fw = CheckpointOperator(op_forward, u=u, v=v, src=src, rec=rec)

# Run with checkpointing
from pyrevolve import Revolver
wrp = Revolver(cp, wrap_fw, wrap_rev, n_checkpoints, nt)
wrp.apply_forward()
wrp.apply_reverse()
```

### Memory Layout
```python
# Control data layout
from devito import TimeFunction

# Row-major (C-style, default)
p = TimeFunction(name='p', grid=grid, time_order=2, space_order=4)

# Explicit padding for alignment
p = TimeFunction(name='p', grid=grid, time_order=2, space_order=4,
                 padding=(0, 16, 16))  # Pad z and x by 16
```

## Operator Tuning

### Space Order Selection
```python
# Trade-off: accuracy vs. performance
# Lower order = faster but less accurate

# space_order=2: Fast, good for testing
# space_order=4: Good balance (recommended)
# space_order=8: High accuracy, slower
# space_order=16: Very accurate, expensive

p = TimeFunction(name='p', grid=grid, time_order=2, space_order=4)
```

### Operator Options
```python
from devito import Operator

# Basic operator
op = Operator([stencil])

# With aggressive optimization
op = Operator([stencil], opt='aggressive')

# Specific optimization options
op = Operator([stencil], opt=('advanced', {'blocklevels': 2}))

# Available opt levels: 'noop', 'advanced', 'aggressive'
```

### Loop Blocking
```python
# Control cache blocking
op = Operator([stencil], opt=('blocking', {'blockinner': True}))

# Custom block sizes
op = Operator([stencil], opt=('blocking', {'blocklevels': 2}))

# At runtime
op.apply(time_M=nt, x0_blk0_size=32, x1_blk0_size=32)
```

### SIMD Vectorization
```python
# Enable SIMD (default with OpenMP)
configuration['language'] = 'openmp'

# Compiler-specific flags are auto-generated
# Check generated code
print(op.ccode)
```

## Profiling

### Built-in Profiling
```python
from devito import Operator

op = Operator([stencil])

# Run with profiling
summary = op.apply(time_M=nt-1)

# Print performance summary
print(summary)
# Shows: time, GFlops/s, GPts/s, memory bandwidth
```

### Detailed Timing
```python
from devito import configuration

configuration['profiling'] = 'advanced'

op = Operator([stencil])
summary = op.apply(time_M=nt-1)

# Access detailed metrics
print(f"Total time: {summary.globals['fdlike'].time:.3f}s")
print(f"GFlops/s: {summary.globals['fdlike'].gflopss:.2f}")
print(f"GPts/s: {summary.globals['fdlike'].gpointss:.2f}")
```

### Memory Bandwidth Analysis
```python
# Estimate theoretical bandwidth
import numpy as np

nx, nz = grid.shape
nt = 1000
bytes_per_cell = 8  # float64

# Reads and writes per timestep
reads = 2 * nx * nz * bytes_per_cell    # p[t] and p[t-1]
writes = 1 * nx * nz * bytes_per_cell   # p[t+1]
total_bytes = (reads + writes) * nt

# Compare with achieved bandwidth from profiling
achieved_bandwidth = total_bytes / summary.globals['fdlike'].time / 1e9
print(f"Achieved bandwidth: {achieved_bandwidth:.2f} GB/s")
```

## Best Practices

### Grid Size Selection
```python
# Prefer powers of 2 or multiples of cache line
# Good: 256, 512, 1024
# Okay: 100, 200, 500 (Devito handles padding)

# For GPUs: multiples of warp size (32 for NVIDIA)
grid = Grid(shape=(1024, 512), extent=(10000., 5000.))
```

### Minimize Operators
```python
# BAD: Multiple separate operators
op1 = Operator([eq1])
op2 = Operator([eq2])
for t in range(nt):
    op1.apply()
    op2.apply()

# GOOD: Single fused operator
op = Operator([eq1, eq2])
op.apply(time_M=nt-1)
```

### Avoid Python Loops
```python
# BAD: Python time loop
for t in range(nt):
    op.apply(time_m=t, time_M=t)

# GOOD: Let Devito handle time loop
op.apply(time_M=nt-1)
```

### Reuse Operators
```python
# Create operator once
op = Operator([stencil] + src_term + rec_term)

# Reuse for multiple shots
for shot_id in range(nshots):
    # Update source location
    src.coordinates.data[0, :] = shot_positions[shot_id]

    # Clear wavefield
    p.data[:] = 0.

    # Run same operator
    op.apply(time_M=nt-1, dt=dt)

    # Store results
    shot_records[shot_id] = rec.data.copy()
```

### Efficient I/O
```python
import numpy as np

# Save wavefield snapshots efficiently
# Don't save every timestep during simulation

# Option 1: Save subsampled in time
save_every = 10
p_save = TimeFunction(name='p', grid=grid, save=nt//save_every, ...)

# Option 2: Save specific snapshots post-hoc
snapshots = [100, 200, 500, 1000]
for t in snapshots:
    np.save(f'wavefield_{t}.npy', p.data[0])
    op.apply(time_m=t, time_M=t+100, dt=dt)
```

### MPI Parallelization
```python
# Enable MPI domain decomposition
configuration['mpi'] = True

# Run with MPI
# mpirun -n 4 python script.py

# Devito auto-distributes grid across processes
from devito import Grid

grid = Grid(shape=(1000, 1000), extent=(10000., 10000.))
# Each MPI rank gets a subdomain
```

## Performance Comparison Table

| Configuration | Relative Speed | Use Case |
|--------------|----------------|----------|
| Pure Python (no Devito) | 1x | Don't do this |
| Devito CPU (1 thread) | 100x | Development |
| Devito CPU (OpenMP) | 500x | Production CPU |
| Devito GPU (OpenACC) | 2000x | Production GPU |
| Devito GPU (CUDA) | 2500x | Maximum GPU perf |

Actual speedups depend on problem size, hardware, and space order.
