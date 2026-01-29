# Multi-Well Project Workflows

## Table of Contents
- [Loading Projects](#loading-projects)
- [Iterating Over Wells](#iterating-over-wells)
- [Filtering Wells](#filtering-wells)
- [Cross-Well Statistics](#cross-well-statistics)
- [Data Aggregation](#data-aggregation)
- [Batch Processing](#batch-processing)
- [Export Workflows](#export-workflows)

## Loading Projects

Load multiple wells into a Project for unified analysis.

```python
from welly import Project

# Load all LAS files from directory
p = Project.from_las('wells/*.las')
print(f"Loaded {len(p)} wells")

# Load from list of paths
from pathlib import Path
paths = list(Path('data').glob('**/*.las'))
p = Project.from_las(paths)

# Print project summary
print(p)
for w in p:
    print(f"  {w.name}: {len(w.data)} curves")
```

## Iterating Over Wells

Access wells by index or iteration.

```python
from welly import Project

p = Project.from_las('wells/*.las')

# Iterate over all wells
for well in p:
    print(f"{well.name}: {list(well.data.keys())}")

# Access by index
first_well = p[0]
last_well = p[-1]

# Access by slicing
subset = p[0:5]  # First 5 wells
```

## Filtering Wells

Select wells based on criteria.

```python
from welly import Project

p = Project.from_las('wells/*.las')

# Filter by curve availability
wells_with_sonic = [w for w in p if 'DT' in w.data]
print(f"Wells with sonic: {len(wells_with_sonic)}")

# Filter by multiple curves
required = ['GR', 'RHOB', 'NPHI']
complete_wells = [w for w in p if all(c in w.data for c in required)]

# Filter by depth coverage
min_depth = 2000
deep_wells = [w for w in p if w.data['GR'].stop > min_depth]

# Filter by location (if available)
wells_in_area = [
    w for w in p
    if hasattr(w.location, 'x') and w.location.x is not None
    and 500000 < w.location.x < 600000
]
```

## Cross-Well Statistics

Compute statistics across the project.

```python
from welly import Project
import pandas as pd
import numpy as np

p = Project.from_las('wells/*.las')

# Gather statistics for each well
stats = []
for w in p:
    row = {'well': w.name}

    # Curve statistics
    for curve_name in ['GR', 'RHOB', 'NPHI']:
        if curve_name in w.data:
            curve = w.data[curve_name]
            values = curve.values[~np.isnan(curve.values)]
            row[f'{curve_name}_mean'] = values.mean()
            row[f'{curve_name}_std'] = values.std()
            row[f'{curve_name}_min'] = values.min()
            row[f'{curve_name}_max'] = values.max()

    # Depth coverage
    if 'GR' in w.data:
        row['depth_start'] = w.data['GR'].start
        row['depth_stop'] = w.data['GR'].stop
        row['depth_range'] = row['depth_stop'] - row['depth_start']

    stats.append(row)

df = pd.DataFrame(stats)
print(df.describe())
```

## Data Aggregation

Combine data from multiple wells.

```python
from welly import Project
import pandas as pd
import numpy as np

p = Project.from_las('wells/*.las')

# Aggregate all GR values for histogram
all_gr = []
for w in p:
    if 'GR' in w.data:
        values = w.data['GR'].values
        all_gr.extend(values[~np.isnan(values)])

all_gr = np.array(all_gr)
print(f"Total samples: {len(all_gr)}")
print(f"GR range: {all_gr.min():.1f} - {all_gr.max():.1f}")

# Create combined DataFrame with well identifier
dfs = []
for w in p:
    df = w.df()
    df['well'] = w.name
    dfs.append(df)

combined = pd.concat(dfs, ignore_index=True)
print(f"Combined shape: {combined.shape}")
```

## Batch Processing

Apply processing to all wells in project.

```python
from welly import Project
import numpy as np

p = Project.from_las('wells/*.las')

# Process each well
for w in p:
    # Despike GR if present
    if 'GR' in w.data:
        w.data['GR_CLEAN'] = w.data['GR'].despike(window=5, z=2)

    # Normalize porosity curves
    for name in ['NPHI', 'DPHI']:
        if name in w.data:
            w.data[f'{name}_NORM'] = w.data[name].normalize()

    # Resample all curves to common basis
    common_step = 0.5
    for name in list(w.data.keys()):
        curve = w.data[name]
        if curve.step != common_step:
            w.data[name] = curve.resample(step=common_step)

# Verify processing
for w in p:
    print(f"{w.name}: {list(w.data.keys())}")
```

## Export Workflows

Export project data in various formats.

```python
from welly import Project
from pathlib import Path

p = Project.from_las('wells/*.las')
output_dir = Path('output')
output_dir.mkdir(exist_ok=True)

# Export each well to LAS
for w in p:
    w.to_las(output_dir / f'{w.name}.las')

# Export each well to CSV
for w in p:
    df = w.df()
    df.to_csv(output_dir / f'{w.name}.csv')

# Export project summary
import pandas as pd

summary = []
for w in p:
    summary.append({
        'name': w.name,
        'uwi': w.uwi,
        'n_curves': len(w.data),
        'curves': ', '.join(w.data.keys()),
    })

pd.DataFrame(summary).to_csv(output_dir / 'project_summary.csv', index=False)
```

## Quality Control Workflow

Check data quality across project.

```python
from welly import Project
import numpy as np
import pandas as pd

p = Project.from_las('wells/*.las')

qc_results = []
for w in p:
    result = {'well': w.name}

    # Check each curve
    for name, curve in w.data.items():
        null_count = np.sum(np.isnan(curve.values))
        null_pct = 100 * null_count / len(curve.values)

        if null_pct > 20:
            result[f'{name}_quality'] = 'POOR'
        elif null_pct > 5:
            result[f'{name}_quality'] = 'FAIR'
        else:
            result[f'{name}_quality'] = 'GOOD'

        result[f'{name}_null_pct'] = null_pct

    qc_results.append(result)

qc_df = pd.DataFrame(qc_results)
print("Data Quality Summary:")
print(qc_df)

# Flag wells needing attention
poor_wells = [
    r['well'] for r in qc_results
    if any(v == 'POOR' for k, v in r.items() if k.endswith('_quality'))
]
print(f"\nWells needing attention: {poor_wells}")
```

## Parallel Processing

Speed up processing for large projects.

```python
from welly import Well
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import pandas as pd

def process_well(path: str) -> dict:
    """Process single well and return statistics."""
    try:
        w = Well.from_las(path)
        result = {'path': path, 'name': w.name, 'status': 'OK'}

        if 'GR' in w.data:
            gr = w.data['GR'].values
            result['gr_mean'] = gr[~np.isnan(gr)].mean()

        return result
    except Exception as e:
        return {'path': path, 'name': None, 'status': str(e)}

# Process in parallel
paths = list(Path('wells/').glob('*.las'))
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_well, [str(p) for p in paths]))

df = pd.DataFrame(results)
print(f"Processed: {len(df[df['status'] == 'OK'])}/{len(df)}")
```
