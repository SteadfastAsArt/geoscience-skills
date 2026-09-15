---
name: gprpy
description: >-
  Read and process ground-penetrating radar profiles using GPRPy. Use for
  sample-based dewow/background removal, auditable gain, time/depth scenarios,
  and radargram export with explicit acquisition units. SEG-Y input uses a
  separate segyio adapter; native GPRPy files are serialized sessions.
license: MIT
metadata:
  version: "1.0.2"
  author: Geoscience Skills
  tags: '["GPR", "Ground-Penetrating Radar", "Near-Surface", "Signal Processing", "GPRPy", "Geophysics", "Depth Conversion", "Radargram"]'
  dependencies: '["gprpy>=1.0.14", "numpy<2", "matplotlib", "scipy", "segyio>=1.9.14"]'
  complements: '["pyvista"]'
  workflow_role: data-loading
  skill_type: domain
---

# Auditable GPR processing

GPRPy operates on arrays shaped `(samples, traces)`. Inspect acquisition
metadata before assigning physical axes: a trace index is not distance, and a
radar vendor's SEG-Y interval field may need a documented time scale. Preserve
unknown units explicitly. Do not obtain a site velocity from a generic material
lookup and present it as measured.

## Read and select operations

GPRPy 1.0.14 natively reads paired MALA `.rad/.rd3`, Sensors & Software
`.DT1/.HD`, GSSI `.DZT`, and its documented BSQ inputs. Native `.gpr` files are
Python pickle sessions, not a MALA exchange format; read only trusted sessions.
GPRPy does not natively read or export SEG-Y.

```python
import gprpy.gprpy as gp

profile = gp.gprpyProfile()
profile.importdata('profile.rad')  # requires matching profile.rd3
raw = profile.data.copy()
profile.dewow(window=64)  # argument is sample count, not ns
```

Select operations to answer the user's question. `dewow(window)` and
`agcGain(window)` take sample counts; `remMeanTrace(ntraces)` takes traces.
Background subtraction may remove real continuous reflectors. Time-power gain
changes amplitude scaling and is not a calibrated attenuation correction.
Keep the raw arrays and record every applied operation. Window edge behaviour
and the effective interior support need particular care; see the
[processing reference](references/processing_steps.md).

`setVelocity(velocity)` uses m/ns and computes the zero-offset constant-velocity
scenario `depth = twtt * velocity / 2`; it does not estimate velocity or migrate
reflectors. Resolve time zero and antenna-offset assumptions first. Retain
native two-way time alongside any assumed depth, and state which independent
measurements support velocity and its uncertainty.

## Reproducible helper

The [processing helper](scripts/process_gpr.py) supports tested `.rad/.rd3` and
`.sgy/.segy` routes. The latter explicitly uses segyio before real GPRPy
processing. It writes `profile.npz` and `processing.json` and reads them back;
NPZ loading uses `allow_pickle=False`. Outputs include raw amplitudes,
intermediate arrays, final amplitudes, original sample/trace indices, available
physical axes, source checksums, parameters and selected encoded header fields.
A new output directory prevents silent replacement of a previous result.

```bash
python scripts/process_gpr.py profile.rad --metadata sampling.json \
  --output processed --dewow-samples 64
```

Resolve paths relative to the installed skill directory. `sampling.json`
contains `source_note`, `sample_interval_ns`, `time_origin_ns`,
`trace_spacing_m`, `profile_origin_m`, `horizontal_crs` and `vertical_reference`.
Use JSON `null` for unknown time or spacing; explain provenance in `source_note`.
Uniform physical sampling requires a finite origin and a positive interval.
Irregular positions require a separately validated geometry route; do not
replace them with a fabricated regular line.

Only supply `--gain-power` when nonnegative physical time is known. Only supply
`--velocity-m-ns` for an explicitly labelled zero-offset constant-velocity depth
scenario. Both are rejected when time calibration is unresolved. No processing
step is enabled by default. The helper fails on missing/nonfinite amplitudes,
unsupported formats, non-live SEG-Y trace flags, variable trace sampling or a
failed requested export instead of reporting partial work as success.

## Other APIs and verification boundary

For plotting, use `showProfile()` or `printProfile(...)`; neither accepts the
previously documented `ax=` export pattern. GPRPy 1.0.14 has no
`bandpassFilter`, `exportASCII`, `exportSEGY` or `gprpyCMP` API. Its CMP/WARR
class is `gprpyCW`; consult the installed source before using its stacked
amplitude methods. Topographic correction uses `topoCorrect(topofile,
delimiter=',')` after a separately chosen velocity, not a `velocity=` keyword.
These advanced branches require their own acceptance checks.

The checked path uses fixed GPRPy source version 1.0.14, native generated MALA
bytes, and one licensed observed SEG-Y line. The field line's time scaling and
coordinate units remain unresolved, so only sample-index processing is claimed.
Synthetic timing and impulse depth checks are separate from field accuracy.
See [source installation and limits](references/processing_steps.md#tested-source)
for the tested commit and dependency distinction.
