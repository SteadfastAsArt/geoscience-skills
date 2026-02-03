---
description: Guide spatial data gridding from exploration through variography and interpolation to validation
---

# Spatial Data Gridding Workflow

Guide the user through spatial data gridding and interpolation. Determine the appropriate skill chain based on data type and gridding method.

## Decision Tree

1. **What gridding method fits your data?**
   - Deterministic (splines, linear, cubic) → Use `verde` skill
   - Geostatistical kriging with GSLIB backend → Use `geostatspy` skill
   - Geostatistical with sklearn-compatible API → Use `scikit-gstat` skill
   - Gravity or magnetic potential field data → Use `harmonica` skill

2. **Which tool best fits your workflow?**
   - Verde: Green's functions gridding, cross-validation, sklearn-style API
   - GeostatsPy: GSLIB-based kriging, simulation, traditional geostatistics
   - scikit-gstat: variogram modelling, sklearn integration, modern Python API
   - Harmonica: equivalent sources for gravity/magnetics, terrain corrections

3. **Visualization needs?**
   - 2D gridded maps → matplotlib (built-in)
   - 3D surfaces and point clouds → Use `pyvista` skill

## Skill Chain

```text
verde (deterministic gridding)        → pyvista (3D viz)
geostatspy (GSLIB kriging/simulation) → pyvista (3D viz)
scikit-gstat (variograms + kriging)   → pyvista (3D viz)
harmonica (potential field gridding)   → pyvista (3D viz)
```

## Step Prompts

For each step, invoke the relevant domain skill and follow its guidance.

### Step 1: Data Exploration
- Load scattered point data with coordinates and values
- Check for spatial clustering, outliers, and trends
- Compute basic statistics and visualize point distribution

### Step 2: Variography (Geostatistical Methods)
- Compute experimental variogram (omnidirectional and directional)
- Fit theoretical variogram model (spherical, exponential, Gaussian)
- Identify nugget, sill, and range parameters

### Step 3: Gridding / Interpolation
- Define output grid extent and resolution
- Verde: fit spline or linear gridder with cross-validation
- GeostatsPy/scikit-gstat: run kriging with fitted variogram
- Harmonica: fit equivalent sources for potential field data

### Step 4: Validation
- Cross-validation with k-fold or leave-one-out
- Compute RMSE, MAE, and R-squared metrics
- Check residuals for spatial bias

### Step 5: Visualization
- Plot gridded surface as contour or image map
- Overlay original data points for comparison
- Render 3D surface with pyvista if needed

$ARGUMENTS
