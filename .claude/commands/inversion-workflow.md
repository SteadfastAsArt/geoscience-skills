---
description: Guide geophysical inversion from data loading through mesh building and inversion to visualization
---

# Geophysical Inversion Workflow

Guide the user through a geophysical inversion pipeline. Determine the appropriate skill chain based on survey type and inversion goals.

## Decision Tree

1. **What survey type?**
   - Electrical Resistivity Tomography (ERT) → Use `pygimli` or `simpeg` skill
   - Magnetics / Gravity → Use `simpeg` skill with `harmonica` for processing
   - Electromagnetic (EM), IP, or multi-physics → Use `simpeg` skill
   - Seismic Refraction Tomography (SRT) → Use `pygimli` skill

2. **Which framework fits your problem?**
   - Multi-physics, large-scale, flexible regularization → Use `simpeg` skill
   - Near-surface ERT/SRT, streamlined API → Use `pygimli` skill

3. **Post-processing and visualization?**
   - Grid scattered inversion results → Use `verde` skill
   - 3D model rendering → Use `pyvista` skill

## Skill Chain

```text
simpeg (multi-physics inversion)   → verde (gridding results) → pyvista (3D viz)
pygimli (ERT/SRT inversion)        → verde (gridding results) → pyvista (3D viz)
harmonica (gravity/mag processing) → simpeg (inversion)
```

## Step Prompts

For each step, invoke the relevant domain skill and follow its guidance.

### Step 1: Data Loading
- Load survey data (electrode positions, observations, uncertainties)
- Assign data uncertainties (absolute or percentage)
- Inspect data quality and remove outliers

### Step 2: Mesh Construction
- Build appropriate mesh (tensor, tree, or unstructured)
- Refine mesh near electrodes or survey points
- Set mesh padding for boundary conditions

### Step 3: Forward Modelling
- Define starting model and physical property mapping
- Run forward simulation to verify data fit
- Compare predicted vs observed data

### Step 4: Inversion
- Configure objective function and regularization
- Set convergence criteria (target misfit, max iterations)
- Run inversion and monitor convergence

### Step 5: Post-Processing and Visualization
- Extract recovered model on mesh
- Grid results to regular grid with verde if needed
- Render 3D inversion results with pyvista
- Evaluate depth of investigation and model reliability

$ARGUMENTS
