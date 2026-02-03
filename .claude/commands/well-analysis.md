---
description: Guide well log analysis from data loading through petrophysics to lithology and visualization
---

# Well Log Analysis Workflow

Guide the user through a well log analysis pipeline. Determine the appropriate skill chain based on their data format and analysis goals.

## Decision Tree

1. **What format is the well data?**
   - LAS (.las) → Use `lasio` skill for loading
   - DLIS (.dlis) → Use `dlisio` skill for loading
   - CSV / already loaded → Skip to processing with `welly`

2. **What analysis is needed?**
   - Multi-well management, curve QC → Use `welly` skill
   - Petrophysics (porosity, saturation, cutoffs) → Use `petropy` skill
   - Lithology / stratigraphy intervals → Use `striplog` skill

3. **Visualization needs?**
   - Log plots, cross-plots → matplotlib via `welly`
   - 3D wellbore trajectories → Use `pyvista` skill

## Skill Chain

```text
lasio/dlisio (load) → welly (manage/QC) → petropy (petrophysics) → striplog (lithology)
                                                                  ↘ pyvista (3D viz)
```

## Step Prompts

For each step, invoke the relevant domain skill and follow its guidance.

### Step 1: Data Loading
- Load well log files and inspect available curves
- Check header metadata (well name, depth units, null values)
- Validate depth range and sampling interval

### Step 2: Quality Control
- Identify missing or null values in key curves
- Check curve mnemonics and units consistency
- Merge or splice curves from multiple runs if needed

### Step 3: Petrophysics
- Compute shale volume (Vsh) from GR or SP
- Calculate porosity (density, neutron, sonic methods)
- Estimate water saturation (Archie or dual-water)
- Apply net pay cutoffs

### Step 4: Lithology Classification
- Define lithology intervals from log response
- Build striplog from interpreted zones
- Correlate across multiple wells

### Step 5: Visualization
- Log plots with tracks (GR, resistivity, porosity, saturation)
- Cross-plots for mineral identification
- 3D wellbore rendering with property logs

$ARGUMENTS
