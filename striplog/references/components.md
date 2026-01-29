# Component Definitions

Components define rock types and their properties within intervals. Each interval can have one or more components.

## Table of Contents
- [Basic Components](#basic-components)
- [Multi-Property Components](#multi-property-components)
- [Accessing Component Data](#accessing-component-data)
- [Multiple Components per Interval](#multiple-components-per-interval)
- [Common Properties](#common-properties)

## Basic Components

```python
from striplog import Component

# Simple component with lithology only
comp = Component({'lithology': 'sandstone'})

# Access properties
print(comp.lithology)  # 'sandstone'
```

## Multi-Property Components

```python
from striplog import Component

# Component with multiple properties
comp = Component({
    'lithology': 'sandstone',
    'grain_size': 'medium',
    'sorting': 'well sorted',
    'colour': 'yellow',
    'porosity': 0.25,
    'permeability': 500,  # mD
    'formation': 'Wilcox',
    'age': 'Eocene',
    'notes': 'Oil shows at 1520m'
})

# Access any property as attribute
print(comp.lithology)      # 'sandstone'
print(comp.grain_size)     # 'medium'
print(comp.porosity)       # 0.25
```

## Creating Intervals with Components

```python
from striplog import Interval, Component

# Single component interval
comp = Component({'lithology': 'sandstone', 'grain_size': 'fine'})
interval = Interval(top=0, base=10, components=[comp])

# Access primary component
print(interval.primary.lithology)
print(interval.primary.grain_size)
```

## Accessing Component Data

```python
from striplog import Striplog, Interval, Component

# Create striplog
intervals = [
    Interval(top=0, base=10, components=[
        Component({'lithology': 'sandstone', 'porosity': 0.22})
    ]),
    Interval(top=10, base=20, components=[
        Component({'lithology': 'shale', 'porosity': 0.05})
    ]),
]
strip = Striplog(intervals)

# Access via interval
for interval in strip:
    print(f"{interval.top}-{interval.base}m: {interval.primary.lithology}")

# Get all values for a property
lithologies = strip.unique('lithology')
print(lithologies)  # ['sandstone', 'shale']
```

## Multiple Components per Interval

Use multiple components for mixed lithologies or interbedded sequences:

```python
from striplog import Interval, Component

# Interbedded sandstone and shale
comp1 = Component({'lithology': 'sandstone', 'proportion': 0.7})
comp2 = Component({'lithology': 'shale', 'proportion': 0.3})

interval = Interval(
    top=100,
    base=150,
    components=[comp1, comp2],
    description='Interbedded sandstone and shale'
)

# Access components
print(interval.primary)    # First component (sandstone)
print(interval.components) # All components

# Iterate through components
for comp in interval.components:
    print(f"{comp.lithology}: {comp.proportion * 100}%")
```

## Common Properties

### Lithology Properties

| Property | Example Values | Description |
|----------|----------------|-------------|
| `lithology` | sandstone, shale, limestone | Rock type |
| `grain_size` | clay, silt, vf, f, m, c, vc | Grain size class |
| `sorting` | well, moderate, poor | Sorting description |
| `rounding` | angular, subangular, rounded | Grain rounding |
| `colour` | grey, brown, yellow | Visual color |
| `hardness` | soft, firm, hard | Induration |

### Reservoir Properties

| Property | Unit | Description |
|----------|------|-------------|
| `porosity` | V/V (0-1) | Porosity fraction |
| `permeability` | mD | Permeability |
| `saturation` | V/V (0-1) | Water saturation |
| `net_pay` | bool | Net pay flag |

### Stratigraphic Properties

| Property | Example Values | Description |
|----------|----------------|-------------|
| `formation` | Wilcox, Austin Chalk | Formation name |
| `member` | Lower Wilcox | Member name |
| `age` | Eocene, Cretaceous | Geological age |
| `environment` | fluvial, marine | Depositional environment |

### Descriptive Properties

| Property | Description |
|----------|-------------|
| `description` | Free text description |
| `notes` | Additional observations |
| `shows` | Hydrocarbon shows |
| `fossils` | Fossil content |

## Building Striplogs from Data

```python
import pandas as pd
from striplog import Striplog, Interval, Component

# From DataFrame with multiple columns
data = pd.DataFrame({
    'top': [0, 10, 25, 40],
    'base': [10, 25, 40, 60],
    'lithology': ['sandstone', 'shale', 'limestone', 'sandstone'],
    'porosity': [0.22, 0.05, 0.15, 0.20],
    'grain_size': ['medium', 'clay', 'n/a', 'fine']
})

intervals = []
for _, row in data.iterrows():
    comp = Component({
        'lithology': row['lithology'],
        'porosity': row['porosity'],
        'grain_size': row['grain_size']
    })
    interval = Interval(top=row['top'], base=row['base'], components=[comp])
    intervals.append(interval)

strip = Striplog(intervals)
```

## Filtering by Component Properties

```python
# Find intervals matching criteria
sand_intervals = [i for i in strip if i.primary.lithology == 'sandstone']

# Net-to-gross with pattern matching
ntg = strip.net_to_gross(pattern={'lithology': 'sandstone'})

# Filter by multiple criteria
reservoir = [
    i for i in strip
    if i.primary.lithology == 'sandstone'
    and getattr(i.primary, 'porosity', 0) > 0.15
]
```

## Component Summary Statistics

```python
# Get statistics by lithology
from collections import defaultdict

stats = defaultdict(lambda: {'thickness': 0, 'count': 0})

for interval in strip:
    lith = interval.primary.lithology
    thickness = interval.base - interval.top
    stats[lith]['thickness'] += thickness
    stats[lith]['count'] += 1

for lith, data in stats.items():
    print(f"{lith}: {data['thickness']:.1f}m in {data['count']} intervals")
```

## Tips

1. **Use primary** - `interval.primary` returns the first (main) component
2. **Check existence** - Use `getattr(comp, 'property', default)` for optional properties
3. **Keep consistent** - Use same property names across all components
4. **Numeric values** - Store porosity/permeability as numbers for calculations
5. **Lists work** - Components list can have any number of Component objects
