# Structural Relations Guide

## Table of Contents
- [Overview](#overview)
- [ERODE Relation](#erode-relation)
- [ONLAP Relation](#onlap-relation)
- [FAULT Relation](#fault-relation)
- [INTRUSION Relation](#intrusion-relation)
- [Ordering and Stacking](#ordering-and-stacking)

## Overview

Structural relations define how different geological units interact with each other. In GemPy, these are set using `StackRelationType` on structural groups.

```python
import gempy as gp

# Access structural relation
geo_model.structural_frame.structural_groups[0].structural_relation = \
    gp.data.StackRelationType.ERODE
```

## ERODE Relation

Used for unconformities where younger units truncate older ones.

### When to Use
- Erosional unconformities
- Angular unconformities
- Disconformities
- Any surface that cuts through underlying geology

### Example
```python
gp.map_stack_to_surfaces(
    geo_model,
    mapping={
        'Post_Unconformity': ['Unit_A', 'Unit_B'],  # Younger
        'Pre_Unconformity': ['Unit_C', 'Unit_D'],   # Older
    }
)

# Set Post_Unconformity to erode Pre_Unconformity
geo_model.structural_frame.structural_groups[0].structural_relation = \
    gp.data.StackRelationType.ERODE
```

### Visualization
```
Before erosion:          After erosion:
+------------------+     +------------------+
|     Unit_A       |     |     Unit_A       |
+------------------+     +------------------+
|     Unit_B       |     |     Unit_B       |
+~~~~~~~~~~~~~~~~~~+     +~~~~~~~~~~~~~~~~~~+
|   / Unit_C  \    |     |   Eroded by B    |
|  /  Unit_D   \   |     |                  |
+------------------+     +------------------+
```

## ONLAP Relation

Used when younger units deposit against and terminate at older surfaces.

### When to Use
- Sedimentary onlap sequences
- Transgressive deposits
- Basin fill sequences
- Pinch-outs against paleotopography

### Example
```python
gp.map_stack_to_surfaces(
    geo_model,
    mapping={
        'Onlapping_Sequence': ['Sed_1', 'Sed_2'],
        'Basement': ['Basement_Surface'],
    }
)

# Set onlap relation
geo_model.structural_frame.structural_groups[0].structural_relation = \
    gp.data.StackRelationType.ONLAP
```

### Visualization
```
ONLAP geometry:
+---------------------------+
|          Sed_2            |
|    +------------------+   |
|    |      Sed_1       |   |
|  +-+              +---+   |
|  |    Basement    |       |
+--+----------------+-------+
   Onlap terminations
```

## FAULT Relation

Used for fault surfaces that offset other geological units.

### When to Use
- Normal faults
- Reverse/thrust faults
- Strike-slip faults
- Any discontinuity that offsets stratigraphy

### Example
```python
# Add fault surface points and orientations
gp.add_surface_points(
    geo_model,
    x=[500, 500, 500],
    y=[200, 500, 800],
    z=[100, 250, 400],
    surface='Main_Fault'
)

gp.add_orientations(
    geo_model,
    x=[500], y=[500], z=[250],
    pole_vector=[1, 0, 0.3],  # Dipping fault plane
    surface='Main_Fault'
)

# Map fault to its own series
gp.map_stack_to_surfaces(
    geo_model,
    mapping={
        'Fault_Series': ['Main_Fault'],
        'Stratigraphy': ['Unit_A', 'Unit_B', 'Unit_C'],
    }
)

# Set as fault
geo_model.structural_frame.structural_groups[0].structural_relation = \
    gp.data.StackRelationType.FAULT
```

### Fault Ordering

Multiple faults must be ordered correctly (youngest first):

```python
gp.map_stack_to_surfaces(
    geo_model,
    mapping={
        'Fault_2': ['Fault_Young'],    # Youngest fault first
        'Fault_1': ['Fault_Old'],      # Older fault second
        'Stratigraphy': ['A', 'B', 'C'],
    }
)
```

### Pole Vector Guidelines

| Fault Type | Pole Vector Direction |
|------------|----------------------|
| Vertical E-W strike | [1, 0, 0] |
| Vertical N-S strike | [0, 1, 0] |
| 60 deg dip to east | [0.87, 0, 0.5] |
| 45 deg dip to north | [0, 0.71, 0.71] |

## INTRUSION Relation

Used for igneous intrusions that crosscut existing geology.

### When to Use
- Plutons
- Dikes and sills
- Volcanic plugs
- Any crosscutting igneous body

### Example
```python
gp.map_stack_to_surfaces(
    geo_model,
    mapping={
        'Intrusion': ['Granite_Body'],
        'Country_Rock': ['Formation_A', 'Formation_B'],
    }
)

geo_model.structural_frame.structural_groups[0].structural_relation = \
    gp.data.StackRelationType.INTRUSION
```

## Ordering and Stacking

### Stack Order Rules

1. **Faults first**: Youngest faults at top
2. **Intrusions next**: Youngest intrusions
3. **Stratigraphy last**: Youngest at top within series

### Complete Example

```python
gp.map_stack_to_surfaces(
    geo_model,
    mapping={
        # Faults (youngest first)
        'Young_Fault': ['Fault_2'],
        'Old_Fault': ['Fault_1'],
        # Intrusions
        'Granite': ['Granite_Body'],
        # Stratigraphy (youngest first within series)
        'Upper_Sequence': ['Top_Fm', 'Mid_Fm'],
        'Lower_Sequence': ['Base_Fm', 'Basement'],
    }
)

# Set relations
groups = geo_model.structural_frame.structural_groups
groups[0].structural_relation = gp.data.StackRelationType.FAULT
groups[1].structural_relation = gp.data.StackRelationType.FAULT
groups[2].structural_relation = gp.data.StackRelationType.INTRUSION
groups[3].structural_relation = gp.data.StackRelationType.ERODE
# Last group typically default (conformal)
```

### Debugging Stack Order

```python
# Print current structure
for i, group in enumerate(geo_model.structural_frame.structural_groups):
    print(f"{i}: {group.name} - {group.structural_relation}")
    for element in group.elements:
        print(f"   - {element.name}")
```
