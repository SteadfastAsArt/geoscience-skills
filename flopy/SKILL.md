---
name: flopy
description: Build, run, inspect and diagnose MODFLOW groundwater flow models with FloPy. Use for aquifer discretization, recharge and boundary conditions, hydraulic heads, groundwater budgets and MODFLOW 6 output; use Pastas for statistical head time series.
license: MIT
metadata:
  version: "1.0.0"
  author: Geoscience Skills
  skill_type: domain
  tags: '["Groundwater", "MODFLOW", "Hydrology"]'
  dependencies: '["flopy==3.11.0"]'
  complements: '["pastas", "discretize", "pyvista"]'
  workflow_role: modelling
---

# FloPy

Produce a reproducible groundwater model and a checked water budget. FloPy writes
and reads MODFLOW files; solving also requires a compatible MODFLOW executable.

## Inputs and choices

- Establish horizontal CRS, vertical datum, length/time units, layer tops/bottoms,
  active cells, hydraulic properties, stresses and observation uncertainties.
- Head is an elevation relative to a datum. Depth below a well collar must first
  be converted with the collar elevation; a LAS depth curve is not a head series.
- Choose steady or transient conditions from the question and stress history.
  Distinguish hydraulic conductivity (length/time), transmissivity (length²/time),
  recharge (length/time) and pumping (length³/time; extraction is negative).
- Keep MODFLOW 6 packages separate from older MODFLOW model/package APIs. Use an
  isolated project environment and record the executable version and origin.

## Workflow

1. Audit geometry, layer ordering and boundary coverage before assigning values.
2. Build the simulation, temporal discretization, solver, flow model and packages.
   Specify convertible/confined cells deliberately, with storage for transients.
3. Write inputs, run the declared executable, and fail if it reports failure.
4. Inspect head/budget files and listing convergence; mask dry/inactive sentinel
   values before statistics. Do not treat a successful process as calibration.
5. Compare observations with uncertainties, inspect budget discrepancy and run
   grid/time-step sensitivity. Hold out wells or periods before tuning parameters.

## Small executable benchmark

Run [scripts/confined_flow.py](scripts/confined_flow.py) in an empty output folder:

```bash
python confined_flow.py --workspace ./flow-check --exe /path/to/mf6
```

The script models a **synthetic** confined strip: 11 cells, each 10 m long and
10 m wide, 20 m thick, K = 1 m/day, with fixed heads of 10 and 9 m at the end
cell centres. The 100 m separation implies a linear head profile and a flow of
2 m³/day. The layer spans elevations -20 to 0 m relative to an arbitrary local
datum, so both imposed heads are above the aquifer top. It checks the head
profile and flow against actual MODFLOW output. No recharge, pumping,
storage or heterogeneous calibration is implied by this benchmark.

## Outputs and interpretation

Keep the input deck, solver/listing output, heads, cell budget and a summary of
units, boundary assumptions, executable and package versions. Report residuals
and uncertainty separately from parameter plausibility and identifiability.

Read the [FloPy documentation](https://flopy.readthedocs.io/en/latest/) for package
arguments and [MODFLOW 6 documentation](https://modflow6.readthedocs.io/en/latest/)
for governing equations and solver diagnostics.
