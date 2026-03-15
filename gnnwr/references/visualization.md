# GNNWR Visualization Reference

## Built-in Folium Maps

```python
from gnnwr import utils

viz = utils.Visualize(model, lon_lat_columns=["lon", "lat"], zoom=5)

# Dataset distribution
m1 = viz.display_dataset(name="all", y_column="y")
m1.save("dataset_map.html")

# Coefficient spatial variation — one map per variable
result = model.reg_result(only_return=True)
for col in [c for c in result.columns if c.startswith("coef_")]:
    m = viz.coefs_heatmap(data_column=col, steps=20)
    m.save(f"map_{col}.html")

# Custom dot map for any DataFrame column
m3 = viz.dot_map(result, "lon", "lat", "denormalized_pred_result", zoom=5)
m3.save("prediction_map.html")
```

## Matplotlib Multi-Panel Coefficient Maps

```python
import matplotlib.pyplot as plt
import numpy as np

result = model.reg_result(only_return=True)
coef_cols = [c for c in result.columns if c.startswith("coef_")]
n_coefs = len(coef_cols)
ncols = min(3, n_coefs)
nrows = (n_coefs + ncols - 1) // ncols

fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 5 * nrows))
if n_coefs == 1:
    axes = [axes]
else:
    axes = axes.flat

for ax, col in zip(axes, coef_cols):
    sc = ax.scatter(
        result["lon"], result["lat"],
        c=result[col], cmap="RdYlBu_r", s=5, alpha=0.8,
        vmin=result[col].quantile(0.02), vmax=result[col].quantile(0.98)
    )
    ax.set_title(col.replace("coef_", "β_"), fontsize=14)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    plt.colorbar(sc, ax=ax, shrink=0.8)

# Hide unused axes
for ax in list(axes)[n_coefs:]:
    ax.set_visible(False)

plt.suptitle("Spatially Varying Coefficients (GNNWR)", fontsize=16)
plt.tight_layout()
plt.savefig("coefficients_map.png", dpi=300, bbox_inches="tight")
```

## GeoPandas + Contextily Basemap

Requires: `pip install geopandas contextily`

```python
import geopandas as gpd
import contextily as ctx
import matplotlib.pyplot as plt

gdf = gpd.GeoDataFrame(
    result,
    geometry=gpd.points_from_xy(result.lon, result.lat),
    crs="EPSG:4326"
)
gdf_web = gdf.to_crs(epsg=3857)

fig, ax = plt.subplots(figsize=(12, 10))
gdf_web.plot(
    column="coef_x1", ax=ax, cmap="RdYlBu_r", legend=True,
    markersize=5, alpha=0.7, legend_kwds={"shrink": 0.6}
)
ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)
ax.set_title("β_x1 Spatial Variation")
ax.set_axis_off()
plt.savefig("coef_basemap.png", dpi=300, bbox_inches="tight")
```

## Colormap and Outlier Handling

For coefficient maps, clip extreme values to avoid color scale distortion:

```python
# Clip at 2nd and 98th percentile
vmin = result[col].quantile(0.02)
vmax = result[col].quantile(0.98)

# Use diverging colormap centered at zero for coefficients that cross zero
import matplotlib.colors as mcolors
if vmin < 0 < vmax:
    norm = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=0, vmax=vmax)
    sc = ax.scatter(..., norm=norm, cmap="RdBu_r")
```

## Publication Figure Checklist

- [ ] Use `RdYlBu_r` or `RdBu_r` colormap for coefficient maps
- [ ] Clip outliers at 2nd/98th percentile
- [ ] Include colorbar with coefficient label
- [ ] Set `dpi=300` and `bbox_inches="tight"` for saving
- [ ] Add basemap with GeoPandas + Contextily for geographic context
- [ ] Use `coolwarm` colormap for residuals (centered at 0)
- [ ] Include 1:1 line in prediction vs observed scatter
- [ ] Report R² on prediction scatter plot title
