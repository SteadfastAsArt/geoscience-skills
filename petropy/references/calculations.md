# Model configuration and volume accounting

## Calibrate a multimineral model

PetroPy solves its configured mineral/fluid response model iteratively.
Provide matrix/clay GR endpoints, selected mineral density/neutron (and PE when
used) endpoints, fluid properties and saturation-model weights. The bundled
JSON selects quartz and calcite, uses densities 2.65 and 2.71 g/cm³, and uses
Archie alone for a clean synthetic rock. It explicitly overrides PetroPy
0.1.6's unsuitable default `rho_clc=1.71` for calcite.

Archie's clean-rock relation is `Sw = (a*Rw/(Rt*phi**m))**(1/n)` before physical
bounds. Rw and Rt must share resistivity units; porosity is a fraction. A shale
correction or alternative model requires its own calibration. Do not combine
weights accidentally: set unwanted saturation and shale-volume methods to
zero. Organic-rich branches introduce additional assumptions even when a
single callable is named `multimineral_model`.

## Volume definitions

`BVQTZ`, `BVCLC`, other selected `BV...` minerals, `BVCLAY`, `BVOM`, `BVPYR`
and `PHIE` are bulk-rock volume fractions. Matrix-normalized `VQTZ`, `VCLAY`
and similar curves use a different denominator; do not add those to bulk
porosity and call the result a closure test. `SW`/`SHC` are pore-space fractions;
`BVW`/`BVH` are bulk-rock pore volumes. `BVWI` and `BVWF` partition bulk water.

The regression mixture is independently specified as 0.65 quartz + 0.15
calcite + 0.20 water. Its density/neutron measurements are forward mixtures of
those endmembers; its resistivity obeys Archie at full water saturation.
Expected recovered values and closure provide an oracle beyond merely checking
that the call returned an array. PVT empirical accuracy is not established by
this self-consistent forward/inverse check.

## Pay and thickness

The helper's optional pay block requires explicit porosity, saturation and
clay cutoffs. Unevaluated/missing samples remain NaN in PAY. Its convention is
piecewise constant from each left sample over `[depth[i], depth[i+1])`, with
actual irregular spacing, within the requested half-open interval. It does
not count one extra sample interval below the bottom. Output thickness is in
feet, not metres. `unknown_interval_ft` reports intervals assigned to missing
left samples rather than silently treating them as non-pay.

Different projects may use midpoint cells, interpolated threshold crossings
or TVT corrections. Those require a new stated integration convention. Do not
sum flags and multiply by a median step on irregular or gapped logs. A
measured-depth thickness is not true vertical/stratigraphic thickness.

## Legacy branches

The helper requires measured normalized density rather than the library's
DPHI fallback, and refuses reuse of previously derived model outputs. Electrofacies,
plots, custom permeability correlations and model ensembles are outside the
executed audit. Consult and test their actual installed API before use.

[PetroPy source and parameter definitions](https://github.com/toddheitmann/PetroPy/blob/master/petropy/log.py),
checked 2026-09-14.
