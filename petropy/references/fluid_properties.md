# PetroPy fluid inputs and units

`Log.fluid_properties` prepares curves consumed by `multimineral_model`.
Supply calibration parameters explicitly and retain the resolved configuration.
The helper requires the primary temperature, pressure, resistivity and fluid
classification parameters and records remaining actual method defaults.

| Input | Meaning and units |
|---|---|
| depth, top, bottom | TVD in feet below the well surface, using one stated datum |
| mast | mean annual surface temperature, °F |
| temp_grad | temperature gradient, °F/ft |
| press_grad | pore-pressure gradient, psi/ft |
| rws, rwt | water resistivity in ohm·m at a reference temperature in °F |
| rmfs, rmft | mud-filtrate resistivity in ohm·m at a reference temperature in °F |
| gas_grav | gas specific gravity relative to air |
| oil_api | API gravity; a positive value selects the oil branch |
| p_sep, t_sep | separator pressure in psi and temperature in °F |

At 5000 ft, `mast=67`, `temp_grad=0.015` gives `RES_TEMP=142 °F`;
`press_grad=0.5` gives `PORE_PRESS=2500 psi`. Passing 1524 metres without
conversion would produce an incorrect physical state even though the code runs.
These gradients use vertical separation from the surface. A deviated-well MD
index is not that separation; the helper requires an explicit TVD basis and
datum. A vertical well with MD=TVD satisfies this assumption.
Water/hydrocarbon density outputs used by the mineral model are g/cm³.

The library computes RW, RHO_W, RHO_HC, NPHI_W, NPHI_HC and formation-volume
factor curves among other outputs. BO belongs to the oil branch; BG belongs to
the gas branch and uses its empirical unit convention. Do not interchange them
or infer SI units from an absent LAS unit label. Read version-matched source
before coupling those outputs to a volumetric resource estimate.

The bundled configuration exercises an oil-fluid calculation in a fully
water-saturated synthetic mixture; it does not establish gas, sour-gas,
high-temperature, salinity-range or organic-rich validity. Use documented
correlation ranges and calibration evidence for a field case. Do not present
unreviewed parameter defaults as measured reservoir conditions.

[Official fluid_properties implementation](https://github.com/toddheitmann/PetroPy/blob/master/petropy/log.py),
checked against PetroPy 0.1.6 on 2026-09-14.
