---
name: gnnwr
description: |
  Spatial and spatiotemporal regression with GNNWR (Geographically Neural Network
  Weighted Regression). Use when Claude needs to: (1) Build spatially varying coefficient
  regression models, (2) Analyze geographic non-stationarity in spatial data,
  (3) Generate spatial coefficient maps for publication, (4) Run spatiotemporal
  regression with GTNNWR, (5) Scale geographically weighted regression to large
  datasets (N > 10k) with KNN mode, (6) Diagnose spatial model performance with
  F-tests, AIC, and residual maps.
version: 1.0.0
author: Geoscience Skills
license: MIT
tags: [Spatial Regression, GNNWR, GTNNWR, GWR, Non-Stationarity, Coefficient Mapping, Spatial Analysis, Geographic Weighting]
dependencies: [gnnwr>=0.1.0, pandas, torch]
complements: [verde, geostatspy, scikit-gstat, pyvista, xarray]
workflow_role: analysis
---

# GNNWR - Geographically Neural Network Weighted Regression

## Quick Reference

```python
from gnnwr import models, datasets, utils
import pandas as pd

data = pd.read_csv("data.csv")

train, val, test = datasets.init_dataset(
    data=data, test_ratio=0.2, valid_ratio=0.1,
    x_column=["x1", "x2", "x3"], y_column=["y"],
    spatial_column=["lon", "lat"],  # REQUIRED: geographic coords
    batch_size=32, process_fn="minmax_scale"
)

model = models.GNNWR(train, val, test, use_gpu=True, optimizer="Adam", start_lr=0.01)
model.run(max_epoch=200, early_stop=30)

result = model.reg_result(only_return=True)  # DataFrame: coef_x1, coef_x2, ..., Pred_y
print(model.result())                         # R², AIC, RMSE, F-tests summary
```

### Spatiotemporal (GTNNWR)

```python
train, val, test = datasets.init_dataset(
    data=data, ...,
    spatial_column=["lon", "lat"],
    temp_column=["year", "month"],  # add temporal coords
    use_model="gtnnwr"
)
model = models.GTNNWR(train, val, test, use_gpu=True)
```

### Large-Scale (N > 10k) — KNN Mode

```python
train, val, test = datasets.init_dataset(
    data=data, ..., knn_k=500  # only k nearest neighbor distances
)
# Memory: N=100k full=55GB → knn_k=2000 only 763MB
```

## Key Classes

| Class | Purpose |
|-------|---------|
| `models.GNNWR` | Spatial regression with neural network geographic weighting |
| `models.GTNNWR` | Spatiotemporal regression with temporal + spatial weighting |
| `datasets.init_dataset` | Data splitting, normalization, distance matrix construction |
| `utils.Visualize` | Built-in folium interactive maps for coefficients and predictions |

## Essential Operations

### init_dataset Parameters

| Parameter | Default | Notes |
|-----------|---------|-------|
| `knn_k` | None | KNN sparse distance; None=full matrix |
| `process_fn` | "minmax_scale" | or "standard_scale" |
| `spatial_fun` | BasicDistance | Euclidean; or ManhattanDistance |
| `Reference` | None | "train", "train_val", or custom DataFrame |
| `sample_seed` | 42 | Reproducibility |

### Model Hyperparameters

| Parameter | Recommended | Notes |
|-----------|-------------|-------|
| `optimizer` | "Adam" | Also: SGD, AdamW, Adagrad, RMSprop |
| `start_lr` | 0.01–0.1 | Critical tuning point |
| `drop_out` | 0.2 | 0.0–0.5 |
| `dense_layers` | None (auto) | Auto: power-of-2 sequence from input_dim to n_coef |
| `early_stop` | 20–50 | Patience; -1=disabled |
| `batch_norm` | True | Stabilizes training |
| `use_ols` | True | OLS-initialized output layer |

### Diagnostics

```python
diag = model._test_diagnosis
diag.R2()           # always available
diag.RMSE()         # always available
diag.AIC()          # needs lite=False (auto for N<10k)
diag.AICc()         # corrected AIC
diag.F1_Global()    # GNNWR vs OLS significance
diag.F2_Global()    # spatial weight significance
diag.F3_Local()     # per-variable significance → (dict1, dict2)
```

`lite=True` (auto when N>10k): only R²/RMSE; Hat-matrix diagnostics skipped.

## Visualization Patterns

### Folium Interactive Maps (built-in)

```python
viz = utils.Visualize(model, lon_lat_columns=["lon", "lat"], zoom=5)
m1 = viz.display_dataset(name="all", y_column="y")
m1.save("dataset_map.html")

for col in [c for c in result.columns if c.startswith("coef_")]:
    m = viz.coefs_heatmap(data_column=col, steps=20)
    m.save(f"map_{col}.html")
```

### Matplotlib Static Maps (publication-ready)

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 3, figsize=(18, 12))
coef_cols = [c for c in result.columns if c.startswith("coef_")]

for ax, col in zip(axes.flat, coef_cols):
    sc = ax.scatter(
        result["lon"], result["lat"],
        c=result[col], cmap="RdYlBu_r", s=5, alpha=0.8,
        vmin=result[col].quantile(0.02), vmax=result[col].quantile(0.98)
    )
    ax.set_title(col.replace("coef_", "β_"), fontsize=14)
    plt.colorbar(sc, ax=ax, shrink=0.8)

plt.suptitle("Spatially Varying Coefficients (GNNWR)", fontsize=16)
plt.tight_layout()
plt.savefig("coefficients_map.png", dpi=300, bbox_inches="tight")
```

### GeoPandas + Contextily (with basemap)

```python
import geopandas as gpd
import contextily as ctx

gdf = gpd.GeoDataFrame(result, geometry=gpd.points_from_xy(result.lon, result.lat), crs="EPSG:4326")
gdf_web = gdf.to_crs(epsg=3857)

fig, ax = plt.subplots(figsize=(12, 10))
gdf_web.plot(column="coef_x1", ax=ax, cmap="RdYlBu_r", legend=True,
             markersize=5, alpha=0.7, legend_kwds={"shrink": 0.6})
ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
ax.set_title("β_x1 Spatial Variation")
ax.set_axis_off()
plt.savefig("coef_basemap.png", dpi=300, bbox_inches="tight")
```

## When to Use vs Alternatives

| Use Case | Tool | Why |
|----------|------|-----|
| Spatially varying coefficients (neural net) | **GNNWR** | Non-linear weighting, scalable, coefficient maps |
| Classical geographically weighted regression | **mgwr / GWR4** | Traditional bandwidth-based, well-established theory |
| Spatial interpolation (no covariates) | **verde / scikit-gstat** | Gridding / kriging without regression |
| Global regression baseline | **statsmodels / scikit-learn** | No spatial non-stationarity assumed |
| Spatiotemporal varying coefficients | **GTNNWR** | GNNWR extended with temporal dimension |
| Large-scale spatial regression (N > 100k) | **GNNWR + knn_k** | Sparse distance matrix, O(n·k²) diagnostics |
| Geostatistical simulation | **geostatspy / SGeMS** | Stochastic realizations, uncertainty quantification |

**Choose GNNWR when**: You need spatially varying regression coefficients with neural
network-based geographic weighting, especially for large datasets where classical GWR
is computationally infeasible.

**Choose classical GWR when**: You need well-established inferential statistics,
bandwidth-based weighting, and simpler model interpretation.

**Choose verde/kriging when**: You need spatial interpolation without explanatory
variables — pure spatial prediction from observed values.

## Common Workflows

### Spatial Regression Analysis
- [ ] EDA: Check spatial distribution, feature correlations, OLS baseline
- [ ] Data split: `init_dataset` with appropriate ratios and `sample_seed=42`
- [ ] Train: Start with defaults, tune `start_lr` and `early_stop`
- [ ] Diagnose: R², RMSE, F1 (GNNWR vs OLS), F2 (spatial weight significance)
- [ ] Visualize: Coefficient maps, residual spatial distribution, pred vs obs
- [ ] Interpret: Where do coefficients vary most? Which variables show strongest non-stationarity? (F3_Local)
- [ ] Report: Model summary table + coefficient maps + diagnostic statistics

## Common Issues

| Issue | Solution |
|-------|----------|
| Model degenerates to global regression | Forgot `spatial_column` — always pass it |
| OOM on distance matrix | N > 10k without `knn_k`; use `knn_k=500–2000` |
| Loss explodes during training | `start_lr` too high; start with 0.01 |
| Overfitting | No `early_stop`; always set 20–50 |
| Coefficients on wrong scale | Use `reg_result()` for denormalized predictions |
| GTNNWR behaves like GNNWR | Missing `temp_column`; silently falls back |

## References

- **[Diagnostics](references/diagnostics.md)** — DIAGNOSIS methods, F-tests, residual analysis
- **[Visualization](references/visualization.md)** — Detailed visualization patterns and publication figures
