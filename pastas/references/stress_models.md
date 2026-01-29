# Pastas Stress Models

## Table of Contents
- [Overview](#overview)
- [StressModel](#stressmodel)
- [RechargeModel](#rechargemodel)
- [WellModel](#wellmodel)
- [Stress Settings](#stress-settings)
- [Multiple Stresses](#multiple-stresses)

## Overview

Stress models describe how external influences (stresses) affect groundwater levels. Each stress model combines:
- **Stress time series** - The input signal (e.g., precipitation, pumping)
- **Response function** - How the aquifer responds over time

## StressModel

The general-purpose stress model for any single time series input.

```python
import pastas as ps

# Basic stress model
sm = ps.StressModel(stress, rfunc=ps.Gamma(), name='stress_name')
ml.add_stressmodel(sm)
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `stress` | Pandas Series with datetime index | Required |
| `rfunc` | Response function object | Required |
| `name` | Identifier for the stress | Required |
| `up` | True if stress increases head | True |
| `settings` | Predefined settings string | None |

### Common Use Cases

```python
# Pumping well (causes drawdown)
sm = ps.StressModel(pumping, rfunc=ps.Hantush(), name='pumping', up=False)

# River stage (water level input)
sm = ps.StressModel(river, rfunc=ps.Exponential(), name='river',
                    settings='waterlevel')

# Barometric pressure
sm = ps.StressModel(baro, rfunc=ps.One(), name='baro', settings='prec')
```

## RechargeModel

Specialized model for groundwater recharge from precipitation and evaporation.

```python
# Basic recharge model
sm = ps.RechargeModel(precip, evap, rfunc=ps.Gamma(), name='recharge')
ml.add_stressmodel(sm)
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `prec` | Precipitation series (mm/day) | Required |
| `evap` | Evaporation series (mm/day) | Required |
| `rfunc` | Response function | Required |
| `name` | Identifier | Required |
| `recharge` | Recharge calculation method | 'Linear' |

### Recharge Methods

| Method | Formula | Use Case |
|--------|---------|----------|
| `'Linear'` | P - f*E | Default, simple linear |
| `'FlexModel'` | Non-linear | Variable recharge factor |
| `'Berendrecht'` | Soil moisture model | Detailed water balance |

```python
# With FlexModel recharge
sm = ps.RechargeModel(precip, evap, rfunc=ps.Gamma(),
                      name='recharge', recharge='FlexModel')
```

## WellModel

For modeling pumping well influence with distance considerations.

```python
# Well model with distance
sm = ps.WellModel(
    stress=[pumping1, pumping2],      # List of pumping series
    rfunc=ps.Hantush(),
    name='wells',
    distances=[100, 250],             # Distances to observation well (m)
    up=False
)
ml.add_stressmodel(sm)
```

### Parameters

| Parameter | Description |
|-----------|-------------|
| `stress` | List of pumping time series |
| `rfunc` | Response function (typically Hantush) |
| `distances` | List of distances from each well |
| `up` | False for pumping (drawdown) |

## Stress Settings

Predefined settings for common stress types:

| Setting | Description | Typical Use |
|---------|-------------|-------------|
| `'prec'` | Precipitation | Rainfall data |
| `'evap'` | Evaporation | Evapotranspiration |
| `'well'` | Pumping well | Extraction rates |
| `'waterlevel'` | Surface water level | River/lake stage |
| `'head'` | Groundwater head | Boundary conditions |

```python
# Using settings
sm = ps.StressModel(river, rfunc=ps.Exponential(),
                    name='river', settings='waterlevel')
```

## Multiple Stresses

Models can include multiple stress models to capture different influences:

```python
ml = ps.Model(head, name='well')

# Recharge
ml.add_stressmodel(ps.RechargeModel(
    precip, evap, rfunc=ps.Gamma(), name='recharge'
))

# Pumping
ml.add_stressmodel(ps.StressModel(
    pumping, rfunc=ps.Hantush(), name='pumping', up=False
))

# River
ml.add_stressmodel(ps.StressModel(
    river, rfunc=ps.Exponential(), name='river', settings='waterlevel'
))

ml.solve()

# Get individual contributions
for name, contrib in ml.get_contributions().items():
    print(f"{name}: {contrib.mean():.3f} m")
```

## Stress Model Selection Guide

| Stress Type | Model | Response Function |
|-------------|-------|-------------------|
| Precipitation + Evap | `RechargeModel` | Gamma, Exponential |
| Single pumping well | `StressModel(up=False)` | Hantush, Theis |
| Multiple pumping wells | `WellModel` | Hantush |
| River/lake level | `StressModel` | Exponential, Polder |
| Barometric pressure | `StressModel` | One |
| Temperature | `StressModel` | Gamma |

## Parameter Bounds

Set parameter bounds to constrain calibration:

```python
# After adding stress model
ml.set_parameter('recharge_A', initial=100, pmin=1, pmax=1000)
ml.set_parameter('recharge_a', initial=10, pmin=1, pmax=365)
```

Common parameter naming convention:
- `{name}_A` - Scaling factor
- `{name}_a` - Time parameter (days)
- `{name}_n` - Shape parameter
