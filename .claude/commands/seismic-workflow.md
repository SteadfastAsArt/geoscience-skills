---
description: Guide seismic data analysis from loading through rock physics to visualization
---

# Seismic Data Analysis Workflow

Guide the user through a seismic data analysis pipeline. Determine the appropriate skill chain based on their data and goals.

## Decision Tree

1. **What format is the data?**
   - SEG-Y (.sgy, .segy) → Use `segyio` skill for loading
   - MiniSEED / SAC / other seismological formats → Use `obspy` skill for loading
   - Already loaded as numpy array → Skip to processing

2. **What processing is needed?**
   - Filtering, detrending, spectral analysis → Use `obspy` skill
   - Rock physics (AVO, fluid substitution, elastic moduli) → Use `bruges` skill
   - Surface wave dispersion → Use `disba` skill

3. **Visualization needs?**
   - 2D section / wiggle plots → matplotlib (built-in)
   - 3D seismic volume rendering → Use `pyvista` skill

## Skill Chain

```text
segyio (load SEG-Y) → obspy (signal processing) → bruges (rock physics) → pyvista (3D viz)
                                                  ↘ disba (dispersion)
```

## Step Prompts

For each step, invoke the relevant domain skill and follow its guidance.

### Step 1: Data Loading
- Load seismic data and inspect geometry
- Check trace headers, inline/crossline ranges
- Validate sample rate and trace length

### Step 2: Quality Control
- Check for dead traces and amplitude anomalies
- Validate geometry consistency
- Review amplitude statistics

### Step 3: Processing
- Apply filters (bandpass, notch) as needed
- Detrend and remove DC offset
- Apply gain corrections if needed

### Step 4: Analysis
- Rock physics: AVO analysis, fluid substitution
- Surface waves: compute dispersion curves
- Attributes: amplitude, phase, frequency

### Step 5: Visualization
- 2D: seismic sections, amplitude maps
- 3D: volume rendering, horizon surfaces

$ARGUMENTS
