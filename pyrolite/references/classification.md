# Geochemical Classification Schemes

## Table of Contents
- [TAS Diagram](#tas-diagram)
- [Pearce Discrimination Diagrams](#pearce-discrimination-diagrams)
- [AFM Diagram](#afm-diagram)
- [Other Classification Diagrams](#other-classification-diagrams)
- [Discrimination Indices](#discrimination-indices)

## TAS Diagram

Total Alkali-Silica diagram for volcanic rock classification (Le Bas et al., 1986).

### Usage
```python
from pyrolite.plot.templates import TAS
import matplotlib.pyplot as plt

df['Na2O_K2O'] = df['Na2O'] + df['K2O']

ax = TAS()
ax.scatter(df['SiO2'], df['Na2O_K2O'], c='red', s=50)
plt.title('Total Alkali-Silica Classification')
plt.show()
```

### TAS Classification Fields

| Field | SiO2 Range | Na2O+K2O Range |
|-------|------------|----------------|
| Foidite | <45% | >6% |
| Picrobasalt | <45% | <2% |
| Basanite/Tephrite | 41-45% | 3-6% |
| Basalt | 45-52% | <5% |
| Trachybasalt | 45-52% | 5-7% |
| Basaltic andesite | 52-57% | <5% |
| Basaltic trachyandesite | 52-57% | 5-7% |
| Andesite | 57-63% | <6% |
| Trachyandesite | 57-63% | 6-8% |
| Dacite | 63-69% | <7% |
| Trachydacite | 63-69% | 7-9% |
| Rhyolite | >69% | <8% |
| Trachyte | 63-69% | 9-12% |

### Alkaline vs Subalkaline
```python
# Irvine-Baragar line separates alkaline from subalkaline
def is_alkaline(sio2, na2o_k2o):
    """Returns True if sample plots in alkaline field."""
    boundary = 0.37 + 0.14 * sio2 - 0.002 * sio2**2
    return na2o_k2o > boundary
```

## Pearce Discrimination Diagrams

Tectonic discrimination diagrams for granites and basalts.

### Y-Nb Diagram (Pearce et al., 1984)
```python
from pyrolite.plot.templates import pearce_templates

ax = pearce_templates.YNb()
ax.scatter(df['Nb'], df['Y'], c='red', s=50, label='Samples')
plt.legend()
```

### Y+Nb vs Rb Diagram
```python
ax = pearce_templates.YNbRb()
df['Y_Nb'] = df['Y'] + df['Nb']
ax.scatter(df['Y_Nb'], df['Rb'], c='red', s=50)
```

### Pearce Fields

| Field | Abbreviation | Description |
|-------|--------------|-------------|
| Volcanic Arc | VAG | Subduction-related |
| Within-Plate | WPG | Intraplate/hotspot |
| Ocean Ridge | ORG | Mid-ocean ridge |
| Syn-Collision | syn-COLG | Collision zones |
| Post-Collision | post-COLG | Post-collisional |

### Manual Pearce Fields
```python
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots()

# Y vs Nb discrimination
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlim(1, 1000)
ax.set_ylim(1, 1000)

# VAG + syn-COLG field
ax.axhline(y=50, color='gray', linestyle='--')
ax.axvline(x=50, color='gray', linestyle='--')

ax.scatter(df['Nb'], df['Y'], c='red', s=50)
ax.set_xlabel('Nb (ppm)')
ax.set_ylabel('Y (ppm)')
```

## AFM Diagram

Ternary diagram showing iron enrichment trends.

### Usage
```python
import matplotlib.pyplot as plt

# Calculate AFM components
df['A'] = df['Na2O'] + df['K2O']
df['F'] = df['FeO'] + df['Fe2O3'] * 0.8998  # Convert Fe2O3 to FeO
df['M'] = df['MgO']

# Normalize to 100%
total = df['A'] + df['F'] + df['M']
df['A_norm'] = df['A'] / total * 100
df['F_norm'] = df['F'] / total * 100
df['M_norm'] = df['M'] / total * 100

# Plot ternary
df[['A_norm', 'F_norm', 'M_norm']].pyroplot.scatter()
```

### Tholeiitic vs Calc-Alkaline
The Kuno line and Irvine-Baragar line separate tholeiitic (Fe-enrichment) from calc-alkaline (no Fe-enrichment) series.

## Other Classification Diagrams

### Jensen Cation Plot
For metamorphosed volcanic rocks using cation proportions.
```python
# Calculate cation proportions
df['Al_cat'] = df['Al2O3'] / 101.96 * 2
df['Fe_cat'] = df['FeO'] / 71.85 + df['Fe2O3'] / 159.69 * 2 + df['TiO2'] / 79.87
df['Mg_cat'] = df['MgO'] / 40.30
```

### Winchester-Floyd (1977)
For altered volcanic rocks using immobile elements.
```python
# Nb/Y vs Zr/TiO2 diagram
df['Nb_Y'] = df['Nb'] / df['Y']
df['Zr_Ti'] = df['Zr'] / (df['TiO2'] * 10000)

plt.scatter(df['Zr_Ti'], df['Nb_Y'])
plt.xlabel('Zr/TiO2 (x 0.0001)')
plt.ylabel('Nb/Y')
plt.xscale('log')
plt.yscale('log')
```

### Th-Hf-Ta Diagram (Wood, 1980)
For basalt tectonic discrimination.
```python
# Ternary: Th - Hf/3 - Ta
df['Th_plot'] = df['Th']
df['Hf_plot'] = df['Hf'] / 3
df['Ta_plot'] = df['Ta']
```

## Discrimination Indices

### Mg Number
```python
# Mg# = Mg / (Mg + Fe) in molar proportions
df['Mg_mol'] = df['MgO'] / 40.30
df['Fe_mol'] = df['FeO'] / 71.85
df['Mg#'] = df['Mg_mol'] / (df['Mg_mol'] + df['Fe_mol']) * 100
```

### Aluminum Saturation Index (ASI)
```python
# ASI = Al / (Ca + Na + K) in molar proportions
df['Al_mol'] = df['Al2O3'] / 101.96 * 2
df['Ca_mol'] = df['CaO'] / 56.08
df['Na_mol'] = df['Na2O'] / 61.98 * 2
df['K_mol'] = df['K2O'] / 94.20 * 2
df['ASI'] = df['Al_mol'] / (df['Ca_mol'] + df['Na_mol'] + df['K_mol'])
```

| ASI Value | Classification |
|-----------|---------------|
| < 1.0 | Metaluminous |
| 1.0 - 1.1 | Weakly peraluminous |
| > 1.1 | Strongly peraluminous |

### Agpaitic Index (AI)
```python
# AI = (Na + K) / Al in molar proportions
df['AI'] = (df['Na_mol'] + df['K_mol']) / df['Al_mol']
```

| AI Value | Classification |
|----------|---------------|
| < 1.0 | Subaluminous/Metaluminous |
| > 1.0 | Peralkaline |

### Fe Index
```python
# FeOt / (FeOt + MgO) - distinguishes tholeiitic from calc-alkaline
df['FeOt'] = df['FeO'] + df['Fe2O3'] * 0.8998
df['Fe_index'] = df['FeOt'] / (df['FeOt'] + df['MgO'])
```

### MALI (Modified Alkali-Lime Index)
```python
# MALI = Na2O + K2O - CaO
df['MALI'] = df['Na2O'] + df['K2O'] - df['CaO']
```

| MALI at 70% SiO2 | Classification |
|------------------|---------------|
| < -8 | Calcic |
| -8 to -2 | Calc-alkalic |
| -2 to +4 | Alkali-calcic |
| > +4 | Alkalic |

## Key References

- Le Bas, M.J., et al. (1986). A chemical classification of volcanic rocks based on the total alkali-silica diagram. Journal of Petrology, 27, 745-750.
- Pearce, J.A., et al. (1984). Trace element discrimination diagrams for the tectonic interpretation of granitic rocks. Journal of Petrology, 25, 956-983.
- Winchester, J.A., Floyd, P.A. (1977). Geochemical discrimination of different magma series and their differentiation products using immobile elements. Chemical Geology, 20, 325-343.
- Wood, D.A. (1980). The application of a Th-Hf-Ta diagram to problems of tectonomagmatic classification. Earth and Planetary Science Letters, 50, 11-30.
- Frost, B.R., et al. (2001). A geochemical classification for granitic rocks. Journal of Petrology, 42, 2033-2048.
