# Conditional extraction

## DEM profile

`sample_from_raster` is not a GemGIS 1.1.9 API. Use
`sample_from_rasterio(raster, point_x, point_y)` with an open Rasterio dataset.
This function takes a 2D LineString in the same projected metre CRS as the DEM;
Z must already be in the intended vertical units/datum. It rejects exterior or
masked samples and retains profile chainage in metres.

```python
import gemgis as gg
from rasterio.transform import rowcol
import numpy as np

def sample_profile(line, dem, count=101):
    if not isinstance(count, int) or count < 2 or line.length <= 0:
        raise ValueError('Require a nonzero profile and at least two samples')
    distance = np.linspace(0., line.length, count)
    points = [line.interpolate(d) for d in distance]
    x = np.array([p.x for p in points])
    y = np.array([p.y for p in points])
    row, col = np.asarray(rowcol(dem.transform, x, y))
    if np.any((row < 0) | (row >= dem.height) | (col < 0) | (col >= dem.width)):
        raise ValueError('Profile leaves the DEM')
    mask = np.ma.vstack(list(dem.sample(zip(x, y), indexes=1, masked=True)))[:, 0]
    if np.ma.getmaskarray(mask).any() or not np.isfinite(mask.data).all():
        raise ValueError('Profile intersects missing elevations')
    z = np.asarray(gg.raster.sample_from_rasterio(dem, x, y), dtype=float)
    return distance, z
```

The distances are 2D map distances along the line, not terrain-following 3D
length. Sampling density does not improve the source raster's resolution.

## Structural measurements

Keep measurements as Point geometries. Dip-direction azimuth differs from
strike. Record whether strike uses a right-hand-rule convention before adding
90 degrees; an unoriented strike alone has a 180-degree ambiguity. Polarity
encodes stratigraphic facing, not simply whether dip is positive. Use the
entrypoint helper to reject missing/invalid attributes rather than inventing a
formation label or clamping measurements.

[Official vector implementation](https://github.com/cgre-aachen/gemgis/blob/main/gemgis/vector.py)
and [raster implementation](https://github.com/cgre-aachen/gemgis/blob/main/gemgis/raster.py),
checked against GemGIS 1.1.9 on 2026-09-14.

For true-north bearings, the helper subtracts local meridian convergence on a
locally conformal DEM projection. DEM-grid bearings must already refer to that
particular grid; a vector CRS transformation alone does not transform an angle.
Nonconformal projections require a full local orientation transformation and
are rejected by this conversion path. Magnetic declination is not inferred.
[PyProj projection factors](https://pyproj4.github.io/pyproj/stable/api/proj.html#pyproj.Proj.get_factors),
checked 2026-09-14.
