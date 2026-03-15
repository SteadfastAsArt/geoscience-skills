# GNNWR Diagnostics Reference

## DIAGNOSIS Object

Access via `model._test_diagnosis` after training.

### Always Available

```python
diag = model._test_diagnosis
r2 = diag.R2()       # R-squared (coefficient of determination)
rmse = diag.RMSE()   # Root Mean Square Error
```

### Full Mode (lite=False, auto for N < 10k)

```python
aic = diag.AIC()          # Akaike Information Criterion
aicc = diag.AICc()        # Corrected AIC (for small samples)
f1 = diag.F1_Global()     # GNNWR vs OLS: is spatial model significantly better?
f2 = diag.F2_Global()     # Spatial weight significance: do weights matter?
f3_dict1, f3_dict2 = diag.F3_Local()  # Per-variable spatial non-stationarity
```

### lite Mode

When `N > 10k`, DIAGNOSIS auto-sets `lite=True`:
- Only R² and RMSE available
- Hat matrix not computed (O(n²) memory)
- To force full diagnostics: set `lite=False` explicitly (requires enough RAM)

## F-test Interpretation

| Test | Null Hypothesis | If Significant |
|------|----------------|----------------|
| F1_Global | GNNWR = OLS (no spatial effect) | GNNWR significantly better than OLS |
| F2_Global | Spatial weights = uniform | Geographic weighting adds value |
| F3_Local | Variable coefficient is constant across space | Variable shows spatial non-stationarity |

### F3_Local Usage

```python
f3_dict1, f3_dict2 = diag.F3_Local()
# f3_dict1: F-statistics per variable
# f3_dict2: p-values per variable

for var, pval in f3_dict2.items():
    status = "spatially varying" if pval < 0.05 else "spatially constant"
    print(f"{var}: p={pval:.4f} → {status}")
```

## Model Summary

```python
# Quick summary (prints to console)
print(model.result())
# Returns: R², AIC, RMSE, and F-test results in formatted table

# Full result DataFrame
result = model.reg_result(only_return=True)
# Columns: coef_x1, coef_x2, ..., Pred_y, denormalized_pred_result
```

## Residual Analysis

```python
result = model.reg_result(only_return=True)
result["residual"] = result["denormalized_pred_result"] - result[y_column]

# Check for spatial autocorrelation in residuals
# If residuals cluster spatially → model may miss a spatial pattern
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 8))
sc = ax.scatter(
    result["lon"], result["lat"],
    c=result["residual"], cmap="coolwarm", s=5,
    vmin=-result["residual"].abs().quantile(0.95),
    vmax=result["residual"].abs().quantile(0.95)
)
ax.set_title("Spatial Residual Distribution")
plt.colorbar(sc, ax=ax, label="Residual")
plt.savefig("residuals_map.png", dpi=300, bbox_inches="tight")
```

## Prediction vs Observed

```python
fig, ax = plt.subplots(figsize=(8, 8))
ax.scatter(result[y_column], result["denormalized_pred_result"], s=3, alpha=0.5)
lim = [result[y_column].min(), result[y_column].max()]
ax.plot(lim, lim, "r--", linewidth=2, label="1:1 line")
ax.set_xlabel("Observed"); ax.set_ylabel("Predicted")
ax.set_title(f"GNNWR: R²={model._test_diagnosis.R2().item():.4f}")
ax.legend()
plt.savefig("pred_vs_obs.png", dpi=300, bbox_inches="tight")
```
