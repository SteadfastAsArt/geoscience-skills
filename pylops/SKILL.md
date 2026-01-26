---
name: pylops
description: Linear operators for large-scale inverse problems. Matrix-free representations for efficient forward/adjoint operations in signal processing and geophysics.
---

# PyLops - Linear Operators Library

Help users define and solve linear inverse problems using matrix-free operators.

## Installation

```bash
pip install pylops
```

## Core Concepts

### Why Linear Operators?
Instead of storing huge matrices explicitly, represent them as functions:
- `y = A @ x` (forward)
- `x = A.H @ y` (adjoint/transpose)

### Key Features
- Matrix-free (memory efficient)
- Backend-agnostic (NumPy, CuPy, PyTorch)
- Composable (chain, stack, sum operators)
- Built-in solvers for inverse problems

## Common Workflows

### 1. Basic Operator Usage
```python
import numpy as np
import pylops

# Create diagonal operator
d = np.array([1., 2., 3., 4., 5.])
D = pylops.Diagonal(d)

# Forward: y = D @ x
x = np.ones(5)
y = D @ x  # or D.matvec(x)

# Adjoint: x = D.H @ y
x_adj = D.H @ y  # or D.rmatvec(y)

# Shape
print(f"Shape: {D.shape}")  # (5, 5)
```

### 2. First Derivative Operator
```python
import numpy as np
import pylops

n = 100
x = np.sin(np.linspace(0, 4*np.pi, n))

# First derivative
D1 = pylops.FirstDerivative(n, dtype='float64')

# Compute derivative
dx = D1 @ x

# Plot
import matplotlib.pyplot as plt
plt.plot(x, label='x')
plt.plot(dx, label='dx/dt')
plt.legend()
```

### 3. Convolution Operator
```python
import numpy as np
import pylops

# Signal
n = 200
x = np.zeros(n)
x[50] = 1.  # Impulse
x[100] = 1.
x[150] = -1.

# Wavelet
wavelet = np.sin(np.linspace(0, 2*np.pi, 21)) * np.hanning(21)

# Convolution operator
C = pylops.signalprocessing.Convolve1D(n, h=wavelet, offset=10)

# Forward (convolve)
y = C @ x

# Adjoint (correlation)
x_adj = C.H @ y
```

### 4. FFT Operator
```python
import numpy as np
import pylops

n = 128
x = np.random.randn(n)

# FFT operator
F = pylops.signalprocessing.FFT(n)

# Forward transform
X = F @ x

# Inverse transform
x_rec = F.H @ X / n
```

### 5. 2D Gradient
```python
import numpy as np
import pylops

ny, nx = 64, 64
image = np.random.randn(ny, nx)

# Gradient operator
G = pylops.Gradient(dims=(ny, nx), dtype='float64')

# Compute gradient (flattened output: [dy, dx])
grad = G @ image.ravel()

# Reshape
dy = grad[:ny*nx].reshape(ny, nx)
dx = grad[ny*nx:].reshape(ny, nx)
```

### 6. Compose Operators
```python
import pylops
import numpy as np

n = 100

# Chain operators: y = (C @ B @ A) @ x
A = pylops.Identity(n)
B = pylops.FirstDerivative(n)
C = pylops.Smoothing1D(5, n)

# Method 1: Matrix multiplication
composed = C @ B @ A

# Method 2: Explicit chaining
composed = pylops.LinearOperator(C) * pylops.LinearOperator(B) * pylops.LinearOperator(A)

# Apply
x = np.random.randn(n)
y = composed @ x
```

### 7. Stack and Block Operators
```python
import pylops
import numpy as np

n = 50

# Vertical stacking
A = pylops.Identity(n)
B = pylops.FirstDerivative(n)
V = pylops.VStack([A, B])  # Shape: (2n, n)

# Horizontal stacking
H = pylops.HStack([A, B])  # Shape: (n, 2n)

# Block diagonal
BD = pylops.BlockDiag([A, B])  # Shape: (2n, 2n)

# Block matrix
Block = pylops.Block([
    [A, B],
    [B, A]
])  # Shape: (2n, 2n)
```

### 8. Solve Inverse Problem (Least Squares)
```python
import numpy as np
import pylops

# Forward problem: y = A @ x + noise
n = 100
A = pylops.FirstDerivative(n)
x_true = np.cumsum(np.random.randn(n))  # Random walk
y = A @ x_true + 0.1 * np.random.randn(n)

# Solve: min ||Ax - y||²
x_est = pylops.optimization.leastsquares.NormalEquationsInversion(
    A, None, y
)

# Or use division operator (auto least squares)
x_est = A / y
```

### 9. Regularized Inversion
```python
import numpy as np
import pylops

# Forward operator
A = pylops.signalprocessing.Convolve1D(100, h=wavelet)
y = A @ x_true + noise

# Regularization: smoothness
Reg = pylops.SecondDerivative(100)

# Solve: min ||Ax - y||² + λ||Rx||²
x_est = pylops.optimization.leastsquares.RegularizedInversion(
    A, [Reg], y,
    epsRs=[0.1]  # Regularization weight
)
```

### 10. Iterative Solvers
```python
import numpy as np
import pylops

# Large sparse problem
n = 10000
A = pylops.FirstDerivative(n)
y = A @ np.random.randn(n)

# LSQR (iterative least squares)
x_lsqr = pylops.optimization.solver.lsqr(A, y, iter_lim=100)[0]

# CGLS (conjugate gradient)
x_cgls = pylops.optimization.solver.cgls(A, y, niter=100)[0]

# With callback for monitoring
def callback(x):
    print(f"Residual: {np.linalg.norm(A @ x - y):.6f}")

x_lsqr = pylops.optimization.solver.lsqr(A, y, iter_lim=100, callback=callback)[0]
```

### 11. Sparsity-Promoting Inversion
```python
import numpy as np
import pylops

# Sparse signal recovery
n = 100
k = 10  # Sparse in derivative domain

# True sparse signal
x_true = np.zeros(n)
x_true[np.random.choice(n, k, replace=False)] = np.random.randn(k)

# Measurement
A = pylops.MatrixMult(np.random.randn(50, n))
y = A @ x_true

# L1 inversion (ISTA/FISTA)
x_l1 = pylops.optimization.sparsity.ista(
    A, y, niter=100, eps=0.1
)[0]
```

### 12. GPU Acceleration
```python
import cupy as cp
import pylops

# Move to GPU
x_gpu = cp.asarray(x)

# Create GPU operator
A = pylops.FirstDerivative(n, dtype='float64')

# Compute on GPU
y_gpu = A @ x_gpu

# Back to CPU
y_cpu = cp.asnumpy(y_gpu)
```

## Key Operators

| Category | Operators |
|----------|-----------|
| Basic | `Identity`, `Diagonal`, `MatrixMult`, `Zero` |
| Derivatives | `FirstDerivative`, `SecondDerivative`, `Gradient`, `Laplacian` |
| Signal | `Convolve1D`, `Convolve2D`, `FFT`, `FFT2D` |
| Transform | `DWT`, `Radon2D`, `Radon3D` |
| Restriction | `Restriction`, `Spread` |
| Combination | `VStack`, `HStack`, `BlockDiag`, `Block` |

## Solvers

| Solver | Use Case |
|--------|----------|
| `NormalEquationsInversion` | Small dense problems |
| `RegularizedInversion` | With regularization |
| `lsqr` | Large sparse, well-conditioned |
| `cgls` | Large sparse, symmetric |
| `ista/fista` | Sparsity-promoting |
| `splitbregman` | TV regularization |

## Tips

1. **Never form full matrix** - Use `.matvec()` and `.rmatvec()`
2. **Check shapes** - Operators have `.shape` attribute
3. **Verify adjoint** - Use `pylops.utils.dottest()`
4. **Start simple** - Test on small problems first
5. **Use GPU** - For large 3D problems

## Dot Test (Verify Adjoint)
```python
import pylops

A = pylops.FirstDerivative(100)
pylops.utils.dottest(A, 100, 100, verb=True)
# Should print: Dot test passed!
```

## Resources

- Documentation: https://pylops.readthedocs.io/
- GitHub: https://github.com/PyLops/pylops
- Tutorials: https://pylops.readthedocs.io/en/stable/tutorials/
- Gallery: https://pylops.readthedocs.io/en/stable/gallery/
