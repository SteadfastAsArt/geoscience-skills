# Interpolation and numerical validation

## Constraint meaning

Use finite X/Y/Z in one Cartesian coordinate system. `val` is a scalar-field
observation. `gx,gy,gz` constrain gradient components and magnitude;
`nx,ny,nz` constrain a normal direction. Keep absent constraints as NaN.
Do not replace NaN orientations with zero vectors. Geological normals can have
a sign ambiguity; resolve their relationship to stratigraphic younging before
combining observations.

## FDI and PLI

FDI uses a finite-difference discretization; PLI uses a piecewise-linear
interpolator. Both are supported by the bundled helper. The `nelements`
argument controls an approximate discretization size, not the exact number of
points in an exported visualization grid. Keep solver mesh resolution separate
from `nsteps` used to sample a model for VTK.

Increase resolution only after establishing units, extent and adequate
constraints. Compare residuals at held-out observations and whether surfaces
change materially under refinement. A small least-squares residual does not
show that geological ordering, topology or fault displacement is correct.

## Coordinate evaluation

Use `model.evaluate_feature_value(name, world_xyz)` for world coordinates.
`model.regular_grid(..., shuffle=False, order='F')` returns world XYZ points in
VTK-compatible order in the tested 1.8.0 version. Do not unpack that N×3 array
as coordinate axes or call a feature directly with projected coordinates
without checking its local-coordinate contract.

NoData in an exported grid is a modelling-domain problem to inspect; the
helper fails rather than writing a visually plausible partial model. Optional
interpolators such as Surfe require separate dependencies and were not part of
this audit.

[LoopStructural model implementation](https://github.com/Loop3D/LoopStructural/blob/master/LoopStructural/modelling/core/geological_model.py),
checked against 1.8.0 on 2026-09-14.
