# PyLops Operators Reference

## Table of Contents
- [Basic Operators](#basic-operators)
- [Derivative Operators](#derivative-operators)
- [Signal Processing](#signal-processing)
- [Transform Operators](#transform-operators)
- [Restriction and Sampling](#restriction-and-sampling)
- [Combination Operators](#combination-operators)
- [Geophysics Operators](#geophysics-operators)

## Basic Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `Identity(N)` | Identity matrix | `I = pylops.Identity(100)` |
| `Diagonal(d)` | Diagonal matrix from vector | `D = pylops.Diagonal(np.array([1,2,3]))` |
| `MatrixMult(A)` | Explicit matrix multiplication | `M = pylops.MatrixMult(np.random.randn(50,100))` |
| `Zero(N, M)` | Zero operator | `Z = pylops.Zero(50, 100)` |
| `Transpose(dims, axes)` | Transpose array dimensions | `T = pylops.Transpose((10,20), axes=(1,0))` |
| `Flip(dims, axis)` | Flip array along axis | `F = pylops.Flip((10,20), axis=0)` |
| `Roll(dims, shift)` | Circular shift | `R = pylops.Roll((100,), shift=10)` |
| `Pad(dims, pad)` | Zero-pad array | `P = pylops.Pad((10,10), pad=((2,2),(3,3)))` |

## Derivative Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `FirstDerivative(N)` | First derivative (central diff) | `D1 = pylops.FirstDerivative(100)` |
| `SecondDerivative(N)` | Second derivative | `D2 = pylops.SecondDerivative(100)` |
| `Gradient(dims)` | Gradient operator (all directions) | `G = pylops.Gradient((64,64))` |
| `Laplacian(dims)` | Laplacian operator | `L = pylops.Laplacian((64,64))` |

### Derivative Options

```python
# Specify direction for multi-dimensional
D1 = pylops.FirstDerivative(dims=(64, 64), axis=0)  # Along axis 0
D1 = pylops.FirstDerivative(dims=(64, 64), axis=1)  # Along axis 1

# Specify sampling interval
D1 = pylops.FirstDerivative(100, sampling=0.1)

# Edge handling: 'zeros' (default), 'periodic', 'reflect'
D1 = pylops.FirstDerivative(100, edge=True)  # Handle edges
```

## Signal Processing

| Operator | Module | Description |
|----------|--------|-------------|
| `Convolve1D` | `signalprocessing` | 1D convolution |
| `Convolve2D` | `signalprocessing` | 2D convolution |
| `ConvolveND` | `signalprocessing` | N-dimensional convolution |
| `FFT` | `signalprocessing` | 1D Fast Fourier Transform |
| `FFT2D` | `signalprocessing` | 2D Fast Fourier Transform |
| `FFTND` | `signalprocessing` | N-dimensional FFT |
| `Shift` | `signalprocessing` | Fractional shift in Fourier domain |
| `Interp` | `signalprocessing` | Sinc interpolation |
| `Bilinear` | `signalprocessing` | Bilinear interpolation |

### Convolution Examples

```python
import pylops.signalprocessing as sp

# 1D convolution
wavelet = np.sin(np.linspace(0, 2*np.pi, 21)) * np.hanning(21)
C1 = sp.Convolve1D(n=200, h=wavelet, offset=10)

# 2D convolution
kernel = np.outer(wavelet, wavelet)
C2 = sp.Convolve2D(dims=(100, 100), h=kernel)

# FFT
F1 = sp.FFT(n=128)          # 1D
F2 = sp.FFT2D(dims=(64, 64)) # 2D
```

## Transform Operators

| Operator | Module | Description |
|----------|--------|-------------|
| `DWT` | `signalprocessing` | Discrete Wavelet Transform |
| `DWT2D` | `signalprocessing` | 2D Discrete Wavelet Transform |
| `DCT` | `signalprocessing` | Discrete Cosine Transform |
| `Radon2D` | `signalprocessing` | 2D Radon transform |
| `Radon3D` | `signalprocessing` | 3D Radon transform |
| `ChirpRadon2D` | `signalprocessing` | Chirp Radon transform |
| `Seislet` | `signalprocessing` | Seislet transform |

### Transform Examples

```python
import pylops.signalprocessing as sp

# Wavelet transform
W = sp.DWT(dims=128, wavelet='db4', level=3)

# Radon transform for multiple offsets
R = sp.Radon2D(
    taxis=np.arange(0, 1, 0.004),  # Time axis
    haxis=np.arange(-1000, 1001, 100),  # Offset axis
    paxis=np.linspace(-1e-3, 1e-3, 100),  # Slowness axis
    kind='linear'  # 'linear', 'parabolic', or 'hyperbolic'
)
```

## Restriction and Sampling

| Operator | Description | Example |
|----------|-------------|---------|
| `Restriction(N, iava)` | Sample at indices | `R = pylops.Restriction(100, [0,10,50])` |
| `Spread(dims, table)` | Spreading/stacking | See docs |
| `Symmetrize(N)` | Symmetrize signal | `S = pylops.Symmetrize(100)` |

### Restriction Example

```python
# Random subsampling
n = 1000
indices = np.random.choice(n, size=100, replace=False)
R = pylops.Restriction(n, indices)

# Forward: subsample
y = R @ x  # Shape: (100,)

# Adjoint: insert zeros
x_adj = R.H @ y  # Shape: (1000,) with zeros
```

## Combination Operators

| Operator | Description | Result Shape |
|----------|-------------|--------------|
| `VStack([A,B])` | Vertical stack | (M_A + M_B, N) |
| `HStack([A,B])` | Horizontal stack | (M, N_A + N_B) |
| `BlockDiag([A,B])` | Block diagonal | (M_A + M_B, N_A + N_B) |
| `Block([[A,B],[C,D]])` | Block matrix | Sum of row dims, sum of col dims |

### Combination Examples

```python
A = pylops.Identity(50)
B = pylops.FirstDerivative(50)

# Vertical stack: [A; B]
V = pylops.VStack([A, B])  # Shape: (100, 50)

# Horizontal stack: [A, B]
H = pylops.HStack([A, B])  # Shape: (50, 100)

# Block diagonal
BD = pylops.BlockDiag([A, B])  # Shape: (100, 100)

# Block matrix
Block = pylops.Block([
    [A, B],
    [B, A]
])  # Shape: (100, 100)
```

## Geophysics Operators

| Operator | Module | Description |
|----------|--------|-------------|
| `Kirchhoff` | `waveeqprocessing` | Kirchhoff migration/demigration |
| `MDC` | `waveeqprocessing` | Multi-dimensional convolution |
| `PrestackLinearModelling` | `avo` | Prestack AVO modelling |
| `Spread` | - | Spreading for NMO correction |

### AVO Modelling Example

```python
from pylops.avo import PrestackLinearModelling

# Angles
theta = np.arange(0, 30, 5)

# AVO modelling
A = PrestackLinearModelling(
    wav=wavelet,
    theta=theta,
    vsvp=0.5,
    nt0=100,
    linearization='akirich'  # or 'fatti', 'PS'
)

# Forward: reflectivity to seismic
# Input: [m, m_scaled, ...] stacked
seismic = A @ reflectivity_model
```

## Creating Custom Operators

```python
import pylops

class MyOperator(pylops.LinearOperator):
    def __init__(self, n, dtype='float64'):
        self.n = n
        super().__init__(shape=(n, n), dtype=dtype)

    def _matvec(self, x):
        """Forward operation: y = A @ x"""
        return x * 2  # Example: scale by 2

    def _rmatvec(self, y):
        """Adjoint operation: x = A.H @ y"""
        return y * 2  # Self-adjoint in this case

# Verify with dot test
op = MyOperator(100)
pylops.utils.dottest(op, 100, 100, verb=True)
```

## Operator Attributes

All operators have these attributes:
- `.shape` - Tuple (M, N)
- `.dtype` - Data type
- `.explicit` - Whether matrix is stored explicitly
- `.H` - Adjoint operator

Common methods:
- `op @ x` or `op.matvec(x)` - Forward operation
- `op.H @ y` or `op.rmatvec(y)` - Adjoint operation
- `op / y` - Least squares solve
- `op.todense()` - Convert to dense matrix (caution: memory!)
