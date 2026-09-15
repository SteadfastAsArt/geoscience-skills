# Executed branch contracts

Choose one branch or several supported by the actual observations. The fixtures
used for repository tests are separate surveys, not evidence of co-located
geology. Shared skill installation does not install the scientific libraries.

## GPR

The `gprpy` skill's helper reads `.rad/.rd3` through GPRPy and `.sgy/.segy`
through segyio, runs selected real GPRPy operations, and exports raw,
intermediate and processed arrays in NPZ plus a checksummed JSON report. Its
sampling sidecar must state the provenance of ns/m axes or mark them unknown.
Raw `.gpr` sessions use pickle and are not a general MALA input format.

A licensed AI4DITE ground-cart SEG-Y line tests amplitude identity and
sample-index processing. The release leaves the radar time scale and coordinate
units unresolved in that file, so no field-depth conversion is claimed. A
separate project-generated MALA record checks known ns/m coordinates and a
zero-offset constant-velocity impulse-depth calculation.

## ERT two-layer diagnostic

The [bundled helper](../scripts/ert_layered_diagnostic.py) requires two CSVs:

| File | Required columns and meaning |
|---|---|
| Observations | `measurement_id`, integer `a,b,m,n` electrode IDs, `rhoa_ohm_m`, `repeatability_pct` |
| Electrodes | Unique integer `electrode_id`, unique `x_m` on an explicitly nominal flat local line |

Four electrodes must be distinct. Resistivity is apparent resistivity in Ω m,
not resistance or voltage. Convert original V/I through the correct signed
geometric factor before supplying `rhoa_ohm_m`; preserve measured columns as
additional CSV columns when useful. No hidden unit conversion is performed.
The helper retains all original rows and marks nonpositive apparent resistivity
as excluded from the log fit, with no fabricated predictions for those rows.

```bash
python scripts/ert_layered_diagnostic.py --observations observations.csv \
  --electrodes electrodes.csv --output results \
  --geometry-note "Documented nominal flat geometry, source/CRS and limitations" \
  --extra-log-sigma 0.03
```

Resolve the script relative to this installed workflow. A new output directory
is required. `responses.csv` retains observation identity, source columns,
exclusion reason, predicted apparent resistivity, log sigma and normalized log
residual, reciprocal group, held-out membership and held-out prediction.
`electrodes.csv` preserves the supplied nominal geometry. `inversion.json`
records source/output hashes, units, starting/fitted/training-only models,
assumptions, fit statistics and local convergence/rank checks. `read_result`
verifies exported hashes and reads the response rows back.

The model is a flat isotropic two-layer earth with three positive parameters:
top-layer thickness and the two resistivities. pyGIMLi VESModelling supplies
actual arbitrary-quadrupole forward responses; inversion uses log data/model
transforms, no regularization and a fixed starting model. This does not estimate
a 2D/3D resistivity distribution or compensate for topography.

The error budget is `hypot(repeatability_pct/100, extra_log_sigma)`, assigned in
log space. The additional term is an assumption, not measured total error.
The chi-square reference uses `N-3` degrees of freedom, conditional independent
Gaussian log errors and a locally identifiable nonlinear solution. A separate
local optimizer checks rank and objective stability before the fit status is
interpreted. Neither local convergence nor passing a nominal residual threshold
proves a unique geological solution or calibrated uncertainty.

The fixed holdout groups pair reversals/reciprocals by electrode identity and
hashes geometry only. Training fits and the log-mean baseline use training data
only. It shares electrodes with the held-out measurements, so it is not an
independent survey. Controlled image-series synthetic recovery is a distinct
test; it is never labelled a recovered field ground truth.

## MT

Use the `mtpy` skill for the executed MTpy-v2 direct-impedance EDI path. The
constructor does not itself read the EDI: call `read(get_elevation=False)` to
avoid an external elevation lookup. Establish MT impedance units, time/axis
conventions, source rotation and variance masks before QC or rotation. Complete
tensors/variances are required for the tested additional rotation. Preserve
valid negative yx phases and unknown uncertainty.

The tested products are complete component/frequency QC CSV, provenance JSON,
an optional response figure, and a native EDI round trip for complete data.
Some upstream EDI writer zero/EMPTY semantics require a separate mask-aware CSV.
These are transfer-function operations; an MT inversion solver and raw-series
estimation are not validated by reading or plotting EDI.
