# MT Plotting Reference

## Table of Contents
- [PlotMTResponse](#plotmtresponse)
- [PlotPhaseTensor](#plotphasetensor)
- [PlotPseudoSection](#plotpseudosection)
- [PlotStrike](#plotstrike)
- [PlotTipper](#plottipper)
- [Common Parameters](#common-parameters)
- [Color Maps](#color-maps)

## PlotMTResponse

Plot apparent resistivity and phase curves for MT data.

### Basic Usage
```python
from mtpy import MT
from mtpy.imaging import PlotMTResponse

mt = MT('station.edi')
plot = PlotMTResponse(mt)
plot.plot()
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| plot_tipper | bool | True | Include tipper arrows |
| plot_pt | bool | False | Include phase tensor ellipse |
| plot_num | int | 1 | Figure number |
| res_limits | tuple | None | (min, max) resistivity limits |
| phase_limits | tuple | (0, 90) | (min, max) phase limits |

### Customization
```python
plot = PlotMTResponse(
    mt,
    plot_tipper=True,
    res_limits=(1, 1000),
    phase_limits=(0, 90),
    fig_size=(8, 10)
)
plot.plot()

# Access figure for further customization
fig = plot.fig
ax_rho = plot.ax_res
ax_phase = plot.ax_phase
```

### Plot Components

| Component | Description |
|-----------|-------------|
| xy (TE) | Red circles - Ex/By response |
| yx (TM) | Blue squares - Ey/Bx response |
| xx, yy | Gray - Diagonal components (often noisy) |

## PlotPhaseTensor

Visualize phase tensor ellipses.

### Basic Usage
```python
from mtpy import MT
from mtpy.imaging import PlotPhaseTensor

mt = MT('station.edi')
pt = PlotPhaseTensor(mt)
pt.plot()
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| ellipse_colorby | str | 'skew' | Color by: 'skew', 'phimin', 'phimax', 'ellipticity' |
| ellipse_range | tuple | (-10, 10) | Color scale range |
| ellipse_cmap | str | 'mt_seg_bl2wh2rd' | Colormap name |
| ellipse_size | float | 0.05 | Ellipse scaling factor |

### Coloring Options

| colorby | Range | Interpretation |
|---------|-------|----------------|
| 'skew' | (-10, 10) | 3D indicator (degrees) |
| 'phimin' | (0, 90) | Minimum phase (degrees) |
| 'phimax' | (0, 90) | Maximum phase (degrees) |
| 'ellipticity' | (0, 1) | Shape: 0=circle, 1=line |

### Example
```python
pt = PlotPhaseTensor(
    mt,
    ellipse_colorby='skew',
    ellipse_range=(-9, 9),
    ellipse_cmap='mt_seg_bl2wh2rd'
)
pt.plot()
```

## PlotPseudoSection

Create pseudosections for profile data.

### Basic Usage
```python
from mtpy import MTCollection
from mtpy.imaging import PlotPseudoSection

mc = MTCollection()
mc.from_edis('profile/*.edi')

ps = PlotPseudoSection(mc)
ps.plot()
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| plot_type | str | 'apparent_resistivity' | 'apparent_resistivity', 'phase', 'tipper' |
| mode | str | 'det' | 'te', 'tm', 'det' (determinant) |
| period_limits | tuple | None | (min, max) period range |
| res_limits | tuple | None | (min, max) resistivity limits |
| phase_limits | tuple | (0, 90) | (min, max) phase limits |

### Plot Types

| plot_type | Description |
|-----------|-------------|
| 'apparent_resistivity' | Resistivity pseudosection |
| 'phase' | Phase pseudosection |
| 'tipper_real' | Real tipper magnitude |
| 'tipper_imag' | Imaginary tipper magnitude |

### Mode Options

| mode | Description |
|------|-------------|
| 'te' | TE mode (Zxy) |
| 'tm' | TM mode (Zyx) |
| 'det' | Determinant average |
| 'both' | TE and TM side by side |

### Example
```python
ps = PlotPseudoSection(
    mc,
    plot_type='apparent_resistivity',
    mode='det',
    res_limits=(1, 10000),
    period_limits=(0.001, 1000),
    fig_size=(12, 6)
)
ps.plot()
```

## PlotStrike

Analyze strike direction vs period.

### Basic Usage
```python
from mtpy import MT
from mtpy.imaging import PlotStrike

mt = MT('station.edi')
strike = PlotStrike(mt)
strike.plot()
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| plot_type | str | 'rose' | 'rose' or 'scatter' |
| fold | bool | True | Fold 180-degree ambiguity |
| period_limits | tuple | None | (min, max) period range |

### Strike Methods

| Method | Description |
|--------|-------------|
| Impedance | From Zxx, Zxy, Zyx, Zyy |
| Phase tensor | From PT principal axes |
| Tipper | Perpendicular to induction arrows |

### Example
```python
strike = PlotStrike(
    mt,
    plot_type='rose',
    fold=True,
    period_limits=(1, 100)
)
strike.plot()
```

## PlotTipper

Visualize magnetic transfer function.

### Basic Usage
```python
from mtpy import MT
from mtpy.imaging import PlotTipper

mt = MT('station.edi')
if mt.has_tipper:
    tipper = PlotTipper(mt)
    tipper.plot()
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| arrow_size | float | 1.0 | Arrow scaling factor |
| arrow_head_length | float | 0.1 | Arrow head length |
| arrow_head_width | float | 0.05 | Arrow head width |
| real_color | str | 'k' | Real tipper color |
| imag_color | str | 'b' | Imaginary tipper color |

### Tipper Convention
- Real arrows point toward conductor
- Length proportional to Hz/Hh ratio
- Useful for locating lateral conductivity contrasts

## Common Parameters

### Figure Size
```python
plot = PlotMTResponse(mt, fig_size=(10, 12))
```

### Saving Figures
```python
plot = PlotMTResponse(mt)
plot.plot()
plot.save_figure('output.png', dpi=300)
```

### Font and Label Sizes
```python
plot = PlotMTResponse(
    mt,
    font_size=12,
    label_font_size=10,
    title_font_size=14
)
```

## Color Maps

### MT-Specific Colormaps

| Name | Description | Use |
|------|-------------|-----|
| mt_seg_bl2wh2rd | Blue-white-red | Skew, symmetric data |
| mt_rd2wh2bl | Red-white-blue | Phase tensor |
| mt_wh2bl | White to blue | Resistivity |
| mt_rd2gr2bl | Red-green-blue | Phase |

### Using Custom Colormaps
```python
import matplotlib.pyplot as plt

ps = PlotPseudoSection(
    mc,
    cmap=plt.cm.viridis
)
```

## Multi-Station Plots

### Map View with Phase Tensors
```python
from mtpy import MTCollection
from mtpy.imaging import PlotPhaseTensorMaps

mc = MTCollection()
mc.from_edis('survey/*.edi')

# Plot at specific period
ptm = PlotPhaseTensorMaps(mc, plot_period=10.0)
ptm.plot()
```

### Profile with Multiple Stations
```python
from mtpy.imaging import PlotMultipleResponses

plots = PlotMultipleResponses(mc)
plots.plot()  # Grid of all station responses
```

## Saving and Export

### Figure Formats
```python
# PNG (raster)
plot.save_figure('figure.png', dpi=300)

# PDF (vector)
plot.save_figure('figure.pdf')

# SVG (vector, editable)
plot.save_figure('figure.svg')
```

### Get Matplotlib Objects
```python
plot = PlotMTResponse(mt)
plot.plot()

# Access underlying matplotlib objects
fig = plot.fig
axes = plot.ax_list

# Further customization
axes[0].set_title('Custom Title')
fig.savefig('custom.png')
```
