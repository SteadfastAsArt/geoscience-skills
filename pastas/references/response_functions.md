# Pastas Response Functions

## Table of Contents
- [Overview](#overview)
- [Available Functions](#available-functions)
- [Function Comparison](#function-comparison)
- [Selection Guide](#selection-guide)
- [Custom Parameters](#custom-parameters)

## Overview

Response functions (also called impulse response functions or transfer functions) describe how an aquifer responds to a unit stress input over time. The choice of response function affects:
- Model fit quality
- Physical interpretability
- Number of parameters to calibrate

## Available Functions

### Gamma

Most commonly used response function. Flexible shape with 3 parameters.

```python
import pastas as ps

rfunc = ps.Gamma()
ml.add_stressmodel(ps.RechargeModel(precip, evap, rfunc=rfunc, name='recharge'))
```

| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| A | Scaling factor | 10-1000 |
| a | Time scale (days) | 1-365 |
| n | Shape parameter | 0.5-5 |

**Best for**: General recharge modeling, flexible aquifer responses

### Exponential

Simple single-parameter response. Instant peak, exponential decay.

```python
rfunc = ps.Exponential()
```

| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| A | Scaling factor | 10-1000 |
| a | Decay time (days) | 1-365 |

**Best for**: Simple aquifers, quick tests, when Gamma is unstable

### Hantush

Based on Hantush well function. Includes leakage effects.

```python
rfunc = ps.Hantush()
ml.add_stressmodel(ps.StressModel(pumping, rfunc=rfunc, name='pump', up=False))
```

| Parameter | Description | Typical Range |
|-----------|-------------|---------------|
| A | Scaling factor | Varies |
| a | Time parameter | 1-1000 |
| b | Leakage parameter | 0.001-1 |

**Best for**: Pumping wells, leaky aquifers, semi-confined conditions

### Polder

Designed for polder (managed water level) systems.

```python
rfunc = ps.Polder()
```

| Parameter | Description |
|-----------|-------------|
| A | Scaling factor |
| a | Fast response time |
| b | Slow response time |

**Best for**: Polders, managed drainage systems, dual-porosity responses

### FourParam

Four-parameter response for maximum flexibility.

```python
rfunc = ps.FourParam()
```

**Best for**: Complex systems where simpler functions don't fit

### One

Instantaneous response (no delay). Useful for direct effects.

```python
rfunc = ps.One()
```

**Best for**: Barometric effects, instantaneous responses

### Theis

Classic Theis well function for confined aquifers.

```python
rfunc = ps.Theis()
```

**Best for**: Confined aquifer pumping tests, ideal conditions

## Function Comparison

### Visual Characteristics

| Function | Peak Location | Tail Behavior | Flexibility |
|----------|---------------|---------------|-------------|
| Gamma | Delayed | Moderate decay | High |
| Exponential | Instant | Fast decay | Low |
| Hantush | Instant | Slow decay | Medium |
| Polder | Two peaks | Dual decay | Medium |
| FourParam | Variable | Variable | Very high |

### Parameter Count

| Function | Parameters | Degrees of Freedom |
|----------|------------|-------------------|
| One | 1 | 1 |
| Exponential | 2 | 2 |
| Gamma | 3 | 3 |
| Hantush | 3 | 3 |
| Polder | 3 | 3 |
| FourParam | 4 | 4 |

## Selection Guide

### By Stress Type

| Stress | Recommended Functions |
|--------|----------------------|
| Precipitation/Recharge | Gamma, Exponential |
| Pumping (confined) | Theis, Hantush |
| Pumping (leaky) | Hantush |
| River stage | Exponential, Polder |
| Barometric pressure | One |

### By Aquifer Type

| Aquifer Type | Best Functions |
|--------------|----------------|
| Unconfined, simple | Exponential |
| Unconfined, complex | Gamma |
| Confined | Theis, Exponential |
| Semi-confined/Leaky | Hantush |
| Polder/Managed | Polder |

### Selection Workflow

```python
import pastas as ps
import pandas as pd

# Compare response functions
results = []
for rfunc in [ps.Gamma(), ps.Exponential(), ps.Hantush()]:
    ml = ps.Model(head.copy())
    ml.add_stressmodel(ps.RechargeModel(precip, evap, rfunc=rfunc, name='r'))
    ml.solve(report=False)
    results.append({
        'function': rfunc.name,
        'evp': ml.stats.evp(),
        'aic': ml.stats.aic(),
        'bic': ml.stats.bic(),
        'n_params': len([p for p in ml.parameters.index if p.startswith('r_')])
    })

df = pd.DataFrame(results)
print(df.sort_values('aic'))  # Lower AIC = better model
```

## Custom Parameters

### Set Initial Values

```python
ml = ps.Model(head)
sm = ps.RechargeModel(precip, evap, rfunc=ps.Gamma(), name='recharge')
ml.add_stressmodel(sm)

# Set initial parameter values
ml.set_parameter('recharge_A', initial=200)
ml.set_parameter('recharge_a', initial=50)
ml.set_parameter('recharge_n', initial=1.5)
```

### Set Bounds

```python
# Constrain parameters
ml.set_parameter('recharge_A', pmin=10, pmax=500)
ml.set_parameter('recharge_a', pmin=1, pmax=200)
ml.set_parameter('recharge_n', pmin=0.5, pmax=3)
```

### Fix Parameters

```python
# Fix a parameter (don't optimize)
ml.set_parameter('recharge_n', vary=False, initial=1.0)
```

## Response Analysis

### Extract Response Function

```python
ml.solve()

# Step response (cumulative)
step = ml.get_step_response('recharge')

# Block/impulse response
block = ml.get_block_response('recharge')

# Plot
import matplotlib.pyplot as plt
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
ax1.plot(step.index, step.values)
ax1.set_xlabel('Time (days)')
ax1.set_ylabel('Step response')

ax2.plot(block.index, block.values)
ax2.set_xlabel('Time (days)')
ax2.set_ylabel('Impulse response')
plt.show()
```

### Response Characteristics

```python
# Get response function parameters
params = ml.parameters
print(params[params.index.str.startswith('recharge')])

# Calculate response time (time to 90% of step response)
step = ml.get_step_response('recharge')
t90_idx = (step / step.iloc[-1] >= 0.9).idxmax()
print(f"Response time (90%): {t90_idx} days")
```
