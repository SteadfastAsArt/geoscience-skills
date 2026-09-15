---
name: mtpy
description: >-
  Read and validate magnetotelluric transfer functions with MTpy-v2. Use for EDI
  import, impedance uncertainty, apparent resistivity/phase, documented tensor
  rotations, response plots and preparation for modelling. External inversion
  solvers and raw time-series processing require separate tools and validation.
license: MIT
metadata:
  version: "1.0.2"
  author: Geoscience Skills
  tags: '["Magnetotellurics", "MT", "EDI", "Impedance Tensor", "Geophysics"]'
  dependencies: '["mtpy-v2>=2.1.4", "numpy", "pandas", "matplotlib"]'
  complements: '["simpeg", "pyvista"]'
  workflow_role: analysis
  skill_type: domain
---

# MTpy-v2: Transfer-Function Analysis

Install the **`mtpy-v2` distribution**, which imports as `mtpy`. The older `mtpy`
distribution has a different API; do not install both in one environment.
The operations below were executed with MTpy-v2 2.1.4 and mt-metadata 1.0.10.

## Read and establish conventions

```python
from mtpy import MT

station = MT("station.edi")
station.read(get_elevation=False)  # constructor alone does not load the file
frequency_hz = station.frequency
z = station.Z.z                   # complex tensor, shape (frequency, 2, 2)
sigma_z = station.Z.z_error       # standard deviation, not EDI variance
rho = station.Z.resistivity       # ohm m
phase = station.Z.phase           # degrees, signed component phases
```

Confirm impedance units, time convention, axes, channel orientation, `ZROT`,
horizontal CRS and elevation reference from acquisition metadata. An EDI `UNITS`
field can describe distances rather than impedance. MT units are mV/km/nT;
the corresponding E/H impedance in ohms is multiplied by `mu0 * 1000`.
For MT units, apparent resistivity is `0.2 * abs(z)**2 / frequency_hz`.
Do not call `xy` and `yx` TE/TM until a justified 2D strike coordinate system
has been established. A yx phase near -135 degrees can be valid under NED.

Read [EDI conventions and missingness](references/edi_format.md) when handling
empty values, variances or exports. mt-metadata can represent missing EDI values
as zero, so inspect source masks before computing quality flags or rotating.
Missing uncertainty is not an exact observation.

## QC, rotation and export

Use the [QC helper](scripts/mt_analysis.py) for **direct-impedance EDI** after
confirming mV/km/nT, positive time convention and north/east/down:

```bash
python scripts/mt_analysis.py station.edi --output-dir results \
  --impedance-units mt --sign-convention + --plot
```

Resolve the script relative to this skill directory. It exports every frequency
and all four components with missingness, uncertainty and diagnostic flags, plus
a JSON provenance file. It reopens its CSV and refuses existing output files.
The default 50% relative-error threshold is a recorded diagnostic choice;
choose task-specific criteria before examining the desired interpretation.

An additional clockwise rotation is available as `--rotation-deg 30`; it requires
complete tensors and variances. It adds to the original orientation, not an
absolute strike estimate. The tested direct library equivalent is
`station.rotate(30, inplace=True)`; its default in-place form returns `None`.
Marginal error propagation does not provide a full covariance model.

For complete data, write with `station.write(fn="copy.edi")`, then read back
coordinates, rotation and tensors. The native EDI writer maps numeric zeros to
its EMPTY sentinel; preserve the original and a separate mask-aware CSV when
physical zeros or missing components matter. Read
[response plotting](references/plotting.md) only when a figure is requested.

## Interpretation and validation

Compare tensor components, uncertainty, phase behavior and frequency coverage
before dimensionality analysis. Phase-tensor skew is a diagnostic affected by
noise and sampling, not a universal pass/fail test for 3D geology. Do not apply
automatic strike or static-shift corrections without independent justification.
Preparing ModEM/Occam inputs is separate from executing an installed solver.

The repository's near-surface workflow checks a field-derived upstream EDI
sample, independent tensor algebra, synthetic responses and output readback.
It does not establish raw time-series estimation, field inversion or geological
uniqueness. Consult the installed-version
[MTpy-v2 API](https://mtpy-v2.readthedocs.io/en/latest/mtpy.html) for other formats
and survey collections; do not substitute older v1 method names.
