---
description: Guide 3D geological model building from data preparation through computation to visualization
---

# 3D Geological Modelling Workflow

Guide the user through building a 3D geological model. Determine the appropriate skill chain based on input data and modelling goals.

## Decision Tree

1. **What input data do you have?**
   - GIS layers (shapefiles, rasters, DEMs) → Use `gemgis` skill for data preparation
   - Borehole data / orientations → Load directly into modelling engine
   - Pre-processed surfaces → Skip to model setup

2. **Which modelling engine fits your problem?**
   - Complex faulted geology, implicit surfaces, GPU support → Use `gempy` skill
   - Fold-dominated structures, lightweight, tetrahedral meshes → Use `loopstructural` skill

3. **Visualization needs?**
   - Interactive 3D model rendering → Use `pyvista` skill
   - Cross-sections and map views → matplotlib (built-in)

## Skill Chain

```text
gemgis (data prep from GIS) → gempy (implicit modelling, GPU)       → pyvista (3D viz)
                             → loopstructural (fold-focused, light)  → pyvista (3D viz)
```

## Step Prompts

For each step, invoke the relevant domain skill and follow its guidance.

### Step 1: Data Preparation
- Extract surface points and orientations from GIS data
- Reproject coordinates to a consistent CRS
- Prepare topography and stratigraphic contact data

### Step 2: Model Setup
- Define model extent and resolution
- Assign stratigraphic pile and fault network
- Set surface points and orientation gradients

### Step 3: Compute Model
- GemPy: run interpolation with dual kriging, configure GPU if available
- LoopStructural: build model with fold constraints, set solver options
- Check for geological consistency (layer ordering, fault offsets)

### Step 4: Validate
- Compare model surfaces against input data
- Check cross-sections for geological plausibility
- Evaluate model uncertainty if supported

### Step 5: Visualization
- Render 3D block model and surfaces interactively
- Extract cross-sections at key locations
- Export model to common formats (VTK, GOCAD)

$ARGUMENTS
