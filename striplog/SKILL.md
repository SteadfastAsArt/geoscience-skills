---
name: striplog
description: Lithological and stratigraphic log display. Create, visualize, and analyze well logs showing rock types, formations, and core descriptions.
---

# Striplog - Lithological Logs

Help users create and visualize lithological and stratigraphic logs.

## Installation

```bash
pip install striplog
```

## Core Concepts

### What Striplog Does
- Display lithological logs from wells
- Represent rock types with patterns and colors
- Handle intervals (from-to depths)
- Well correlation
- Extract statistics from logs

### Key Classes
| Class | Purpose |
|-------|---------|
| `Striplog` | Main log container |
| `Interval` | Depth interval with properties |
| `Component` | Rock type definition |
| `Lexicon` | Rock type dictionary |
| `Legend` | Visualization styles |

## Common Workflows

### 1. Create Simple Striplog
```python
from striplog import Striplog, Interval, Component

# Define intervals
intervals = [
    Interval(top=0, base=10, components=[Component({'lithology': 'sandstone'})]),
    Interval(top=10, base=25, components=[Component({'lithology': 'shale'})]),
    Interval(top=25, base=40, components=[Component({'lithology': 'limestone'})]),
    Interval(top=40, base=50, components=[Component({'lithology': 'sandstone'})]),
]

# Create striplog
strip = Striplog(intervals)

# Display
print(strip)
strip.plot()
```

### 2. Load from CSV
```python
from striplog import Striplog
import pandas as pd

# CSV format: top, base, lithology
csv_data = """top,base,lithology
0,10,sandstone
10,25,shale
25,40,limestone
40,50,sandstone"""

# Save to file
with open('lithology.csv', 'w') as f:
    f.write(csv_data)

# Load striplog
strip = Striplog.from_csv('lithology.csv')
strip.plot()
```

### 3. Load from LAS File
```python
from striplog import Striplog
import lasio

# Load LAS file
las = lasio.read('well.las')

# If LAS has lithology curve (categorical)
# Create striplog from categorical log
# This requires preprocessing the LAS data

# For interval-based data in LAS
strip = Striplog.from_las('lithology.las', lexicon=lexicon)
```

### 4. Create Custom Legend
```python
from striplog import Striplog, Legend, Decor

# Define decorations for rock types
decors = [
    Decor({
        'component': 'sandstone',
        'colour': '#FFFF00',
        'hatch': '...',
        'width': 3
    }),
    Decor({
        'component': 'shale',
        'colour': '#808080',
        'hatch': '---',
        'width': 3
    }),
    Decor({
        'component': 'limestone',
        'colour': '#00BFFF',
        'hatch': '+++',
        'width': 3
    }),
]

legend = Legend(decors)

# Plot with legend
strip.plot(legend=legend)
```

### 5. Using a Lexicon
```python
from striplog import Lexicon, Striplog

# Define lexicon (rock type synonyms and properties)
lexicon_dict = {
    'lithology': {
        'sandstone': {
            'synonyms': ['sand', 'ss', 'sst', 'sandst'],
            'colour': '#FFFF00',
            'hatch': '...'
        },
        'shale': {
            'synonyms': ['sh', 'clay', 'mudstone'],
            'colour': '#808080',
            'hatch': '---'
        },
        'limestone': {
            'synonyms': ['ls', 'lime', 'calcaire'],
            'colour': '#00BFFF',
            'hatch': '+++'
        }
    }
}

lexicon = Lexicon(lexicon_dict)

# Use lexicon to interpret descriptions
text = "0-10: sand, 10-25: sh, 25-40: ls"
strip = Striplog.from_description(text, lexicon=lexicon)
```

### 6. Striplog from Description Text
```python
from striplog import Striplog

# Parse geological description
description = """
0.0 - 5.5 m: Fine to medium sandstone, well sorted
5.5 - 12.0 m: Grey shale with thin silt laminations
12.0 - 18.5 m: Massive limestone, fossiliferous
18.5 - 25.0 m: Interbedded sandstone and shale
"""

strip = Striplog.from_description(description)
print(strip)
```

### 7. Extract Statistics
```python
from striplog import Striplog

# After creating striplog
strip = Striplog.from_csv('lithology.csv')

# Total thickness by lithology
for lith in ['sandstone', 'shale', 'limestone']:
    thickness = strip.net_to_gross(pattern={'lithology': lith})
    print(f"{lith}: {thickness * strip.stop:.1f} m")

# Number of intervals
print(f"Total intervals: {len(strip)}")

# Get all unique lithologies
lithologies = strip.unique('lithology')
print(f"Lithologies: {lithologies}")
```

### 8. Merge Adjacent Intervals
```python
from striplog import Striplog

strip = Striplog.from_csv('lithology.csv')

# Merge adjacent intervals with same lithology
merged = strip.merge_neighbours()

print(f"Before merge: {len(strip)} intervals")
print(f"After merge: {len(merged)} intervals")
```

### 9. Extract Depth Range
```python
from striplog import Striplog

strip = Striplog.from_csv('lithology.csv')

# Extract subset by depth
subset = strip.read_at(
    z=15,              # Or z=(10, 30) for range
    return_interval=False
)

# Get interval at specific depth
interval = strip.read_at(z=15)
print(f"At 15m: {interval}")

# Crop to depth range
cropped = strip.crop((10, 30))
```

### 10. Well Correlation
```python
from striplog import Striplog
import matplotlib.pyplot as plt

# Create multiple wells
well1 = Striplog.from_csv('well1_lith.csv')
well2 = Striplog.from_csv('well2_lith.csv')
well3 = Striplog.from_csv('well3_lith.csv')

# Plot side by side
fig, axes = plt.subplots(1, 3, figsize=(10, 8), sharey=True)

well1.plot(ax=axes[0], legend=legend)
axes[0].set_title('Well 1')

well2.plot(ax=axes[1], legend=legend)
axes[1].set_title('Well 2')

well3.plot(ax=axes[2], legend=legend)
axes[2].set_title('Well 3')

plt.tight_layout()
plt.show()
```

### 11. Add Components to Intervals
```python
from striplog import Striplog, Interval, Component

# Create interval with multiple properties
comp = Component({
    'lithology': 'sandstone',
    'grain_size': 'medium',
    'porosity': 0.25,
    'colour': 'yellow',
    'notes': 'Well sorted, oil shows'
})

interval = Interval(top=0, base=10, components=[comp])

# Access properties
print(interval.primary.lithology)
print(interval.primary.porosity)
```

### 12. Export Striplog
```python
from striplog import Striplog

strip = Striplog.from_csv('lithology.csv')

# Export to CSV
strip.to_csv('output.csv')

# Export to LAS
strip.to_las('output.las')

# Export to JSON
strip.to_json('output.json')

# Get as DataFrame
df = strip.to_dataframe()
print(df)
```

## Component Properties

Common properties for geological components:
- `lithology` - Rock type
- `grain_size` - Fine, medium, coarse
- `colour` - Rock color
- `porosity` - Porosity value
- `permeability` - Permeability value
- `age` - Geological age
- `formation` - Formation name

## Hatch Patterns

| Pattern | Code | Description |
|---------|------|-------------|
| Dots | `...` | Sandstone |
| Dashes | `---` | Shale |
| Plus | `+++` | Limestone |
| X | `xxx` | Dolomite |
| V | `vvv` | Volcanic |

## Tips

1. **Use lexicons** for consistent rock type mapping
2. **Define legends** for publication-quality plots
3. **Merge neighbours** to simplify logs
4. **Use components** for multi-attribute intervals
5. **Export to DataFrame** for analysis with pandas

## Resources

- Documentation: https://striplog.readthedocs.io/
- GitHub: https://github.com/agilescientific/striplog
- Tutorials: https://github.com/agile-geoscience/notebooks
