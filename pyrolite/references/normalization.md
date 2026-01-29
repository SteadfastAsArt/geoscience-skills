# Normalization References

## Table of Contents
- [Chondrite Normalizations](#chondrite-normalizations)
- [Mantle Normalizations](#mantle-normalizations)
- [Crustal Normalizations](#crustal-normalizations)
- [MORB Normalizations](#morb-normalizations)
- [Usage Examples](#usage-examples)

## Chondrite Normalizations

Used for REE (Rare Earth Element) patterns.

| Reference | Code | Source |
|-----------|------|--------|
| McDonough & Sun 1995 | `Chondrite_McDonough1995` | Most commonly used |
| Sun & McDonough 1989 | `Chondrite_SunMcDonough1989` | Widely cited |
| Boynton 1984 | `Chondrite_Boynton1984` | Classic reference |
| Anders & Grevesse 1989 | `Chondrite_AndersGrevesse1989` | CI chondrite |
| Palme & O'Neill 2014 | `Chondrite_PalmeONeill2014` | Updated values |

### Chondrite Values (McDonough & Sun 1995, ppm)

| Element | Value | Element | Value |
|---------|-------|---------|-------|
| La | 0.237 | Tb | 0.0353 |
| Ce | 0.613 | Dy | 0.246 |
| Pr | 0.0928 | Ho | 0.0546 |
| Nd | 0.457 | Er | 0.160 |
| Sm | 0.148 | Tm | 0.0247 |
| Eu | 0.0563 | Yb | 0.161 |
| Gd | 0.199 | Lu | 0.0246 |

## Mantle Normalizations

Used for multi-element spider diagrams.

| Reference | Code | Description |
|-----------|------|-------------|
| Primitive Mantle (McDonough 1995) | `PM_McDonough1995` | Most common for spider diagrams |
| Primitive Mantle (Sun 1989) | `PM_SunMcDonough1989` | Alternative PM values |
| Depleted Mantle | `DM_Salters2004` | For MORB source |
| Pyrolite | `Pyrolite_McDonough1995` | Bulk silicate Earth |

### Primitive Mantle Values (McDonough & Sun 1995, ppm)

| Element | Value | Element | Value |
|---------|-------|---------|-------|
| Cs | 0.021 | Nb | 0.658 |
| Rb | 0.600 | La | 0.648 |
| Ba | 6.600 | Ce | 1.675 |
| Th | 0.0795 | Pb | 0.150 |
| U | 0.0203 | Sr | 19.9 |
| K | 240 | Nd | 1.250 |
| Ta | 0.037 | Sm | 0.406 |

## Crustal Normalizations

Used for comparison with crustal rocks.

| Reference | Code | Description |
|-----------|------|-------------|
| Upper Continental Crust | `UCC_RudnickGao2003` | Most used for crustal studies |
| Upper Crust (Taylor 1981) | `UCC_TaylorMcLennan1985` | Classic reference |
| Bulk Continental Crust | `BCC_RudnickGao2003` | Bulk crust average |
| Lower Continental Crust | `LCC_RudnickGao2003` | Mafic lower crust |
| PAAS | `PAAS_TaylorMcLennan1985` | Post-Archean Australian Shale |

### Upper Continental Crust Values (Rudnick & Gao 2003, ppm)

| Element | Value | Element | Value |
|---------|-------|---------|-------|
| La | 30 | Tb | 0.7 |
| Ce | 64 | Dy | 3.9 |
| Pr | 7.1 | Ho | 0.83 |
| Nd | 26 | Er | 2.3 |
| Sm | 4.5 | Tm | 0.33 |
| Eu | 0.88 | Yb | 2.2 |
| Gd | 3.8 | Lu | 0.32 |

## MORB Normalizations

Used for ocean floor basalts and mantle-derived rocks.

| Reference | Code | Description |
|-----------|------|-------------|
| N-MORB (Sun & McDonough) | `NMORB_SunMcDonough1989` | Normal MORB |
| E-MORB (Sun & McDonough) | `EMORB_SunMcDonough1989` | Enriched MORB |
| Average MORB | `MORB_Gale2013` | Updated global average |

### N-MORB Values (Sun & McDonough 1989, ppm)

| Element | Value | Element | Value |
|---------|-------|---------|-------|
| Cs | 0.007 | La | 2.50 |
| Rb | 0.56 | Ce | 7.50 |
| Ba | 6.30 | Nd | 7.30 |
| Th | 0.12 | Sm | 2.63 |
| U | 0.047 | Eu | 1.02 |
| Nb | 2.33 | Gd | 3.68 |
| Ta | 0.132 | Yb | 3.05 |
| K | 600 | Lu | 0.455 |

## Usage Examples

### Get Reference Composition
```python
from pyrolite.geochem.norm import get_reference_composition

# Get reference
chondrite = get_reference_composition('Chondrite_McDonough1995')
pm = get_reference_composition('PM_McDonough1995')

# View available elements
print(chondrite.index.tolist())
```

### List All Available References
```python
from pyrolite.geochem.norm import all_reference_compositions

# Get all available reference names
refs = all_reference_compositions()
print(refs)
```

### Normalize Data
```python
import pandas as pd
from pyrolite.geochem.norm import get_reference_composition

df = pd.read_csv('samples.csv')
chondrite = get_reference_composition('Chondrite_McDonough1995')

# Normalize REE data
df_norm = df.pyrochem.normalize_to(chondrite, units='ppm')
```

### Compare Multiple Normalizations
```python
import matplotlib.pyplot as plt
from pyrolite.geochem.norm import get_reference_composition

# Get different references
chond_mc = get_reference_composition('Chondrite_McDonough1995')
chond_bo = get_reference_composition('Chondrite_Boynton1984')

# Plot comparison
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

df.pyrochem.normalize_to(chond_mc, units='ppm').pyroplot.REE(ax=axes[0])
axes[0].set_title('McDonough 1995')

df.pyrochem.normalize_to(chond_bo, units='ppm').pyroplot.REE(ax=axes[1])
axes[1].set_title('Boynton 1984')
```

## Choosing Normalization

| Rock Type | Recommended Reference |
|-----------|----------------------|
| Any rock (REE only) | Chondrite_McDonough1995 |
| Mantle-derived (spider) | PM_McDonough1995 |
| Ocean basalts | NMORB_SunMcDonough1989 |
| Crustal rocks | UCC_RudnickGao2003 |
| Sedimentary | PAAS_TaylorMcLennan1985 |
| Arc volcanics | PM or NMORB |

## Key References

- McDonough, W.F., Sun, S.-S. (1995). The composition of the Earth. Chemical Geology, 120, 223-253.
- Sun, S.-S., McDonough, W.F. (1989). Chemical and isotopic systematics of oceanic basalts. Geological Society, London, Special Publications, 42, 313-345.
- Rudnick, R.L., Gao, S. (2003). Composition of the Continental Crust. Treatise on Geochemistry, 3, 1-64.
- Taylor, S.R., McLennan, S.M. (1985). The Continental Crust: Its Composition and Evolution. Blackwell Scientific, Oxford.
