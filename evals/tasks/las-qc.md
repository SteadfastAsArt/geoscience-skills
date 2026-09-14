# LAS quality control

Inspect `inputs/well.las` without changing it. Write a reproducible `solution.py`
and execute it with the supplied Python environment. Produce `result.json` with:

```json
{
  "row_count": 0,
  "depth": {
    "unit": "...", "minimum": 0, "maximum": 0,
    "strictly_increasing": false, "duplicate_count": 0
  },
  "curves": {
    "GR": {"unit": "...", "valid_count": 0, "null_count": 0,
           "minimum": 0, "maximum": 0, "mean": 0},
    "RHOB": {"unit": "...", "valid_count": 0, "null_count": 0,
             "minimum": 0, "maximum": 0, "mean": 0}
  }
}
```

The zeroes and ellipses above describe the schema, not expected values. Preserve
file units. Exclude LAS NULL values from curve statistics. Count duplicate depth
rows beyond their first occurrence; test strictly increasing in original order.
Do not sort, interpolate, or discard input rows.
