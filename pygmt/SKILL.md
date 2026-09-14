---
name: pygmt
description: Make geographic maps and process geospatial grids with PyGMT and GMT, including projection, regions, grid registration and vector/raster export. Use for GMT cartography and map-ready scientific data; check the separate GMT shared library before plotting.
license: MIT
metadata:
  version: "1.0.0"
  author: Geoscience Skills
  skill_type: domain
  tags: '["Cartography", "GMT", "Maps", "Grids"]'
  dependencies: '["pygmt==0.19.0"]'
  complements: '["xarray", "verde", "boule"]'
  workflow_role: visualization
---

# PyGMT

Produce a map whose projection, coordinate units and data coverage are explicit.
PyGMT 0.19 requires Python 3.12+ and GMT 6.5+; the Python package alone does not
install the GMT shared library. Use the documented isolated conda-forge setup
with Ghostscript when exporting figures. Record PyGMT and GMT versions separately.

## Inputs and map design

Establish geographic versus projected coordinates, horizontal CRS, longitude
convention and vertical datum. Choose region `[west, east, south, north]` and
projection deliberately. Decide pixel versus gridline registration and verify
coordinate ordering, spacing and NaN masks before gridding or image display.
Do not reinterpret projected metres as longitude/latitude degrees.

## Offline map with synthetic locations

This example requires `output_pdf` to name a new output file. It uses no remote
relief or coastline dataset; the three locations are illustrative, not a survey.

```python
# example: synthetic-map
import pygmt

figure = pygmt.Figure()
figure.basemap(region=[5, 10, 44, 48], projection="M10c",
               frame=["af", "+tSynthetic locations"])
figure.plot(x=[6, 7.5, 9], y=[45, 46, 47], style="c0.18c",
            fill="navy", pen="0.4p,black")
figure.savefig(output_pdf)
```

For actual gridded data, inspect spacing/registration before `grdimage`; choose
interpolation and color limits appropriate to units and scientific comparison.
Remote datasets such as Earth relief require documented resolution, cache,
license and download size. A cropped map does not prove the source data only
cover that region.

## Validate and deliver

Reopen the exported file, check bounds, labels, orientation, missing-data areas
and color scale. Compare control-point coordinates with the input, and sample
known grid nodes through GMT when grid operations are involved. Provide the
source data references, script, CRS/projection and export settings with the map.

See [installation](https://www.pygmt.org/latest/install.html),
[tutorials](https://www.pygmt.org/latest/tutorials/index.html) and
[GMT grid conventions](https://docs.generic-mapping-tools.org/latest/cookbook/file-formats.html).
