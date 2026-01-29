# Lexicon Configuration

A Lexicon maps rock type names, synonyms, and visual properties for consistent interpretation of geological descriptions.

## Table of Contents
- [Basic Lexicon](#basic-lexicon)
- [Lexicon Structure](#lexicon-structure)
- [Common Lithology Synonyms](#common-lithology-synonyms)
- [Using with Descriptions](#using-with-descriptions)
- [Built-in Lexicons](#built-in-lexicons)

## Basic Lexicon

```python
from striplog import Lexicon

lexicon_dict = {
    'lithology': {
        'sandstone': {
            'synonyms': ['sand', 'ss', 'sst', 'sandst', 'arenite'],
            'colour': '#FFFF00',
            'hatch': '...'
        },
        'shale': {
            'synonyms': ['sh', 'clay', 'mudstone', 'claystone'],
            'colour': '#808080',
            'hatch': '---'
        },
        'limestone': {
            'synonyms': ['ls', 'lime', 'calcaire', 'carbonate'],
            'colour': '#00BFFF',
            'hatch': '+++'
        }
    }
}

lexicon = Lexicon(lexicon_dict)
```

## Lexicon Structure

```python
lexicon_dict = {
    'lithology': {           # Property name
        'rock_type': {       # Canonical name
            'synonyms': [],  # Alternative names
            'colour': '',    # Hex color for plotting
            'hatch': '',     # Matplotlib hatch pattern
            # Additional properties...
        }
    }
}
```

### Multiple Property Categories

```python
lexicon_dict = {
    'lithology': {
        'sandstone': {'synonyms': ['sand', 'ss']},
        'shale': {'synonyms': ['sh', 'clay']},
    },
    'grain_size': {
        'fine': {'synonyms': ['f', 'fn', 'vf']},
        'medium': {'synonyms': ['m', 'med']},
        'coarse': {'synonyms': ['c', 'crs']},
    },
    'sorting': {
        'well sorted': {'synonyms': ['ws', 'well-sorted']},
        'poorly sorted': {'synonyms': ['ps', 'poorly-sorted']},
    }
}
```

## Common Lithology Synonyms

| Lithology | Common Synonyms |
|-----------|-----------------|
| sandstone | sand, ss, sst, sandst, arenite, psammite |
| shale | sh, clay, mudstone, claystone, argillite |
| limestone | ls, lime, calcaire, carbonate, calc |
| dolomite | dol, dolostone, dolomitic |
| siltstone | silt, slst, sltst |
| conglomerate | cgl, congl, gravel |
| coal | c, lignite, anthracite |
| granite | gr, granitic |
| basalt | bas, volcanic |
| gneiss | gn, metamorphic |

## Using with Descriptions

```python
from striplog import Striplog, Lexicon

# Define lexicon
lexicon = Lexicon({
    'lithology': {
        'sandstone': {'synonyms': ['sand', 'ss']},
        'shale': {'synonyms': ['sh', 'clay']},
        'limestone': {'synonyms': ['ls', 'lime']},
    }
})

# Parse text with abbreviations
text = """
0-10: ss, fine grained
10-25: sh, dark grey
25-40: ls, fossiliferous
"""

strip = Striplog.from_description(text, lexicon=lexicon)
print(strip)
```

### Parsing Different Formats

```python
# Depth-colon-description format
text1 = "0-10: sandstone, 10-20: shale"

# Depth range with units
text2 = """
0.0 - 5.5 m: fine sandstone
5.5 - 12.0 m: grey shale
"""

# Both work with from_description()
strip = Striplog.from_description(text1, lexicon=lexicon)
```

## Built-in Lexicons

Striplog includes default lexicons for common use cases:

```python
from striplog import Lexicon

# Load default lexicon
lexicon = Lexicon.default()

# Check available lithologies
print(lexicon.lithology.keys())
```

## Creating Legend from Lexicon

```python
from striplog import Lexicon, Legend, Decor

# Lexicon with visual properties
lexicon_dict = {
    'lithology': {
        'sandstone': {
            'synonyms': ['sand'],
            'colour': '#FFFF00',
            'hatch': '...',
            'width': 3
        },
        'shale': {
            'synonyms': ['sh'],
            'colour': '#808080',
            'hatch': '---',
            'width': 3
        },
    }
}

# Create matching legend
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
]

legend = Legend(decors)
```

## Standard Colors

| Lithology | Suggested Color | Hex Code |
|-----------|-----------------|----------|
| Sandstone | Yellow | #FFFF00 |
| Shale | Grey | #808080 |
| Limestone | Light Blue | #00BFFF |
| Dolomite | Cyan | #00FFFF |
| Siltstone | Light Brown | #D2B48C |
| Coal | Black | #000000 |
| Conglomerate | Orange | #FFA500 |
| Granite | Pink | #FFC0CB |
| Basalt | Dark Grey | #404040 |

## Tips

1. **Case insensitivity** - Synonyms are matched case-insensitively
2. **Partial matching** - Some methods support partial string matching
3. **Order matters** - First matching synonym wins
4. **Keep it simple** - Start with common synonyms, add more as needed
5. **Consistent spelling** - Use canonical names in outputs
