Complete the task below in /workspace using Python from PATH. This is one small evaluation: do not launch other coding-agent CLIs or additional agents. The scientific Python environment is already available; do not install packages or download data. Do not access credentials or modify the input files. Write solution.py, execute it, check the requested scientific outputs, and finish with a brief response. Do not create a separate evidence report; the evaluator records actual execution events.

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
