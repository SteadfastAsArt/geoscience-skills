# PyLops Solvers Reference

## Table of Contents
- [Overview](#overview)
- [Direct Solvers](#direct-solvers)
- [Iterative Solvers](#iterative-solvers)
- [Sparsity-Promoting Solvers](#sparsity-promoting-solvers)
- [Regularized Inversion](#regularized-inversion)
- [Solver Selection Guide](#solver-selection-guide)
- [Advanced Options](#advanced-options)

## Overview

PyLops provides solvers for the inverse problem: given `y = Ax + n`, find `x`.

```python
import pylops
from pylops.optimization import leastsquares, solver, sparsity
```

## Direct Solvers

### Normal Equations Inversion

Best for small, well-conditioned problems.

```python
# Basic usage: solve (A^H A) x = A^H y
x = leastsquares.NormalEquationsInversion(A, None, y)

# With regularization
x = leastsquares.NormalEquationsInversion(
    A,
    Regs=[pylops.SecondDerivative(n)],  # Regularization operators
    y=y,
    epsNRs=[0.1],  # Regularization weights
    returninfo=False
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `Op` | LinearOperator | Forward operator |
| `Regs` | list or None | Regularization operators |
| `data` | ndarray | Observed data y |
| `epsNRs` | list | Regularization weights |
| `Weight` | LinearOperator | Data weighting |
| `NRegs` | list | Normal equations regularizers |
| `returninfo` | bool | Return solver info |

### Regularized Inversion

General regularized least squares solver.

```python
# Solve: min ||Ax - y||^2 + sum(eps_i * ||R_i x||^2)
x = leastsquares.RegularizedInversion(
    Op=A,
    Regs=[pylops.SecondDerivative(n)],
    data=y,
    epsRs=[0.1],
    **kwargs_solver
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `Op` | LinearOperator | Forward operator |
| `Regs` | list | Regularization operators |
| `data` | ndarray | Observed data |
| `epsRs` | list | Regularization weights |
| `x0` | ndarray | Initial guess |
| `**kwargs_solver` | dict | Passed to underlying solver |

## Iterative Solvers

Located in `pylops.optimization.solver`.

### LSQR

Iterative least squares for large, sparse problems.

```python
x, istop, itn, r1norm, r2norm, anorm, acond, arnorm, xnorm, var = \
    solver.lsqr(A, y, damp=0.0, iter_lim=100, show=False)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `A` | LinearOperator | Forward operator |
| `b` | ndarray | Right-hand side |
| `damp` | float | Damping factor (Tikhonov) |
| `iter_lim` | int | Maximum iterations |
| `atol`, `btol` | float | Convergence tolerances |
| `show` | bool | Print progress |

Returns tuple: `(x, istop, itn, r1norm, r2norm, anorm, acond, arnorm, xnorm, var)`

### CGLS

Conjugate gradient for least squares.

```python
x, niter, cost = solver.cgls(A, y, x0=None, niter=100, tol=1e-6, show=False)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `A` | LinearOperator | Forward operator |
| `b` | ndarray | Right-hand side |
| `x0` | ndarray | Initial guess |
| `niter` | int | Maximum iterations |
| `tol` | float | Convergence tolerance |
| `show` | bool | Print progress |

Returns: `(x, niter, cost_history)`

### CG (Conjugate Gradient)

For symmetric positive definite systems.

```python
x, niter = solver.cg(A, y, x0=None, niter=100, tol=1e-6, show=False)
```

## Sparsity-Promoting Solvers

Located in `pylops.optimization.sparsity`.

### ISTA (Iterative Shrinkage-Thresholding)

L1 minimization: `min ||Ax - y||^2 + eps * ||x||_1`

```python
x, niter, cost = sparsity.ista(
    A, y,
    niter=100,
    eps=0.1,        # L1 regularization weight
    tol=1e-6,
    returninfo=True,
    show=False
)
```

### FISTA (Fast ISTA)

Accelerated version of ISTA with momentum.

```python
x, niter, cost = sparsity.fista(
    A, y,
    niter=100,
    eps=0.1,
    tol=1e-6,
    returninfo=True,
    show=False
)
```

### ISTA/FISTA Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `Op` | LinearOperator | Forward operator |
| `data` | ndarray | Observed data |
| `niter` | int | Maximum iterations |
| `eps` | float | L1 regularization weight |
| `tol` | float | Convergence tolerance |
| `alpha` | float | Step size (auto-computed if None) |
| `eigsiter` | int | Iterations for eigenvalue estimation |
| `threshkind` | str | 'soft' or 'hard' thresholding |
| `show` | bool | Print progress |

### OMP (Orthogonal Matching Pursuit)

Greedy sparse recovery.

```python
x, niter = sparsity.omp(
    A, y,
    niter_outer=10,  # Max non-zero coefficients
    niter_inner=100,
    sigma=1e-4,      # Noise level
    show=False
)
```

### Split Bregman

For total variation regularization.

```python
x, niter = sparsity.splitbregman(
    Op=A,                    # Forward operator
    RegsL1=[G],              # L1-regularized operators (e.g., gradient)
    data=y,
    niter_inner=5,
    niter_outer=10,
    mu=1.0,                  # Data fidelity weight
    epsRL1s=[0.1],           # L1 regularization weights
    tol=1e-6,
    show=False
)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `Op` | LinearOperator | Forward operator (e.g., Identity for denoising) |
| `RegsL1` | list | Operators for L1 penalty (e.g., Gradient for TV) |
| `data` | ndarray | Observed data |
| `niter_inner` | int | Inner iterations |
| `niter_outer` | int | Outer (Bregman) iterations |
| `mu` | float | Data fidelity weight |
| `epsRL1s` | list | L1 regularization weights |

## Regularized Inversion

### Preconditioned CG

```python
x = leastsquares.PreconditionedInversion(
    Op=A,
    P=preconditioner,
    data=y,
    **kwargs_solver
)
```

### Bayesian Inversion

```python
x_map, C_post = leastsquares.BayesianInversion(
    Op=A,
    y=y,
    Cm=prior_covariance,
    Cd=noise_covariance
)
```

## Solver Selection Guide

| Problem Type | Recommended Solver | When to Use |
|--------------|-------------------|-------------|
| Small, dense | `NormalEquationsInversion` | N < 10,000, well-conditioned |
| Large, sparse | `lsqr` | N > 10,000, general case |
| Symmetric | `cgls` or `cg` | A^H A is symmetric |
| Sparse solution | `ista`/`fista` | Want L1 regularization |
| Very sparse | `omp` | Known sparsity level |
| TV denoising | `splitbregman` | Preserve edges in images |
| Ill-conditioned | `RegularizedInversion` | Need explicit regularization |

### Problem Size Guidelines

```python
n = A.shape[1]

if n < 5000:
    # Direct solve is fast enough
    x = leastsquares.NormalEquationsInversion(A, None, y)
elif n < 100000:
    # Iterative solver
    x = solver.lsqr(A, y, iter_lim=200)[0]
else:
    # Large-scale: use GPU + iterative
    import cupy as cp
    y_gpu = cp.asarray(y)
    x_gpu = solver.lsqr(A, y_gpu, iter_lim=500)[0]
```

## Advanced Options

### Monitoring Convergence

```python
# With callback
costs = []
def callback(x):
    costs.append(np.linalg.norm(A @ x - y))

x = solver.lsqr(A, y, iter_lim=100, callback=callback)[0]
```

### Warm Starting

```python
# Use previous solution as initial guess
x0 = previous_solution
x = solver.cgls(A, y, x0=x0, niter=50)[0]
```

### Custom Stopping Criteria

```python
# Stop when residual norm is small enough
x, istop, itn, r1norm, *_ = solver.lsqr(A, y, iter_lim=1000, atol=1e-8, btol=1e-8)
print(f"Stopped after {itn} iterations, reason: {istop}")
```

### LSQR Stop Conditions

| istop | Meaning |
|-------|---------|
| 0 | x = 0 is exact solution |
| 1 | Ax - b is small enough (atol) |
| 2 | A^T(Ax - b) is small enough (btol) |
| 3 | Condition number too large |
| 4 | Reached iter_lim |

### Regularization Parameter Selection

```python
# L-curve method (manual)
eps_values = np.logspace(-4, 1, 20)
residuals = []
reg_norms = []

for eps in eps_values:
    x = leastsquares.RegularizedInversion(
        A, [Reg], y, epsRs=[eps]
    )
    residuals.append(np.linalg.norm(A @ x - y))
    reg_norms.append(np.linalg.norm(Reg @ x))

# Plot L-curve
import matplotlib.pyplot as plt
plt.loglog(residuals, reg_norms, 'o-')
plt.xlabel('Residual norm')
plt.ylabel('Regularization norm')
```

### GPU Acceleration

```python
import cupy as cp

# Move data to GPU
y_gpu = cp.asarray(y)

# Solve on GPU
x_gpu = solver.lsqr(A, y_gpu, iter_lim=100)[0]

# Result stays on GPU; move back if needed
x_cpu = cp.asnumpy(x_gpu)
```
