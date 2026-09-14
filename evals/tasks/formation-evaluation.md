# Formation evaluation with missing intervals

Complete a well-log formation evaluation from `inputs/formation.las` and the
calibration parameters in `inputs/formation-parameters.json`: load the logs,
check curve validity, calculate petrophysical properties, and construct merged
lithology intervals while preserving gaps. Keep every original depth row and
the original measurements. Do not despike, resample, or interpolate this small
fixture, and do not generate figures.

Write `evaluated.json` containing an object with a `rows` array. Each row must
have `depth_m`, `qc_valid`, `vsh`, `phi_d`, `sw`, and `sw_clipped`. Numeric derived
values that cannot be calculated must be JSON `null`, never NaN or Infinity.
The LAS NULL sentinel is missing data. A row is QC-valid only if GR, RHOB and RT
are finite and RHOB and RT are positive.

- Vsh is the linear GR index clipped to [0, 1], using the supplied sand/shale
  endpoints; it is null for QC-invalid rows.
- Density porosity uses the supplied matrix and fluid densities. Keep it only
  for QC-valid rows when its value is in [0, 1], otherwise null.
- Use clean-formation Archie saturation with the supplied `a`, `m`, `n`, and
  formation-water resistivity. Saturation is null if porosity is missing or
  non-positive; otherwise clip to [0, 1]. `sw_clipped` is true only where the
  finite unbounded saturation was greater than 1.

Also write `lithology.json` with an `intervals` array. An interval between two
adjacent depth samples exists only if both samples have valid Vsh. Classify it
using the upper sample: Vsh < 0.3 is `sandstone`, 0.3 <= Vsh < 0.6 is
`siltstone`, otherwise `shale`. Merge touching intervals with equal lithology;
never join intervals across an invalid sample. Each interval must contain
`top_m`, `base_m`, and `lithology`, sorted by depth.

This is a synthetic clean-formation calculation. The specified Archie model
is not a validated saturation model for shaly field formations. Retain the
provided units and calibration choices in comments in `solution.py`.
