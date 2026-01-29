# SimPEG Survey Types and Configurations

## Table of Contents
- [DC Resistivity](#dc-resistivity)
- [Induced Polarization](#induced-polarization)
- [Magnetics](#magnetics)
- [Gravity](#gravity)
- [Time-Domain EM](#time-domain-em)
- [Frequency-Domain EM](#frequency-domain-em)
- [Magnetotellurics](#magnetotellurics)

## DC Resistivity

### Survey Configurations

| Configuration | Description | Best For |
|--------------|-------------|----------|
| Dipole-Dipole | Current and potential dipoles | Lateral resolution |
| Wenner | Equal spacing A-M-N-B | Vertical resolution |
| Schlumberger | Expanding current electrodes | Deep sounding |
| Pole-Dipole | One current at infinity | Near-surface |
| Pole-Pole | Both currents at infinity | Large coverage |

### Dipole-Dipole Survey
```python
from simpeg.electromagnetics.static import resistivity as dc
import numpy as np

# Electrode locations along survey line
n_electrodes = 21
spacing = 10  # meters
electrode_x = np.linspace(0, (n_electrodes-1)*spacing, n_electrodes)
electrode_locs = np.c_[electrode_x, np.zeros(n_electrodes)]

source_list = []
for i in range(n_electrodes - 3):
    # Current electrodes A, B
    a_loc = electrode_locs[i]
    b_loc = electrode_locs[i + 1]

    # Potential electrodes M, N for multiple n-spacings
    rx_list = []
    for n in range(1, min(6, n_electrodes - i - 2)):
        m_loc = electrode_locs[i + 1 + n]
        n_loc = electrode_locs[i + 2 + n]
        rx = dc.receivers.Dipole(m_loc.reshape(1, -1), n_loc.reshape(1, -1))
        rx_list.append(rx)

    src = dc.sources.Dipole(rx_list, a_loc, b_loc)
    source_list.append(src)

survey = dc.Survey(source_list)
```

### Wenner Survey
```python
source_list = []
for a_spacing in [10, 20, 40, 80]:  # Expanding array
    for start in range(0, n_electrodes - 3):
        if start + 3 * (a_spacing // 10) < n_electrodes:
            a_loc = electrode_locs[start]
            m_loc = electrode_locs[start + a_spacing // 10]
            n_loc = electrode_locs[start + 2 * (a_spacing // 10)]
            b_loc = electrode_locs[start + 3 * (a_spacing // 10)]

            rx = dc.receivers.Dipole(m_loc.reshape(1, -1), n_loc.reshape(1, -1))
            src = dc.sources.Dipole([rx], a_loc, b_loc)
            source_list.append(src)
```

### Data Types

| Receiver | Output | Units |
|----------|--------|-------|
| `Dipole` | Voltage difference | V |
| `Pole` | Voltage | V |

## Induced Polarization

```python
from simpeg.electromagnetics.static import induced_polarization as ip

# IP uses same geometry as DC
rx = ip.receivers.Dipole(m_locs, n_locs, data_type='apparent_chargeability')
src = ip.sources.Dipole([rx], a_loc, b_loc)
survey = ip.Survey([src])
```

### IP Data Types
- `apparent_chargeability` - Unitless (0-1)
- `secondary_potential` - Volts

## Magnetics

### Total Field Anomaly Survey
```python
from simpeg.potential_fields import magnetics

# Receiver locations (typically airborne or ground grid)
rx_x, rx_y = np.meshgrid(np.linspace(-500, 500, 21), np.linspace(-500, 500, 21))
rx_locs = np.c_[rx_x.ravel(), rx_y.ravel(), np.ones(rx_x.size) * 100]  # 100m altitude

# Total magnetic intensity receiver
rx = magnetics.receivers.Point(rx_locs, components='tmi')

# Background field
src = magnetics.sources.UniformBackgroundField(
    receiver_list=[rx],
    amplitude=50000,    # nT (typical Earth field)
    inclination=60,     # degrees from horizontal
    declination=10      # degrees from north
)

survey = magnetics.Survey(src)
```

### Magnetic Components

| Component | Description |
|-----------|-------------|
| `tmi` | Total magnetic intensity anomaly |
| `bx`, `by`, `bz` | Vector components |
| `bxx`, `bxy`, ... | Gradient tensor |

## Gravity

### Vertical Gravity Survey
```python
from simpeg.potential_fields import gravity

# Station locations
rx_locs = np.c_[x_stations, y_stations, z_stations]

# Vertical component (most common)
rx = gravity.receivers.Point(rx_locs, components='gz')
src = gravity.sources.SourceField(receiver_list=[rx])
survey = gravity.Survey(src)
```

### Gravity Components

| Component | Description | Units |
|-----------|-------------|-------|
| `gz` | Vertical gravity | mGal |
| `gx`, `gy` | Horizontal components | mGal |
| `gxx`, `gxy`, ... | Gravity gradient tensor | Eotvos |

### Full Tensor Gradiometry
```python
components = ['gxx', 'gxy', 'gxz', 'gyy', 'gyz', 'gzz']
rx = gravity.receivers.Point(rx_locs, components=components)
```

## Time-Domain EM

### Central Loop TEM
```python
from simpeg.electromagnetics import time_domain as tdem

# Measurement times
times = np.logspace(-5, -2, 31)  # 10us to 10ms

# Receiver: dB/dt at loop center
rx = tdem.receivers.PointMagneticFluxTimeDerivative(
    locations=np.array([[0, 0, 0]]),
    times=times,
    orientation='z'
)

# Transmitter: square loop
tx_vertices = np.array([
    [-50, -50, 0], [50, -50, 0], [50, 50, 0], [-50, 50, 0], [-50, -50, 0]
])
src = tdem.sources.LineCurrent(
    receiver_list=[rx],
    location=tx_vertices,
    waveform=tdem.sources.StepOffWaveform()
)

survey = tdem.Survey([src])
```

### TEM Receiver Types

| Receiver | Measures | Units |
|----------|----------|-------|
| `PointMagneticFluxDensity` | B field | T |
| `PointMagneticFluxTimeDerivative` | dB/dt | T/s |
| `PointElectricField` | E field | V/m |

## Frequency-Domain EM

### Horizontal Loop EM (HLEM)
```python
from simpeg.electromagnetics import frequency_domain as fdem

frequencies = [400, 1800, 7200, 28800]  # Hz

source_list = []
for freq in frequencies:
    # Horizontal coplanar configuration
    rx = fdem.receivers.PointMagneticFluxDensitySecondary(
        locations=np.array([[100, 0, 0]]),  # 100m offset
        orientation='z',
        component='both'  # real and imaginary
    )
    src = fdem.sources.MagDipole(
        receiver_list=[rx],
        location=np.array([0, 0, 0]),
        frequency=freq,
        orientation='z'
    )
    source_list.append(src)

survey = fdem.Survey(source_list)
```

## Magnetotellurics

### MT Survey
```python
from simpeg.electromagnetics import natural_source as nsem

frequencies = np.logspace(-3, 3, 31)  # 0.001 to 1000 Hz

# Impedance tensor components
rx_list = [
    nsem.receivers.PointNaturalSource(
        locations=rx_locs,
        orientation='xy',
        component='real'
    ),
    nsem.receivers.PointNaturalSource(
        locations=rx_locs,
        orientation='xy',
        component='imag'
    ),
    # Add yx, xx, yy components as needed
]

source_list = [
    nsem.sources.PlanewaveXYPrimary(rx_list, frequency=f)
    for f in frequencies
]

survey = nsem.Survey(source_list)
```

### MT Output

| Component | Description |
|-----------|-------------|
| Zxy, Zyx | Off-diagonal impedance |
| Zxx, Zyy | Diagonal impedance |
| Apparent resistivity | Derived from Z |
| Phase | Derived from Z |
