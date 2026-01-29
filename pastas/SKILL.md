---
name: pastas
description: |
  Groundwater time series analysis and modelling using transfer function noise
  models. Use when Claude needs to: (1) Analyze groundwater level time series,
  (2) Model well responses to precipitation/pumping, (3) Calibrate aquifer
  parameters from head data, (4) Forecast or hindcast groundwater levels,
  (5) Decompose hydrological signals into components, (6) Compare response
  functions, (7) Perform model diagnostics and uncertainty analysis.
---

# Pastas - Groundwater Time Series Analysis

## Quick Reference

```python
import pastas as ps
import pandas as pd

# Load data
head = pd.read_csv('well.csv', index_col=0, parse_dates=True).squeeze()
precip = pd.read_csv('precip.csv', index_col=0, parse_dates=True).squeeze()
evap = pd.read_csv('evap.csv', index_col=0, parse_dates=True).squeeze()

# Create model
ml = ps.Model(head, name='Well_001')

# Add recharge stress
sm = ps.RechargeModel(precip, evap, rfunc=ps.Gamma(), name='recharge')
ml.add_stressmodel(sm)

# Solve and plot
ml.solve()
ml.plot()
```

## Key Classes

| Class | Purpose |
|-------|---------|
| `ps.Model` | Main model container |
| `ps.StressModel` | Response to external stress (pumping, river) |
| `ps.RechargeModel` | Recharge from precipitation minus evaporation |
| `ps.Gamma` | Gamma distribution response function |
| `ps.Exponential` | Simple exponential response function |

## Essential Operations

### Create and Solve Model
```python
ml = ps.Model(head, name='well')
ml.add_stressmodel(ps.RechargeModel(precip, evap, rfunc=ps.Gamma(), name='recharge'))
ml.solve()
```

### Add Pumping Well
```python
pumping = pd.read_csv('pumping.csv', index_col=0, parse_dates=True).squeeze()
ml.add_stressmodel(ps.StressModel(pumping, rfunc=ps.Hantush(),
                                   name='pumping', up=False))  # up=False for drawdown
```

### Model Diagnostics
```python
print(f"EVP: {ml.stats.evp():.1f}%")      # Explained variance
print(f"RMSE: {ml.stats.rmse():.3f} m")   # Root mean square error
print(f"AIC: {ml.stats.aic():.1f}")       # Model selection criterion

ml.plots.diagnostics()                     # Diagnostic plots
ml.plots.acf()                            # Autocorrelation
```

### Get Contributions
```python
contributions = ml.get_contributions()
for name, contrib in contributions.items():
    print(f"{name}: mean={contrib.mean():.2f}")
```

### Step and Impulse Response
```python
step = ml.get_step_response('recharge')    # Step response
block = ml.get_block_response('recharge')  # Impulse response
```

### Export and Load
```python
ml.to_json('model.pas')                    # Save model
ml_loaded = ps.io.load('model.pas')        # Load model

sim = ml.simulate()
sim.to_csv('simulation.csv')               # Export results
```

## Model Statistics

| Statistic | Description | Good Value |
|-----------|-------------|------------|
| EVP | Explained variance percentage | >70% |
| RMSE | Root mean square error | Low (context-dependent) |
| AIC | Akaike Information Criterion | Lower = better |
| BIC | Bayesian Information Criterion | Lower = better |

## Common Patterns

### Compare Response Functions
```python
for rfunc in [ps.Gamma(), ps.Exponential(), ps.Hantush()]:
    ml = ps.Model(head)
    ml.add_stressmodel(ps.RechargeModel(precip, evap, rfunc=rfunc, name='r'))
    ml.solve(report=False)
    print(f"{rfunc.name}: EVP={ml.stats.evp():.1f}%, AIC={ml.stats.aic():.1f}")
```

### Forecast Future Levels
```python
ml.solve()
forecast = ml.simulate(tmin='2024-01-01', tmax='2025-12-31')
ml.plot(tmax='2025-12-31')
```

### River or Custom Stress
```python
river = pd.read_csv('river_stage.csv', index_col=0, parse_dates=True).squeeze()
sm = ps.StressModel(river, rfunc=ps.Exponential(), name='river',
                    settings='waterlevel')
ml.add_stressmodel(sm)
```

## Tips

1. **Start simple** - Add stresses incrementally
2. **Check residuals** - Should be white noise (use `ml.plots.diagnostics()`)
3. **Compare response functions** - Use AIC/BIC to select best model
4. **Use daily data** - Pastas works best with daily time series
5. **Normalize units** - Precipitation in mm/day, head in meters

## Common Issues

| Issue | Solution |
|-------|----------|
| Poor fit (low EVP) | Try different response functions |
| Residual autocorrelation | Add noise model: `ml.solve(noise=True)` |
| Unstable parameters | Set parameter bounds or fix values |
| Missing stress data | Interpolate or use `fillna()` before modeling |

## References

- **[Stress Models](references/stress_models.md)** - Available stress model types
- **[Response Functions](references/response_functions.md)** - Response function selection

## Scripts

- **[scripts/groundwater_model.py](scripts/groundwater_model.py)** - Complete groundwater modeling workflow
