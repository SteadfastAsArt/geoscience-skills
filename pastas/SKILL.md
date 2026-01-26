---
name: pastas
description: Groundwater time series analysis and modelling. Analyze well data, simulate aquifer responses, and forecast groundwater levels using transfer function noise models.
---

# Pastas - Groundwater Time Series Analysis

Help users analyze and model groundwater time series data.

## Installation

```bash
pip install pastas
# For advanced optimization
pip install pastas[solvers]
```

## Core Concepts

### What Pastas Does
- Time series modelling of groundwater levels
- Transfer function noise (TFN) models
- Stress-response analysis (rainfall, pumping)
- Forecasting and hindcasting
- Statistical diagnostics

### Key Classes
| Class | Purpose |
|-------|---------|
| `ps.Model` | Main model container |
| `ps.StressModel` | Response to external stress |
| `ps.RechargeModel` | Recharge from precipitation |
| `ps.Gamma` | Impulse response function |
| `ps.Exponential` | Simple response function |

## Common Workflows

### 1. Basic Model Setup
```python
import pastas as ps
import pandas as pd

# Load groundwater head data
head = pd.read_csv('well_data.csv', index_col=0, parse_dates=True)
head = head.squeeze()  # Convert to Series

# Load precipitation and evaporation
precip = pd.read_csv('precipitation.csv', index_col=0, parse_dates=True).squeeze()
evap = pd.read_csv('evaporation.csv', index_col=0, parse_dates=True).squeeze()

# Create model
ml = ps.Model(head, name='Well_001')

# Add recharge stress (precipitation - evaporation)
sm = ps.RechargeModel(precip, evap, rfunc=ps.Gamma(), name='recharge')
ml.add_stressmodel(sm)

# Solve (calibrate)
ml.solve()

# Plot results
ml.plot()
```

### 2. Model with Pumping Well
```python
import pastas as ps

# Load data
head = pd.read_csv('observation_well.csv', index_col=0, parse_dates=True).squeeze()
precip = pd.read_csv('precipitation.csv', index_col=0, parse_dates=True).squeeze()
evap = pd.read_csv('evaporation.csv', index_col=0, parse_dates=True).squeeze()
pumping = pd.read_csv('pumping_rate.csv', index_col=0, parse_dates=True).squeeze()

# Create model
ml = ps.Model(head)

# Add recharge
ml.add_stressmodel(ps.RechargeModel(precip, evap, rfunc=ps.Gamma(), name='recharge'))

# Add pumping well stress
ml.add_stressmodel(ps.StressModel(pumping, rfunc=ps.Hantush(), name='pumping',
                                   up=False))  # up=False for drawdown

ml.solve()
ml.plot()
```

### 3. Model Diagnostics
```python
import pastas as ps

# After solving model
ml.solve()

# Get model statistics
print(f"EVP: {ml.stats.evp():.1f}%")      # Explained variance
print(f"RMSE: {ml.stats.rmse():.3f} m")   # Root mean square error
print(f"AIC: {ml.stats.aic():.1f}")       # Akaike Information Criterion

# Plot diagnostics
ml.plots.diagnostics()

# Residual analysis
residuals = ml.residuals()
ml.plots.acf()  # Autocorrelation function
```

### 4. Compare Response Functions
```python
import pastas as ps

# Test different response functions
rfuncs = [ps.Gamma(), ps.Exponential(), ps.Hantush(), ps.Polder()]

results = []
for rfunc in rfuncs:
    ml = ps.Model(head)
    ml.add_stressmodel(ps.RechargeModel(precip, evap, rfunc=rfunc, name='recharge'))
    ml.solve(report=False)
    results.append({
        'rfunc': rfunc.name,
        'evp': ml.stats.evp(),
        'aic': ml.stats.aic()
    })

# Compare
import pandas as pd
df = pd.DataFrame(results)
print(df.sort_values('aic'))
```

### 5. Decompose Model Components
```python
import pastas as ps
import matplotlib.pyplot as plt

ml.solve()

# Get individual contributions
contributions = ml.get_contributions()

# Plot decomposition
fig, axes = plt.subplots(len(contributions) + 1, 1, figsize=(10, 8), sharex=True)

# Observed vs simulated
axes[0].plot(head.index, head.values, 'k.', label='Observed')
axes[0].plot(ml.simulate().index, ml.simulate().values, 'b-', label='Simulated')
axes[0].legend()
axes[0].set_ylabel('Head (m)')

# Individual contributions
for i, (name, contrib) in enumerate(contributions.items()):
    axes[i+1].plot(contrib.index, contrib.values)
    axes[i+1].set_ylabel(name)

plt.tight_layout()
plt.show()
```

### 6. Forecast Future Levels
```python
import pastas as ps
import pandas as pd

# Solve model with historical data
ml.solve()

# Create future stress data
future_dates = pd.date_range('2024-01-01', '2025-12-31', freq='D')
future_precip = pd.Series(2.5, index=future_dates)  # mm/day average
future_evap = pd.Series(1.5, index=future_dates)    # mm/day average

# Simulate future
forecast = ml.simulate(tmin='2024-01-01', tmax='2025-12-31')

# Plot
ml.plot(tmax='2025-12-31')
```

### 7. Step Response Analysis
```python
import pastas as ps
import matplotlib.pyplot as plt

ml.solve()

# Get step response for each stress
for name in ml.stressmodels:
    step = ml.get_step_response(name)
    plt.plot(step.index, step.values, label=name)

plt.xlabel('Time (days)')
plt.ylabel('Head response (m)')
plt.legend()
plt.title('Step Response Functions')
plt.show()
```

### 8. Block Response (Impulse Response)
```python
import pastas as ps

ml.solve()

# Get block (impulse) response
block = ml.get_block_response('recharge')

import matplotlib.pyplot as plt
plt.plot(block.index, block.values)
plt.xlabel('Time (days)')
plt.ylabel('Response')
plt.title('Impulse Response Function')
plt.show()
```

### 9. Uncertainty Analysis
```python
import pastas as ps

ml.solve()

# Get parameter confidence intervals
params = ml.parameters
print(params[['optimal', 'stderr']])

# Monte Carlo simulation
# Requires lmfit solver
ml.solve(solver=ps.LmfitSolve)
ci = ml.fit.ci_simulation(n=1000)

# Plot with confidence interval
ml.plot()
```

### 10. Multiple Wells (Pastastore)
```python
import pastas as ps
from pastastore import PastaStore

# Create store
store = PastaStore.from_pastas(name='aquifer_study')

# Add observations
store.add_oseries(head1, 'well_001', metadata={'x': 100, 'y': 200})
store.add_oseries(head2, 'well_002', metadata={'x': 150, 'y': 250})

# Add stresses
store.add_stress(precip, 'precipitation', kind='prec')
store.add_stress(evap, 'evaporation', kind='evap')

# Create and solve models for all wells
for name in store.oseries.index:
    ml = store.create_model(name)
    ml.add_stressmodel(ps.RechargeModel(
        store.get_stress('precipitation'),
        store.get_stress('evaporation'),
        name='recharge'
    ))
    ml.solve()
    store.add_model(ml)
```

### 11. Custom Stress Model
```python
import pastas as ps

# River stage as stress
river = pd.read_csv('river_stage.csv', index_col=0, parse_dates=True).squeeze()

# Create stress model with custom settings
sm = ps.StressModel(
    river,
    rfunc=ps.Exponential(),
    name='river',
    settings='waterlevel'  # Predefined settings for water level data
)

ml.add_stressmodel(sm)
ml.solve()
```

### 12. Export Results
```python
import pastas as ps

ml.solve()

# Export to JSON
ml.to_json('model.pas')

# Load model
ml_loaded = ps.io.load('model.pas')

# Export simulation to CSV
sim = ml.simulate()
sim.to_csv('simulation.csv')

# Export parameters
params = ml.parameters
params.to_csv('parameters.csv')
```

## Response Functions

| Function | Description | Use Case |
|----------|-------------|----------|
| `Gamma` | Gamma distribution | General recharge |
| `Exponential` | Single exponential | Simple aquifer |
| `Hantush` | Leaky aquifer | Wells with leakage |
| `Polder` | Polder systems | Managed water levels |
| `FourParam` | 4-parameter | Flexible response |

## Model Statistics

| Statistic | Description | Good Value |
|-----------|-------------|------------|
| EVP | Explained variance | >70% |
| RMSE | Root mean square error | Low |
| AIC | Akaike Information Criterion | Lower = better |
| BIC | Bayesian Information Criterion | Lower = better |

## Tips

1. **Start simple** - Add stresses incrementally
2. **Check residuals** - Should be white noise
3. **Compare response functions** - Use AIC to select
4. **Use daily data** - Pastas works best with daily
5. **Normalize units** - Precipitation in mm/day, head in m

## Resources

- Documentation: https://pastas.readthedocs.io/
- GitHub: https://github.com/pastas/pastas
- Examples: https://github.com/pastas/pastas/tree/main/examples
- Publications: Check Zotero group for papers using Pastas
