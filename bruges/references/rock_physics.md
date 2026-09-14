# Rock physics calculations

These independent examples use Bruges 0.5.4. Use m/s, kg/m³ and Pa consistently;
mineral/fluid tables expressed in GPa or g/cm³ require conversion first.

## Elastic moduli and velocities

Use keyword arguments: several moduli functions share long signatures, so
positional arguments can bind to a different property than intended.

```python
import numpy as np
from bruges.rockphysics import moduli

vp, vs, rho = 3000.0, 1700.0, 2300.0
bulk_pa = moduli.bulk(vp=vp, vs=vs, rho=rho)
shear_pa = moduli.mu(vs=vs, rho=rho)
youngs_pa = moduli.youngs(vp=vp, vs=vs, rho=rho)
poisson = moduli.pr(vp=vp, vs=vs)
bulk_gpa = bulk_pa / 1e9
vp_roundtrip = moduli.vp(bulk=bulk_pa, mu=shear_pa, rho=rho)
vs_roundtrip = moduli.vs(mu=shear_pa, rho=rho)
```

For an isotropic elastic solid, require finite positive density, shear modulus
and bulk modulus. The stability range is `-1 < poisson < 0.5`; the narrower
positive range is common for rocks but is not the full mathematical range.
The functions do not automatically convert units or validate log quality.

## Empirical estimates

Gardner belongs to `bruges.petrophysics`, and its default output is kg/m³.
Castagna's mudrock relation is written explicitly because Bruges 0.5.4 has no
`rockphysics.castagna` function. These empirical relations require local
calibration; label derived curves and retain the measured input.

```python
import numpy as np
from bruges.petrophysics import gardner

vp_m_s = np.array([2000.0, 3000.0, 4000.0])
rho_kg_m3 = gardner(vp_m_s)
rho_g_cm3 = rho_kg_m3 / 1000.0
vs_m_s = (vp_m_s - 1360.0) / 1.16  # Castagna mudrock line, m/s.
```

Reject nonpositive predicted Vs instead of treating it as a fluid layer.
The fit should not be extrapolated indiscriminately to unconsolidated soil,
carbonates, gas-bearing formations or laboratory pressure conditions.

## Gassmann fluid substitution

The example substitutes brine with a gas using illustrative fluid properties.
`kmin` is the **mineral** bulk modulus, not the dry-frame modulus; this API
needs neither mineral density nor an argument named `rho_min`.

```python
import numpy as np
from bruges.rockphysics import avseth_fluidsub, moduli

vp_sat, vs_sat, rho_sat = 3000.0, 1700.0, 2300.0
phi = 0.20
rho_brine, rho_gas = 1050.0, 100.0  # kg/m³
kmin, k_brine, k_gas = 37e9, 2.5e9, 0.05e9  # Pa
substituted = avseth_fluidsub(
    vp=vp_sat, vs=vs_sat, rho=rho_sat, phi=phi,
    rhof1=rho_brine, rhof2=rho_gas,
    kmin=kmin, kf1=k_brine, kf2=k_gas,
)
vp_new, vs_new, rho_new = substituted
mu_before = moduli.mu(vs=vs_sat, rho=rho_sat)
mu_after = moduli.mu(vs=vs_new, rho=rho_new)
```

For these inputs density decreases by 190 kg/m³. The shear modulus is
unchanged, while Vs changes with density. Also check identity substitution
and the saturated/dry/mineral modulus ordering. Require `0 < phi < 1`,
positive fluid/mineral moduli and plausible saturated properties before
applying this simple model; do not replace invalid outputs with zero.

Gassmann assumes a connected equilibrated pore system at low frequency, an
isotropic solid frame, and no fluid-induced frame alteration. Calibrate fluid
properties to pressure, temperature and composition. Fluid substitution alone
is not a saturation inversion or a unique hydrocarbon indicator.

## Mineral mixing and conditional models

For mineral mixing, `voigt_bound`, `reuss_bound`, `hill_average` and
`hashin_shtrikman` are available in `bruges.rockphysics`. Keep volume fractions
normalized and moduli in the same units. A mineral mixture's modulus is not
a dry porous frame modulus. Select contact/effective-medium models only when
their pore geometry and stress assumptions are justified; consult the
specific upstream API before using a model not exercised here.

## Sources

API and units checked **2026-09-14**:

- [Bruges moduli API](https://code.agilescientific.com/bruges/api/bruges.rockphysics.html#module-bruges.rockphysics.moduli)
- [Bruges 0.5.4 fluid substitution source](https://github.com/agilescientific/bruges/blob/v0.5.4/bruges/rockphysics/fluidsub.py)
- [Bruges 0.5.4 Gardner source](https://github.com/agilescientific/bruges/blob/v0.5.4/bruges/petrophysics/petrophysics.py)
- [Castagna, Batzle and Eastwood (1985)](https://doi.org/10.1190/1.1441933): empirical velocity relationships.
- [SEG mudrock-line definition](https://wiki.seg.org/wiki/Dictionary:Mudrock_line/en): `Vp = 1.16*Vs + 1.36`, with velocities in km/s.
