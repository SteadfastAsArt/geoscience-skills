---
name: petropy
description: |
  Configure PetroPy fluid-property and multimineral formation evaluation from
  normalized LAS well logs. Use for calibrated porosity, water saturation,
  mineral and pore-volume estimation, missing-sample handling, and explicitly
  defined pay intervals. Requires documented log units, fluid parameters and
  mineral endpoints; standalone permeability correlations need separate methods.
license: MIT
metadata:
  version: "1.0.2"
  author: Geoscience Skills
  tags: '["Petrophysics", "Formation Evaluation", "Water Saturation", "Porosity", "PetroPy", "Well Logs", "Permeability", "Archie"]'
  dependencies: '["petropy==0.1.6", "lasio==0.30", "numpy>=1.26,<2", "setuptools<81", "cchardet==2.2.0a2"]'
  complements: '["lasio", "welly", "striplog"]'
  workflow_role: analysis
  skill_type: domain
---

# Configured PetroPy formation evaluation

PetroPy 0.1.6 uses `Log.fluid_properties()` followed by
`Log.multimineral_model()`. It does not provide the previously shown
`shale_volume`, `formation_porosity`, `water_saturation`, `permeability` or
`to_las` methods. Export a Log with `write(...)`.

## Environment and input contract

Use an isolated Python 3.11 environment with the metadata dependencies. The
verified combination is PetroPy 0.1.6, lasio 0.30 and NumPy 1.26.4; lasio 0.32
removed `add_curve`, which PetroPy still calls. Old lasio 0.23/0.29 also fail
with modern NumPy during header parsing. The cchardet prerelease has Python
3.11 wheels; dependency declarations in this skill do not install packages.

Before creating `Log`, prepare and inspect measured `GR_N`, `NPHI_N`, `RHOB_N`
and `RESDEEP_N`. Their units are API, fraction v/v, g/cm³ and ohm·m. Input depth
must be strictly increasing nonnegative feet of **TVD below the well surface**,
with an identified datum, for these temperature/pressure correlations. The
synthetic fixture is a vertical well where MD equals TVD. Deviated-well MD
cannot be passed directly; establish a TVD/PVT treatment separately without
silently resampling the logs. Convert percent
neutron porosity explicitly. Do not rely on PetroPy's legacy density-porosity
fallback: require a validated measured density curve before preconditioning.
Keep missing measurements as NaN and retain their masks.

## Run a configured model

The following function expects input satisfying that contract and a reviewed
configuration. Declare `depth_basis="tvd_below_surface"` and `depth_datum`;
the helper rejects an MD basis. [example_config.json](references/example_config.json) is a
synthetic clean quartz/calcite calibration, not a default calibration for a
field well. Adjust its interval, fluid parameters, mineral endpoints and
weights using actual well/laboratory information before field use.

```python
import json
import petropy as pp

def run_configured(las_path, config_path):
    with open(config_path, encoding='utf-8') as stream:
        config = json.load(stream)
    top, bottom = config['interval_ft']
    log = pp.Log(str(las_path))
    log.fluid_properties(top=top, bottom=bottom, **config['fluid'])
    log.multimineral_model(top=top, bottom=bottom, **config['multimineral'])
    return log
```

PetroPy 0.1.6 requires `top` and `bottom` to equal existing sampled depths, yet
calculates on `[top, bottom)`: the bottom sample remains unevaluated. Do not
pass an arbitrary interval endpoint or describe all samples as evaluated.
The library skips rows with missing required measurements; do not turn those
rows into zero porosity, zero saturation or non-pay.

## Validated helper and result checks

The [formation evaluation helper](scripts/formation_evaluation.py) validates
normalized curve names/units, increasing feet depth, exact interval endpoints,
explicit fluid/mineral calibration and positive density/resistivity. It runs
the actual library, checks bulk and pore-volume closure, and writes LAS plus a
JSON record of resolved parameters, interval, sample counts and source checksum.
It rejects previously calculated model curves to prevent stale values surviving
at missing or excluded samples.

```bash
python scripts/formation_evaluation.py normalized.las \
  --config reviewed_config.json --output evaluated.las
```

Resolve the script relative to the installed skill directory. Confirm for
evaluated rows that matrix-mineral bulk volumes + BVCLAY + BVOM + BVPYR + PHIE
sum to one, BVW + BVH equals PHIE, and SW/PHIE remain physical fractions.
These are necessary consistency checks, not proof of a correct formation model.

Read [calculations and pay intervals](references/calculations.md) for the
difference between bulk and matrix fractions and a stated thickness convention.
Read [fluid-property units](references/fluid_properties.md) before changing
PVT inputs or interpreting fluid outputs. Standalone permeability, clustering,
plotting and gas/shaly/organic-rich calibrations need separate validation.

## Verification scope

Executed real LAS read/write, configured fluid calculation and two-mineral
NNLS evaluation with project-generated observations. The analytic synthetic
mixture is 65% quartz, 15% calcite and 20% water-filled pores. Tests check
recovered fractions, conservation, feet-based temperature/pressure, NaN masks,
interval edges and CLI failures. This is an API and physical-consistency
baseline, not field calibration or a blanket validation of legacy PetroPy.

[Official PetroPy implementation](https://github.com/toddheitmann/PetroPy/blob/master/petropy/log.py),
checked against 0.1.6 on 2026-09-14.
