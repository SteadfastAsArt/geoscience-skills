# Geophysical Methods in pyGIMLi

## Table of Contents
- [Electrical Resistivity Tomography (ERT)](#electrical-resistivity-tomography-ert)
- [Seismic Refraction Tomography (SRT)](#seismic-refraction-tomography-srt)
- [Induced Polarization (IP)](#induced-polarization-ip)
- [Time-Lapse Monitoring](#time-lapse-monitoring)
- [Joint Inversion](#joint-inversion)
- [Ground Penetrating Radar (GPR)](#ground-penetrating-radar-gpr)

## Electrical Resistivity Tomography (ERT)

ERT maps subsurface resistivity distribution from surface electrical measurements.

### Basic Workflow
```python
from pygimli.physics import ert

# Load and inspect data
data = ert.load("survey.ohm")
print(data)
ert.showData(data)

# Inversion
mgr = ert.ERTManager(data)
model = mgr.invert(lam=20, verbose=True)
mgr.showResult()
```

### Inversion Parameters

| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| `lam` | Regularization strength | 10-100 |
| `zWeight` | Vertical smoothing weight | 0.1-1.0 |
| `maxIter` | Maximum iterations | 10-50 |
| `robustData` | Robust data weighting | True/False |
| `blockyModel` | Minimum gradient support | True/False |

### Quality Assessment
```python
# Coverage (sensitivity)
coverage = mgr.coverage()
pg.show(mgr.mesh, coverage, label='Coverage')

# Chi-squared misfit
chi2 = mgr.inv.chi2()
print(f"Chi-squared = {chi2:.2f}")

# Relative RMS
rms = mgr.inv.relrms()
print(f"Relative RMS = {rms:.1f}%")
```

### Data Filtering
```python
# Remove bad data points
data = ert.load("survey.ohm")

# Filter by apparent resistivity range
valid = (data['rhoa'] > 1) & (data['rhoa'] < 10000)
data.markInvalid(~valid)
data.removeInvalid()

# Filter by geometric factor
data.markInvalid(data['k'] > 1000)
data.removeInvalid()
```

## Seismic Refraction Tomography (SRT)

SRT maps subsurface velocity structure from first-arrival traveltimes.

### Basic Workflow
```python
from pygimli.physics import srt

# Load traveltime data
data = srt.load("traveltimes.sgt")

# View traveltimes
srt.showData(data)

# Inversion
mgr = srt.SRTManager(data)
model = mgr.invert(
    lam=30,
    zWeight=0.3,
    verbose=True
)
mgr.showResult()
```

### Velocity Constraints
```python
# Set velocity bounds
mgr.invert(
    lam=30,
    limits=[200, 5000],  # Min/max velocity m/s
    verbose=True
)
```

### First-Arrival Picking
```python
# If you have raw seismic data
from pygimli.physics.srt import firstArrival

# Load SEG-Y traces (external library)
# times = firstArrival(traces, dt)
```

## Induced Polarization (IP)

IP measures chargeability or phase shift, indicating clay content or mineralization.

### Time-Domain IP
```python
from pygimli.physics import ert

# Load data with chargeability
data = pg.load("ip_survey.ohm")

# First invert resistivity
mgr = ert.ERTManager(data)
mgr.invert(lam=20)

# Then invert IP
ip_model = mgr.invertIPData(data['ip'])
mgr.showIPModel(ip_model)
```

### Spectral IP
```python
# For frequency-domain measurements
from pygimli.physics import SIP

# Load SIP data (multiple frequencies)
sip_data = pg.load("sip_survey.ohm")

# Inversion with Cole-Cole model
# sip = SIPManager(sip_data)
# sip.invert()
```

## Time-Lapse Monitoring

Track subsurface changes over time.

### Ratio Approach
```python
from pygimli.physics import ert

# Load baseline and monitor datasets
data_base = ert.load("baseline.ohm")
data_mon = ert.load("monitor.ohm")

# Invert baseline
mgr = ert.ERTManager(data_base)
model_base = mgr.invert(lam=20)

# Time-lapse inversion
from pygimli.physics.ert import TimelapseERT

tl = TimelapseERT([data_base, data_mon])
tl.invert(lam=20)

# Show ratio of changes
tl.showResults()
```

### 4D Inversion
```python
# For multiple time steps
datasets = [ert.load(f"survey_t{i}.ohm") for i in range(5)]
tl = TimelapseERT(datasets)
tl.invert(lam=20)

# Animate results
for i, model in enumerate(tl.models):
    pg.show(tl.mesh, model, label=f'Time {i}')
```

## Joint Inversion

Combine multiple geophysical methods for better constraints.

### Structurally Coupled Joint Inversion
```python
from pygimli.physics import ert, srt
from pygimli.frameworks import JointInversion

# Load both datasets
ert_data = ert.load("ert_survey.ohm")
srt_data = srt.load("srt_survey.sgt")

# Create managers
ert_mgr = ert.ERTManager(ert_data)
srt_mgr = srt.SRTManager(srt_data)

# Joint inversion with structural coupling
ji = JointInversion([ert_mgr, srt_mgr])
ji.invert(lam=20)

# Access individual models
ert_model = ji.models[0]
srt_model = ji.models[1]
```

### Petrophysical Joint Inversion
```python
# When physical relationship exists between properties
from pygimli.frameworks import PetroJointInversion

# Define rock physics relationship
# e.g., Archie's law: resistivity = a * porosity^(-m)

# pji = PetroJointInversion(...)
# pji.invert()
```

## Ground Penetrating Radar (GPR)

GPR simulation and analysis (forward modelling focus).

### FDTD Simulation
```python
import pygimli as pg
from pygimli.physics import gpr

# Create velocity/permittivity model
mesh = pg.createGrid(x=np.linspace(0, 10, 101),
                     y=np.linspace(-5, 0, 51))

# Permittivity model (relative)
er = np.ones(mesh.cellCount()) * 9  # Background
er[mesh.cellCenters()[:, 1] > -2] = 4  # Top layer

# Forward modelling
# Note: Full GPR modelling may require additional packages
```

### Velocity Analysis
```python
# Convert permittivity to velocity
c = 0.3  # Speed of light in m/ns
velocity = c / np.sqrt(er)

# Two-way traveltime
depth = 5  # meters
twt = 2 * depth / velocity  # nanoseconds
```

## Common Physical Properties

### Typical Resistivity Values (Ohm-m)

| Material | Resistivity |
|----------|-------------|
| Clay | 1-100 |
| Sand (dry) | 100-1000 |
| Sand (saturated) | 10-100 |
| Gravel | 100-10000 |
| Limestone | 100-10000 |
| Granite | 1000-100000 |
| Saltwater | 0.1-1 |
| Freshwater | 10-100 |

### Typical P-wave Velocities (m/s)

| Material | Velocity |
|----------|----------|
| Air | 330 |
| Water | 1500 |
| Dry sand | 200-500 |
| Saturated sand | 1500-2000 |
| Clay | 1000-2500 |
| Limestone | 2000-6000 |
| Granite | 4500-6500 |
