# Coordinate and raster decisions

## CRS and elevation

`GeoDataFrame.to_crs(dem.crs)` transforms coordinates. `set_crs` only assigns a
label and is suitable only when the original coordinates' CRS is known. There
is no `gemgis.vector.reproject` convenience function in the tested API.

Use a projected CRS with metre axes for the supplied modelling helper. Convert
DEM heights separately when they are in feet (multiply by 0.3048). Horizontal
reprojection does not convert an ellipsoidal height to an orthometric height;
record the vertical datum and obtain an appropriate vertical transformation
when combining incompatible sources. Reject a missing CRS instead of guessing
an EPSG code from coordinate magnitudes.

## Clip bounds

`GeoDataFrame.total_bounds` is `[xmin, ymin, xmax, ymax]`. The helper's `--extent`
is `[xmin, xmax, ymin, ymax]`, in the DEM CRS. Validate this order before using
`shapely.geometry.box(xmin, ymin, xmax, ymax)` and `gdf.clip(...)`. Clip line
geometries before extracting vertices; clipping changes endpoint locations.

## Missing data and resampling

Read Rasterio masks as well as the nodata tag. A finite nodata value such as
−9999 is not an elevation. A source without a nodata tag may still have a mask.
The supplied helper rejects masked/nonfinite/outside samples; make any fill or
exclusion policy explicit before rerunning it.

Use Rasterio's `calculate_default_transform` and `reproject` for an actual
raster reprojection. Choose a resampling method according to the variable:
nearest neighbour for categorical codes, an appropriate continuous method for
elevation. Record source and target CRS, resolution, nodata and interpolation.
Do not sample an untransformed DEM using a vector's new CRS coordinates.

## Provenance

Keep source paths/checksums, CRS WKT, vertical unit/datum, clipping extent and
nodata policy beside CSV exports because CSV has no standard CRS container.
`spatial_metadata.json` from the helper records CRS, units, datum and sources;
add project provenance/checksums for published models.

[GeoPandas reprojection API](https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoDataFrame.to_crs.html),
[Rasterio reprojection guide](https://rasterio.readthedocs.io/en/stable/topics/reproject.html),
checked 2026-09-14. Raster reprojection itself is conditional guidance, not part
of this audit's executed extraction tests.
