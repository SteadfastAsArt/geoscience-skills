---
name: near-surface-geophysics
description: >-
  Plan and validate near-surface interpretation from GPR, electrical resistivity
  tomography, or magnetotelluric data. Use when selecting acquisition-dependent
  processing and inversion branches, comparing survey results, or relating
  geophysical anomalies to independently supported geological hypotheses.
license: MIT
metadata:
  version: "1.0.1"
  author: Geoscience Skills
  skill_type: workflow
  tags: '["Near Surface", "GPR", "ERT", "Magnetotellurics"]'
  dependencies: '["gprpy", "pygimli", "mtpy-v2", "numpy", "pandas", "scipy", "matplotlib"]'
  complements: '["gprpy", "pygimli", "mtpy", "simpeg", "pyvista"]'
  workflow_role: analysis
---

# Near-Surface Geophysics

Select only branches supported by the supplied data. This is a single-agent
workflow; companion skills are optional references, and a missing GPR or MT
dataset does not prevent an ERT-only interpretation.

## Input-dependent routes

| Input | Start with | Required checks before interpretation |
| --- | --- | --- |
| GPR traces and acquisition geometry | `gprpy` | Trace order/spacing, sample-time units, time zero, antenna offsets and an independently supported velocity model |
| ERT electrode geometry and measurements | `pygimli` | Electrode indexing, measured quantities, geometric factors, uncertainty/reciprocals and topography |
| MT transfer functions or EDI files | `mtpy` | Frequency coverage, impedance units and convention, rotations, tensor components and uncertainty |
| Multiple methods with compatible survey support | Process each branch independently, then compare | Common CRS/vertical reference, resolution, uncertainty and acquisition timing |

If only an image is available, state which quantitative operations require raw
data or survey metadata. Do not infer a complete inversion dataset from colours
or an unlabelled axis. Check package version and file-reader support before
choosing a library-specific implementation.

## Shared preparation

Retain raw files and acquisition metadata with checksums. Establish horizontal
CRS, elevation datum, profile direction, measurement units and sign conventions.
Keep instrument flags and a record of excluded readings. Describe the physical
question and independent borehole, geological or hydrological constraints before
tuning an image or model to resemble an expected structure.

## GPR branch

Inspect unprocessed radargrams first. Apply time-zero correction only when a
justified reference is available, and select documented signal processing;
compare each step to the input.
Record filter bands relative to sample interval and antenna bandwidth. Gain
changes amplitude interpretation, and background removal can suppress genuine
laterally continuous reflectors. Preserve original amplitudes when an amplitude
comparison is required.

Keep two-way travel time as the native vertical coordinate until velocity is
supported by survey measurements or a stated scenario. Report the assumed
velocity, units and uncertainty for depth conversion or migration; do not use
a generic dielectric constant as a measured site property. Separate an observed
reflector from a geological boundary hypothesis.

The checked GPR route is raw SEG-Y via segyio or native paired MALA via GPRPy,
selected sample/trace operations, then NPZ plus JSON export and readback. The
`gprpy` helper records encoded headers and leaves unresolved time/position units
as indices. GPRPy's dewow window is a sample count; it has no native SEG-Y
export API. Use the companion helper when installed, or implement the same
auditable steps with the available libraries and their current documentation.

## ERT branch

Distinguish measured resistance/voltage/current from apparent resistivity. Verify
electrode indices and geometry before recomputing geometric factors, including
topography where required. Estimate errors from repeat/reciprocal observations
when available; document any assumed error floor and filtering criteria.
See the [pyGIMLi topography example](https://www.pygimli.org/_examples_auto/3_ert/plot_02_ert_field_data/)
when selecting the matching data and geometric-factor route.

Check forward response and data units before inversion. Compare observed and
predicted data, normalised residuals, convergence and sensitivity to mesh,
regularisation and starting model. A pseudosection is a data display, not a
resolved depth model. A small misfit alone does not establish uniqueness or
depth of investigation; mark weakly constrained regions using justified
sensitivity/resolution analysis and alternative plausible models.

For an explicitly flat two-layer diagnostic, the bundled
[ERT helper](scripts/ert_layered_diagnostic.py) provides an executed route from
quadrupole measurements and nominal electrode positions to inversion, a fixed
reciprocal-group holdout, and CSV/JSON response/residual readback. It checks
local convergence and reports when the combined model/error assumptions fail.
This lightweight route is not a topographic 2D/3D ERT reconstruction; use an
appropriate mesh/solver for those tasks. See the
[input schema and branch limits](references/validated_branches.md).

## MT branch

Inspect tensor components, uncertainty, frequency sampling and phase behaviour.
Confirm units, time convention and rotations before plotting apparent
resistivity/phase or exporting inversion inputs. Use the `mtpy` skill and the
installed-version documentation for EDI and transfer-function details. Choose
1D, 2D or 3D modelling only after examining dimensionality, survey geometry and
available computational tools; a plotting library does not guarantee an
installed inversion solver.

The checked MT route uses the `mtpy-v2` distribution: read direct-impedance EDI,
inspect source masks/variances, apply an explicitly requested tensor rotation,
then export QC CSV/JSON and optional response plots with readback. Complete
tensors also undergo actual EDI write/read. A field-derived transfer-function
sample supports this route; raw time-series estimation and MT inversion remain
separate tasks. Preserve signed component phases and unknown uncertainties.

## Comparison, outputs and limits

Deliver QC tables, processing/model configuration, observed-versus-predicted
checks, georeferenced products and uncertainty notes. Preserve each method's
native sampling/resolution when overlaying results; resampling onto one grid
does not create equal resolution or independent evidence.

Test interpretation against withheld lines, repeat surveys or independent site
information when available. Shared preprocessing, priors and reused boreholes
must not enter both model fitting and a supposedly independent validation set.
Electrical properties also depend on fluids, salinity, saturation, temperature
and clay; avoid converting a resistivity anomaly directly into a unique lithology,
water table or hydraulic conductivity without calibrated supporting evidence.

The three branches now have separate executed import-to-export checks: observed
GPR sample-index processing plus separately generated physical-unit data,
observed ERT fit/holdout plus separate controlled model recovery, and an upstream
field-derived MT EDI plus independent tensor/impedance checks. They are different
surveys and must not be combined into a fictitious common-site interpretation.
Joint inversion, general field accuracy and every vendor format are outside
these checks; report the branch and physical assumptions actually exercised.
