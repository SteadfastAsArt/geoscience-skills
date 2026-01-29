# Landlab Components Reference

## Table of Contents
- [Flow Routing](#flow-routing)
- [Erosion](#erosion)
- [Hillslope Processes](#hillslope-processes)
- [Weathering](#weathering)
- [Hydrology](#hydrology)
- [Tectonics](#tectonics)
- [Analysis](#analysis)

## Flow Routing

| Component | Description | Key Parameters |
|-----------|-------------|----------------|
| `FlowAccumulator` | Routes flow and calculates drainage area | `flow_director`, `runoff_rate` |
| `FlowDirectorD8` | Single-direction flow (steepest of 8) | - |
| `FlowDirectorSteepest` | Single-direction flow (any neighbor) | - |
| `FlowDirectorMFD` | Multiple flow directions | `partition_method` |
| `FlowDirectorDINF` | D-infinity flow direction | - |
| `LakeMapperBarnes` | Fill/route through depressions | `method`, `fill_flat` |
| `DepressionFinderAndRouter` | Find and route through sinks | `routing` |

### FlowAccumulator Example
```python
from landlab.components import FlowAccumulator

fa = FlowAccumulator(
    grid,
    flow_director='D8',        # 'Steepest', 'MFD', 'DINF'
    runoff_rate=1.0,           # m/yr
    depression_finder='LakeMapperBarnes'
)
fa.run_one_step()

# Output fields
grid.at_node['drainage_area']
grid.at_node['flow__receiver_node']
grid.at_node['flow__upstream_node_order']
```

## Erosion

| Component | Description | Key Parameters |
|-----------|-------------|----------------|
| `StreamPowerEroder` | Detachment-limited stream power | `K_sp`, `m_sp`, `n_sp` |
| `FastscapeEroder` | Implicit stream power (faster) | `K_sp`, `m_sp`, `n_sp` |
| `StreamPowerSmoothThresholdEroder` | Stream power with threshold | `K_sp`, `threshold_sp` |
| `SedDepEroder` | Sediment-flux-dependent erosion | `K_sp`, `F_f`, `phi` |
| `ErosionDeposition` | Combined erosion and deposition | `K`, `v_s`, `m_sp`, `n_sp` |
| `Space` | Stream power with alluvium | `K_sed`, `K_br`, `H_star` |

### StreamPowerEroder Example
```python
from landlab.components import StreamPowerEroder

sp = StreamPowerEroder(
    grid,
    K_sp=1e-5,      # Erodibility coefficient
    m_sp=0.5,       # Drainage area exponent
    n_sp=1.0,       # Slope exponent
    threshold_sp=0  # Erosion threshold
)
sp.run_one_step(dt=1000)  # dt in years
```

### Space Example (Sediment-Flux Model)
```python
from landlab.components import SpaceLargeScaleEroder

space = SpaceLargeScaleEroder(
    grid,
    K_sed=1e-5,     # Sediment erodibility
    K_br=1e-6,      # Bedrock erodibility
    F_f=0.0,        # Fraction fines
    phi=0.3,        # Sediment porosity
    H_star=0.1,     # Characteristic sediment thickness
    v_s=1.0         # Settling velocity
)
```

## Hillslope Processes

| Component | Description | Key Parameters |
|-----------|-------------|----------------|
| `LinearDiffuser` | Linear hillslope diffusion | `linear_diffusivity` |
| `PerronNLDiffuse` | Nonlinear diffusion | `kappa` |
| `TaylorNonLinearDiffuser` | Taylor series nonlinear | `nterms`, `linear_diffusivity` |
| `DepthDependentDiffuser` | Depth-dependent transport | `linear_diffusivity` |
| `DepthDependentTaylorDiffuser` | Combines both | `soil_transport_decay_depth` |

### LinearDiffuser Example
```python
from landlab.components import LinearDiffuser

ld = LinearDiffuser(
    grid,
    linear_diffusivity=0.01  # m^2/yr
)
ld.run_one_step(dt=100)  # years
```

### Nonlinear Diffusion Example
```python
from landlab.components import TaylorNonLinearDiffuser

nld = TaylorNonLinearDiffuser(
    grid,
    linear_diffusivity=0.01,
    slope_crit=0.6,   # Critical slope (tan)
    nterms=2          # Taylor series terms
)
```

## Weathering

| Component | Description | Key Parameters |
|-----------|-------------|----------------|
| `ExponentialWeatherer` | Exponential soil production | `max_soil_production_rate`, `soil_production_decay_depth` |
| `ExponentialWeathererIntegrated` | Time-integrated version | same |

### ExponentialWeatherer Example
```python
from landlab.components import ExponentialWeatherer

# Requires soil__depth field
grid.add_zeros('soil__depth', at='node')

weatherer = ExponentialWeatherer(
    grid,
    max_soil_production_rate=0.001,    # m/yr (at zero soil depth)
    soil_production_decay_depth=0.5     # m (e-folding depth)
)
weatherer.run_one_step(dt=100)

# Updates: soil__depth, soil_production__rate
```

## Hydrology

| Component | Description | Key Parameters |
|-----------|-------------|----------------|
| `KinwaveOverlandFlowModel` | Kinematic wave overland flow | `mannings_n`, `critical_depth` |
| `OverlandFlow` | 2D overland flow | `mannings_n` |
| `GroundwaterDupuitPercolator` | Dupuit groundwater | `hydraulic_conductivity` |
| `PrecipitationDistribution` | Generate storm series | `mean_storm_duration`, `mean_storm_depth` |

### Overland Flow Example
```python
from landlab.components import KinwaveOverlandFlowModel

kw = KinwaveOverlandFlowModel(
    grid,
    mannings_n=0.03,
    critical_depth=0.003
)

grid.at_node['surface_water__depth'] = 0.01  # Initial condition
kw.run_one_step(dt=60)  # seconds
```

### Precipitation Example
```python
from landlab.components import PrecipitationDistribution

precip = PrecipitationDistribution(
    grid,
    mean_storm_duration=2.0,        # hours
    mean_interstorm_duration=24.0,  # hours
    mean_storm_depth=0.01           # m
)
precip.update()
intensity = precip.intensity  # m/hr
```

## Tectonics

| Component | Description | Key Parameters |
|-----------|-------------|----------------|
| `ListricKinematicExtender` | Listric fault extension | `fault_dip`, `fault_location` |
| `NormalFault` | Normal fault displacement | `fault_throw_rate_through_time` |

### Uplift (Manual)
```python
# Apply uniform uplift to interior nodes
uplift_rate = 0.001  # m/yr
dt = 1000  # years
z[grid.core_nodes] += uplift_rate * dt
```

## Analysis

| Component | Description | Key Parameters |
|-----------|-------------|----------------|
| `ChannelProfiler` | Extract channel profiles | `number_of_watersheds`, `minimum_channel_threshold` |
| `ChiFinder` | Calculate chi coordinates | `min_drainage_area`, `reference_concavity` |
| `DrainageDensity` | Calculate drainage density | `channel_definition_field` |
| `Profiler` | Generic line profiler | - |
| `SteepnessFinder` | Calculate steepness index | `min_drainage_area`, `reference_concavity` |

### ChannelProfiler Example
```python
from landlab.components import ChannelProfiler

profiler = ChannelProfiler(
    grid,
    number_of_watersheds=1,
    minimum_channel_threshold=1e6  # m^2 drainage area
)
profiler.run_one_step()

# Access profile data
for outlet, segments in profiler.data_structure.items():
    for segment_id, node_ids in segments.items():
        distances = profiler.data_structure[outlet][segment_id]['distances']
        elevations = z[node_ids]
```

### ChiFinder Example
```python
from landlab.components import ChiFinder

cf = ChiFinder(
    grid,
    min_drainage_area=1e5,     # m^2
    reference_concavity=0.45,
    reference_area=1.0
)
cf.calculate_chi()

chi = grid.at_node['channel__chi_index']
```

## Common Field Names

| Field Name | Description | Created By |
|------------|-------------|------------|
| `topographic__elevation` | Surface elevation | User |
| `drainage_area` | Upstream drainage area | FlowAccumulator |
| `flow__receiver_node` | Downstream node | FlowAccumulator |
| `surface_water__discharge` | Water discharge | FlowAccumulator |
| `soil__depth` | Soil thickness | User/ExponentialWeatherer |
| `sediment__flux` | Sediment flux | ErosionDeposition/Space |
