---
name: pyrolite
description: Geochemistry data analysis and visualization. Create ternary diagrams, spider plots, REE patterns, and perform compositional data analysis.
---

# pyrolite - Geochemistry Analysis

Help users analyze and visualize geochemical data.

## Installation

```bash
pip install pyrolite
```

## Core Concepts

### What pyrolite Does
- Compositional data handling
- Ternary and spider diagrams
- REE normalization
- Element ratio calculations
- Classification diagrams

### Key Modules
| Module | Purpose |
|--------|---------|
| `pyrolite.comp` | Compositional transforms |
| `pyrolite.plot` | Geochemical plots |
| `pyrolite.geochem` | Normalization, lambdas |
| `pyrolite.mineral` | Mineral calculations |

## Common Workflows

### 1. Load and Prepare Data
```python
import pandas as pd
import pyrolite

# Load geochemical data
df = pd.read_csv('rock_samples.csv')

# View columns
print(df.columns)

# Basic statistics
print(df.describe())

# Access pyrolite accessor
print(df.pyrochem)  # Geochemistry methods
print(df.pyrocomp)  # Compositional methods
```

### 2. Ternary Diagram
```python
import pandas as pd
import matplotlib.pyplot as plt
from pyrolite.plot import pyroplot

# Sample data
df = pd.DataFrame({
    'SiO2': [50, 55, 60, 65, 70],
    'Na2O': [3, 3.5, 4, 4.5, 5],
    'K2O': [1, 1.5, 2, 2.5, 3],
    'CaO': [8, 7, 6, 5, 4]
})

# Create ternary plot
ax = df[['SiO2', 'CaO', 'Na2O']].pyroplot.scatter(
    c='k',
    s=50,
    alpha=0.7
)
plt.title('SiO2-CaO-Na2O Ternary')
plt.show()
```

### 3. TAS Diagram (Total Alkali-Silica)
```python
import pandas as pd
import matplotlib.pyplot as plt
from pyrolite.plot.templates import TAS

# Rock data
df = pd.DataFrame({
    'SiO2': [45, 50, 55, 60, 65, 70, 75],
    'Na2O': [2, 3, 3.5, 4, 4.5, 5, 5],
    'K2O': [0.5, 1, 1.5, 2, 2.5, 3, 3.5]
})

# Calculate total alkalis
df['Na2O_K2O'] = df['Na2O'] + df['K2O']

# Create TAS diagram
ax = TAS()
ax.scatter(df['SiO2'], df['Na2O_K2O'], c='red', s=50)
plt.title('Total Alkali-Silica Diagram')
plt.show()
```

### 4. Spider Diagram (Trace Elements)
```python
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pyrolite.geochem.norm import get_reference_composition

# Trace element data (ppm)
df = pd.DataFrame({
    'Rb': [50, 60, 70],
    'Ba': [300, 350, 400],
    'Th': [5, 6, 7],
    'U': [1.5, 2, 2.5],
    'Nb': [10, 12, 14],
    'La': [20, 25, 30],
    'Ce': [45, 50, 55],
    'Nd': [22, 25, 28],
    'Sm': [5, 5.5, 6],
    'Eu': [1.2, 1.3, 1.4],
    'Gd': [4.5, 5, 5.5],
    'Yb': [2, 2.2, 2.4],
    'Lu': [0.3, 0.35, 0.4]
})

# Normalize to primitive mantle
norm = get_reference_composition('PM_McDonough1995')

# Create spider diagram
ax = df.pyrochem.normalize_to(norm).pyroplot.spider(
    unity_line=True,
    color=['red', 'blue', 'green']
)
plt.title('Primitive Mantle Normalized Spider Diagram')
plt.show()
```

### 5. REE Pattern
```python
import pandas as pd
import matplotlib.pyplot as plt
from pyrolite.geochem.norm import get_reference_composition

# REE data (ppm)
df = pd.DataFrame({
    'La': [25, 30, 35],
    'Ce': [55, 60, 70],
    'Pr': [6.5, 7, 8],
    'Nd': [26, 28, 32],
    'Sm': [5.5, 6, 7],
    'Eu': [1.5, 1.6, 1.8],
    'Gd': [5, 5.5, 6],
    'Tb': [0.8, 0.9, 1],
    'Dy': [4.5, 5, 5.5],
    'Ho': [0.9, 1, 1.1],
    'Er': [2.5, 2.8, 3],
    'Tm': [0.35, 0.4, 0.45],
    'Yb': [2.2, 2.5, 2.8],
    'Lu': [0.32, 0.36, 0.4]
})

# Normalize to chondrite
chondrite = get_reference_composition('Chondrite_McDonough1995')

# Plot REE pattern
ax = df.pyrochem.normalize_to(chondrite, units='ppm').pyroplot.REE(
    unity_line=True
)
plt.title('Chondrite-Normalized REE Pattern')
plt.show()
```

### 6. Harker Diagrams
```python
import pandas as pd
import matplotlib.pyplot as plt

# Major element data
df = pd.DataFrame({
    'SiO2': [45, 50, 55, 60, 65, 70, 75],
    'TiO2': [2.5, 2, 1.5, 1, 0.7, 0.5, 0.3],
    'Al2O3': [14, 15, 16, 16, 15, 14, 13],
    'FeO': [12, 10, 8, 6, 4, 2.5, 1.5],
    'MgO': [8, 6, 4, 3, 2, 1, 0.5],
    'CaO': [10, 9, 7, 5, 4, 3, 2],
    'Na2O': [2, 2.5, 3, 3.5, 4, 4.5, 5],
    'K2O': [0.5, 1, 1.5, 2, 2.5, 3, 4]
})

# Create Harker diagram grid
fig, axes = plt.subplots(2, 3, figsize=(12, 8))
axes = axes.flatten()

elements = ['TiO2', 'Al2O3', 'FeO', 'MgO', 'CaO', 'Na2O']

for ax, elem in zip(axes, elements):
    ax.scatter(df['SiO2'], df[elem], c='blue', s=50)
    ax.set_xlabel('SiO2 (wt%)')
    ax.set_ylabel(f'{elem} (wt%)')

plt.tight_layout()
plt.suptitle('Harker Diagrams', y=1.02)
plt.show()
```

### 7. Compositional Transforms
```python
import pandas as pd
import numpy as np

# Compositional data (must sum to 100%)
df = pd.DataFrame({
    'SiO2': [50, 55, 60],
    'Al2O3': [15, 16, 17],
    'FeO': [10, 8, 6],
    'MgO': [8, 6, 4],
    'CaO': [10, 9, 8],
    'Na2O': [4, 4, 3],
    'K2O': [3, 2, 2]
})

# Closure (ensure sums to 100%)
df_closed = df.pyrocomp.renormalise(scale=100)

# Log-ratio transforms
df_clr = df.pyrocomp.CLR()  # Centered log-ratio
df_alr = df.pyrocomp.ALR()  # Additive log-ratio
df_ilr = df.pyrocomp.ILR()  # Isometric log-ratio

print("CLR transformed:")
print(df_clr.head())
```

### 8. Element Ratios
```python
import pandas as pd

df = pd.DataFrame({
    'Rb': [50, 60, 70],
    'Sr': [300, 350, 400],
    'Ba': [400, 450, 500],
    'Th': [5, 6, 7],
    'U': [1.5, 2, 2.5],
    'La': [20, 25, 30],
    'Yb': [2, 2.2, 2.4]
})

# Calculate ratios
df['Rb_Sr'] = df['Rb'] / df['Sr']
df['Th_U'] = df['Th'] / df['U']
df['La_Yb'] = df['La'] / df['Yb']  # LREE/HREE

# Or use lambda functions for complex ratios
df['Eu_Eu*'] = df['Eu'] / (df['Sm'] * df['Gd']) ** 0.5  # Eu anomaly

print(df[['Rb_Sr', 'Th_U', 'La_Yb']])
```

### 9. Classification Diagrams
```python
import pandas as pd
import matplotlib.pyplot as plt
from pyrolite.plot.templates import pearce_templates

# Trace element data
df = pd.DataFrame({
    'Y': [20, 25, 30, 35],
    'Nb': [5, 10, 15, 20],
    'Rb': [50, 100, 150, 200],
    'Yb': [2, 2.5, 3, 3.5],
    'Ta': [0.5, 1, 1.5, 2]
})

# Y-Nb diagram for tectonic discrimination
ax = pearce_templates.YNb()
ax.scatter(df['Nb'], df['Y'], c='red', s=50)
plt.title('Y-Nb Tectonic Discrimination')
plt.show()
```

### 10. Mineral Recalculation
```python
import pandas as pd
from pyrolite.mineral.normative import CIPW_norm

# Whole rock analysis (wt%)
df = pd.DataFrame({
    'SiO2': [50.5],
    'TiO2': [1.5],
    'Al2O3': [15.2],
    'Fe2O3': [2.5],
    'FeO': [8.5],
    'MnO': [0.15],
    'MgO': [7.2],
    'CaO': [10.5],
    'Na2O': [2.8],
    'K2O': [0.8],
    'P2O5': [0.25]
})

# Calculate CIPW norm
norm = CIPW_norm(df)
print(norm)
```

### 11. Lambda Coefficients (REE Shape)
```python
import pandas as pd
from pyrolite.geochem.ind import get_ionic_radii
import numpy as np

# REE data
df = pd.DataFrame({
    'La': [25], 'Ce': [55], 'Pr': [6.5], 'Nd': [26],
    'Sm': [5.5], 'Eu': [1.5], 'Gd': [5], 'Tb': [0.8],
    'Dy': [4.5], 'Ho': [0.9], 'Er': [2.5], 'Tm': [0.35],
    'Yb': [2.2], 'Lu': [0.32]
})

# Calculate lambda coefficients
# λ0: overall enrichment
# λ1: LREE/HREE slope
# λ2: curvature (MREE anomaly)

lambdas = df.pyrochem.lambda_lnREE()
print(lambdas)
```

### 12. Export Plots
```python
import pandas as pd
import matplotlib.pyplot as plt

# Create and save publication-quality figure
df = pd.DataFrame({...})

fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
df.pyroplot.spider(ax=ax, unity_line=True)
ax.set_title('Spider Diagram')

plt.savefig('spider_diagram.png', dpi=300, bbox_inches='tight')
plt.savefig('spider_diagram.pdf', bbox_inches='tight')
```

## Normalization References

| Reference | Code |
|-----------|------|
| Chondrite (McDonough 1995) | `Chondrite_McDonough1995` |
| Primitive Mantle | `PM_McDonough1995` |
| MORB | `NMORB_SunMcDonough1989` |
| Continental Crust | `UCC_RudnickGao2003` |

## Common Diagrams

| Diagram | Purpose |
|---------|---------|
| TAS | Rock classification |
| Harker | Major element variation |
| Spider | Trace element patterns |
| REE | Rare earth patterns |
| Ternary | Three-component systems |

## Tips

1. **Close compositions** before analysis (sum to 100%)
2. **Use log-ratios** for statistical analysis
3. **Normalize to appropriate reference** for spider diagrams
4. **Check for Eu anomaly** in REE patterns
5. **Consider analytical uncertainty** in interpretation

## Resources

- Documentation: https://pyrolite.readthedocs.io/
- GitHub: https://github.com/morganjwilliams/pyrolite
- Tutorials: https://pyrolite.readthedocs.io/en/main/tutorials/
