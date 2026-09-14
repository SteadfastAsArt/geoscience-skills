# Wavelets and phase

Use this reference for choosing a wavelet shape or changing its phase. The
examples are independent and use seconds and Hz. In Bruges 0.5.4, named-tuple
fields are `amplitude` and `time`, in that order. The sampled duration may
include both endpoints; use the returned time axis instead of reconstructing
its length by truncating `duration / dt`.

## Ricker

```python
from bruges.filters import ricker

ricker_wavelet = ricker(duration=0.128, dt=0.001, f=25.0)
amplitude = ricker_wavelet.amplitude
time_s = ricker_wavelet.time
```

Ricker is symmetric with its maximum at zero time. Its frequency parameter
specifies the spectral peak; any quoted bandwidth needs an explicit amplitude
threshold. Choose frequency from observed data, rather than a fixed
frequency-versus-depth formula.

## Ormsby

```python
from bruges.filters import ormsby

ormsby_wavelet = ormsby(duration=0.256, dt=0.001, f=[5.0, 10.0, 50.0, 60.0])
amplitude = ormsby_wavelet.amplitude
time_s = ormsby_wavelet.time
```

The four frequencies are the low cut, end of rising ramp, start of falling
ramp, and high cut. Require `0 < f1 < f2 < f3 < f4 < 1/(2*dt)`; duration controls
truncation and frequency resolution. Corners describe a target trapezoidal
spectrum, not exact finite-record spectral bins.

## Klauder

```python
from bruges.filters import klauder

klauder_wavelet = klauder(duration=0.256, dt=0.001, f=[10.0, 80.0],
                          autocorrelate=True, taper='blackman')
amplitude = klauder_wavelet.amplitude
time_s = klauder_wavelet.time
```

The default autocorrelation gives a pulse representing a correlated sweep;
`autocorrelate=False` produces the sweep. `taper` accepts a supported window
name or callable, not an integer taper length. Actual Vibroseis signatures
also depend on the emitted sweep and processing; this pulse is an illustration.

## Synthetic alignment

Use the complete regularly sampled time-domain synthetic in
[the skill entrypoint](../SKILL.md#wavelet-and-time-domain-synthetic). Keep the
reflectivity on the same time grid as the output trace and declare whether an
interface is indexed at the upper or lower sample. Test a single impulse:
convolution should reproduce the shifted, reflectivity-scaled wavelet.
Do not convolve an unresampled depth-indexed log with a time wavelet.

## Phase rotation

```python
import numpy as np
from scipy.signal import hilbert

def phase_rotate(amplitude, angle_deg):
    """Rotate using positive-angle exp(+i*angle) on the analytic signal."""
    analytic = hilbert(np.asarray(amplitude, dtype=float))
    return np.real(analytic * np.exp(1j * np.deg2rad(angle_deg)))
```

This convention gives `-imag(hilbert(amplitude))` at +90 degrees. Some seismic
software uses the opposite sign; state the convention when comparing traces.
Finite-record Hilbert transforms introduce edge effects, so pad or taper
appropriately for the intended use.

Quarter-wavelength tuning `vp / (4*f)` is an approximate interference scale,
not a universal resolvability limit. Account for bandwidth, phase, sampling
and noise before interpreting thin-bed thickness.

## Sources

Checked **2026-09-14** against the [official wavelet API](https://code.agilescientific.com/bruges/api/bruges.filters.html)
and [Bruges 0.5.4 source](https://github.com/agilescientific/bruges/blob/v0.5.4/bruges/filters/wavelets.py).
