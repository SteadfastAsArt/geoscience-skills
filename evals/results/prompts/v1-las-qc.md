Complete the task below in /workspace. This is one small evaluation; do not launch other agents or coding-agent CLIs. Read skill-catalog.json, select the relevant skill(s), and read their SKILL.md before implementation. The provided skills/ library is read-only. Use Python from PATH; lasio, segyio and NumPy are already installed. Do not install packages, download data, access credentials, or modify inputs. Write solution.py, execute it, and create the requested output. Also write evidence.json as {"selected_skills":["name"],"commands":["command actually run"],"outputs":["filename"]}. Keep the final response brief.

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
