---
name: seismic-interpretation
description: |
  End-to-end seismic interpretation workflow from SEG-Y loading through
  signal processing, rock physics, and visualization. Use when working
  with seismic data analysis pipelines.
license: MIT
metadata:
  skill_type: workflow
  version: 1.0.2
  author: Geoscience Skills
  tags: '["Seismic", "Interpretation", "SEG-Y", "Rock Physics", "Workflow", "AVO", "Processing"]'
  dependencies: '["segyio>=1.9", "obspy>=1.4", "bruges>=0.5.4", "disba>=0.7", "pyvista", "numpy", "scipy", "setuptools<81"]'
  complements: '["segyio", "obspy", "bruges", "disba", "pyvista"]'
  workflow_role: processing
---

# Seismic Interpretation Workflow

End-to-end pipeline for seismic data analysis, from loading SEG-Y files through
signal processing, rock physics modelling, and 3D visualization.

## Skill Chain

```text
segyio          obspy           bruges          disba           pyvista
[SEG-Y I/O] --> [Signal Proc] --> [Rock Physics] --> [Dispersion] --> [3D Viz]
  |               |                |                 |                |
  Load traces     Filter/FFT       AVO modelling     Surface waves    Volume render
  Read headers    Instrument resp   Fluid sub         Phase velocity   Slice display
  3D geometry     Spectral anal    Synthetics        Inversion        Horizon pick
```

## Decision Points

| Question | If Yes | If No |
|----------|--------|-------|
| Working with SEG-Y files? | Start with `segyio` | Use `obspy` for miniSEED/SAC |
| Need frequency filtering or spectral analysis? | Use `obspy` signal tools | Skip to rock physics |
| Performing AVO or fluid substitution? | Use `bruges` | Skip to visualization |
| Analysing surface waves (MASW/SASW)? | Use `disba` for dispersion | Skip `disba` |
| Need 3D volume rendering? | Use `pyvista` | Use matplotlib for 2D |

## Step-by-Step Orchestration

### Stage 1: Data Loading (segyio)

This loader handles a complete post-stack grid, including crossline-fast trace
ordering. Supply the survey's projected CRS from authoritative metadata. Header
coordinate units must be length units, and the binary measurement system must
identify metres or feet. Angular coordinates need reprojection first. Confirm
that the sample axis represents two-way time in milliseconds for this workflow.

```python
import segyio
import numpy as np

def load_poststack(path, crs):
    if not isinstance(crs, str) or not crs.strip():
        raise ValueError('Supply the projected survey CRS; SEG-Y coordinates alone do not identify it')
    with segyio.open(path, 'r', iline=189, xline=193) as f:
        if len(f.offsets) != 1:
            raise ValueError('Select or stack offsets before loading a post-stack cube')
        time_ms = np.asarray(f.samples, dtype=float).copy()
        if len(time_ms) < 2 or not np.all(np.isfinite(time_ms)):
            raise ValueError('Require at least two finite time samples')
        dt_ms = time_ms[1] - time_ms[0]
        if dt_ms <= 0 or not np.allclose(np.diff(time_ms), dt_ms):
            raise ValueError('Resample inconsistent time sampling before building a cube')
        to_metres = {1: 1.0, 2: 0.3048}.get(f.bin[segyio.BinField.MeasurementSystem])
        if to_metres is None:
            raise ValueError('Confirm SEG-Y measurement system: metres or feet')
        ilines, xlines = np.array(f.ilines), np.array(f.xlines)
        ii = {int(value): index for index, value in enumerate(ilines)}
        jj = {int(value): index for index, value in enumerate(xlines)}
        shape = (len(ilines), len(xlines))
        cube = np.empty((*shape, len(time_ms)), dtype=np.float32)
        easting, northing = np.empty(shape), np.empty(shape)
        seen = np.zeros(shape, dtype=bool)
        for trace_index, header in enumerate(f.header):
            i, j = ii[header[189]], jj[header[193]]
            if seen[i, j]:
                raise ValueError('Duplicate inline/crossline location')
            if header[segyio.TraceField.CoordinateUnits] != 1:
                raise ValueError('Require projected coordinates in length units')
            if (not np.isclose(header[segyio.TraceField.TRACE_SAMPLE_INTERVAL] / 1000, dt_ms)
                    or not np.isclose(header[segyio.TraceField.DelayRecordingTime], time_ms[0])):
                raise ValueError('Trace time axes differ; align them before stacking into a cube')
            scalar = header[segyio.TraceField.SourceGroupScalar]
            factor = scalar if scalar > 0 else 1 / abs(scalar) if scalar < 0 else 1.0
            easting[i, j] = header[segyio.TraceField.CDP_X] * factor * to_metres
            northing[i, j] = header[segyio.TraceField.CDP_Y] * factor * to_metres
            cube[i, j] = f.trace[trace_index]
            seen[i, j] = True
        if not np.all(seen):
            raise ValueError('Incomplete grid: retain missing traces explicitly or regrid')
    return dict(amplitude=cube, easting_m=easting, northing_m=northing,
                time_ms=time_ms, crs=crs, ilines=ilines, xlines=xlines)
```

### Stage 2: Signal Processing (obspy)

```python
from obspy import Trace

def filter_poststack(survey, freqmin=5, freqmax=80):
    dt_s = np.diff(survey['time_ms'])[0] / 1000.0
    if not 0 < freqmin < freqmax < 0.5 / dt_s:
        raise ValueError('Bandpass frequencies must be below the Nyquist frequency')
    result = dict(survey)
    result['amplitude'] = survey['amplitude'].astype(float, copy=True)
    if not np.all(np.isfinite(result['amplitude'])):
        raise ValueError('QC missing or nonfinite amplitudes before filtering')
    for trace in result['amplitude'].reshape(-1, result['amplitude'].shape[-1]):
        tr = Trace(data=trace.copy(), header={'delta': dt_s})
        tr.filter('bandpass', freqmin=freqmin, freqmax=freqmax, corners=4, zerophase=True)
        trace[:] = tr.data
    return result  # Pass this processed cube, with its geometry, to visualization.
```

### Stage 3: Rock Physics (bruges)

This optional branch needs well-derived inputs; it cannot infer elastic properties
from the loaded seismic cube. Supply aligned `vp`, `vs` (m/s), `rho` (kg/m3),
`porosity` (v/v), and `twt_s` (s) on a **uniform time grid**. Map depth logs through
a calibrated time-depth relation first; see `rock-physics-avo`. This illustrative
fluid replacement assumes an initially brine-saturated interval and a fixed frame.

```python
from bruges.reflection import zoeppritz_rpp
from bruges.filters import ricker
from bruges.rockphysics.fluidsub import avseth_fluidsub
from scipy.signal import convolve

vp, vs, rho, porosity, twt_s = [np.asarray(a, dtype=float)
                              for a in (vp, vs, rho, porosity, twt_s)]
if (any(a.ndim != 1 or a.shape != vp.shape for a in (vp, vs, rho, porosity, twt_s))
        or len(vp) < 2 or not np.all(np.isfinite([vp, vs, rho, porosity, twt_s]))
        or np.any(vp <= 0) or np.any(vs <= 0) or np.any(rho <= 0) or np.any(vp**2 <= 4/3 * vs**2)
        or np.any((porosity <= 0) | (porosity >= 1))):
    raise ValueError('Provide aligned, finite and physically valid elastic logs')
dt_s = twt_s[1] - twt_s[0]
if dt_s <= 0 or not np.allclose(np.diff(twt_s), dt_s):
    raise ValueError('Resample logs onto uniform two-way time before convolution')
if 25 >= 0.5 / dt_s:
    raise ValueError('Wavelet frequency must be below Nyquist')

theta_deg = np.arange(0, 40, 1)
Rpp = zoeppritz_rpp(vp[:-1], vs[:-1], rho[:-1], vp[1:], vs[1:], rho[1:], theta1=theta_deg)
vp_new, vs_new, rho_new = avseth_fluidsub(
    vp=vp, vs=vs, rho=rho, phi=porosity,
    rhof1=1050, rhof2=800, kmin=36.6e9, kf1=2.6e9, kf2=1.0e9,
)

impedance = vp * rho
rc = np.r_[0.0, np.diff(impedance) / (impedance[:-1] + impedance[1:])]
wavelet, wavelet_time = ricker(duration=0.128, dt=dt_s, f=25)
synthetic = convolve(rc, wavelet, mode='same')
```

### Stage 4: Surface Wave Analysis (disba, optional)

```python
from disba import PhaseDispersion

# Define velocity model (thickness, Vp, Vs, density)
velocity_model = PhaseDispersion(
    thickness=np.array([5, 10, 20, 0]) / 1000.0,  # km; last layer is half-space
    velocity_p=np.array([300, 600, 1200, 2500]) / 1000.0,  # km/s
    velocity_s=np.array([150, 300, 600, 1200]) / 1000.0,   # km/s
    density=np.array([1.8, 1.9, 2.1, 2.4]),       # g/cm3
)
period_s = np.linspace(0.01, 1.0, 50)
dispersion = velocity_model(period_s, wave='rayleigh', mode=0)
phase_velocity_m_s = dispersion.velocity * 1000.0
# Plot against dispersion.period: the returned curve contains computed periods.
```

### Stage 5: Visualization (pyvista)

```python
import pyvista as pv

def make_seismic_grid(survey):
    cube = survey['amplitude']
    x = np.broadcast_to(survey['easting_m'][..., None], cube.shape).copy()
    y = np.broadcast_to(survey['northing_m'][..., None], cube.shape).copy()
    z = np.broadcast_to(-survey['time_ms'][None, None, :], cube.shape).copy()
    # Explicit points preserve rotation, non-unit spacing and geographic origin.
    grid = pv.StructuredGrid(x, y, z)
    grid.point_data['amplitude'] = cube.ravel(order='F')
    grid.field_data['crs'] = np.array([survey['crs']])
    grid.field_data['axis_units'] = np.array(['m', 'm', 'ms (negative TWT)'])
    return grid
```

For the seismic processing branch, connect the functions as follows. Supply
`survey_crs` from the survey metadata, using the CRS of the metre coordinates.
The third plotting axis is time, **not depth**; distances and volumes in this
mixed-unit grid are not physical spatial measurements. Depth conversion requires
a velocity model. A structured grid also preserves rotated surveys without
pretending they are axis-aligned `ImageData`.

```python
survey = load_poststack('survey.sgy', crs=survey_crs)
processed = filter_poststack(survey)
grid = make_seismic_grid(processed)
plotter = pv.Plotter()
plotter.add_mesh(grid.slice(normal='z', origin=grid.center),
                 scalars='amplitude', cmap='seismic')
plotter.show_axes()
plotter.show()
grid.save('seismic_time_grid.vts')
```

## Common Pipelines

### Basic Seismic QC
```text
- [ ] Load SEG-Y with `segyio.open()`, check trace count and geometry
- [ ] Inspect text and binary headers for acquisition parameters
- [ ] Read trace headers to verify coordinates and fold
- [ ] Compute amplitude statistics (min, max, RMS) per trace
- [ ] Display representative inlines/crosslines with matplotlib
- [ ] Check for dead traces (zero or constant amplitude)
- [ ] Verify sample rate and recording length
```

### AVO Analysis Pipeline
```text
- [ ] Load near and far angle stacks from SEG-Y (segyio)
- [ ] Extract well log Vp, Vs, density at target zone (lasio/welly)
- [ ] Compute AVO response with `bruges.reflection.zoeppritz_rpp()`
- [ ] Classify AVO anomaly (Class I-IV) from intercept and gradient
- [ ] Perform Gassmann fluid substitution for scenario modelling
- [ ] Generate synthetic seismogram and compare to seismic
- [ ] Create AVO crossplot (intercept vs gradient)
```

### Surface Wave Analysis (MASW)
```text
- [ ] Load shot gathers from SEG-Y (segyio)
- [ ] Apply f-k or phase-shift transform to extract dispersion image
- [ ] Pick fundamental mode dispersion curve
- [ ] Fit a 1D Vs model with an optimizer using disba as the dispersion forward solver
- [ ] Repeat for multiple shot points
- [ ] Interpolate Vs profiles into 2D section (verde)
- [ ] Visualize with pyvista or matplotlib
```

### Seismic-to-Well Tie
```text
- [ ] Load seismic section (segyio) and well logs (lasio)
- [ ] Map depth logs to a uniform two-way-time axis with a calibrated time-depth relation
- [ ] Compute acoustic impedance from Vp and density logs
- [ ] Generate reflectivity series from impedance
- [ ] Create Ricker wavelet at dominant frequency (bruges)
- [ ] Convolve reflectivity with wavelet for synthetic
- [ ] Extract seismic trace at well location
- [ ] Cross-correlate synthetic with seismic to find time shift
- [ ] Justify any alignment edits against checkshots; report wavelet and time-depth provenance
```

## When to Use

Use the seismic interpretation workflow when:

- Processing seismic data from SEG-Y files through to interpretation
- Building AVO analysis pipelines that combine well logs and seismic
- Performing seismic QC, attribute extraction, or volume visualization
- Running surface wave analysis (MASW/SASW) workflows
- Creating synthetic seismograms for well ties

Use individual domain skills when:
- Only reading/writing SEG-Y files (use `segyio` alone)
- Only processing waveforms without seismic context (use `obspy` alone)
- Only computing rock physics equations (use `bruges` alone)

## Common Issues

| Issue | Solution |
|-------|----------|
| SEG-Y geometry not detected | Specify `iline=` and `xline=` byte positions in `segyio.open()` |
| obspy Trace stats wrong | Set `sampling_rate` and `delta` correctly from SEG-Y sample interval |
| AVO angles unrealistic | Verify angle range matches acquisition (typically 0-40 degrees) |
| Synthetic does not tie | Check time-depth relationship and wavelet phase |
| Memory error on large cube | Load inline-by-inline instead of full cube |

## API Sources

- [segyio trace, header and cube conventions](https://segyio.readthedocs.io/en/stable/segyio.html)
- [Bruges wavelets](https://code.agilescientific.com/bruges/userguide/Making_wavelets.html)
- [Bruges fluid substitution](https://code.agilescientific.com/bruges/api/bruges.rockphysics.html)
- [disba dispersion units and call signature](https://keurfonluu.github.io/disba/api/dispersion.html)
- [PyVista StructuredGrid](https://docs.pyvista.org/api/core/_autosummary/pyvista.structuredgrid)
