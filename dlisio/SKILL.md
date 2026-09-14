---
name: dlisio
description: |
  Read and parse DLIS (Digital Log Interchange Standard) and LIS (Log Information
  Standard) well log files. Use when the agent needs to: (1) Read/parse DLIS or LIS
  files, (2) Extract well log curves as numpy arrays, (3) Access file metadata and
  origin information, (4) Handle multi-frame or multi-file DLIS, (5) Convert DLIS
  to LAS or DataFrame, (6) Work with RP66 format well logs, (7) Process array or
  image log data.
license: MIT
metadata:
  version: "1.0.2"
  author: Geoscience Skills
  tags: '["Well Logs", "DLIS", "RP66", "Data I/O", "Dlisio", "Petrophysics", "LIS", "Wireline"]'
  dependencies: '["dlisio>=1.0.4", "numpy", "pandas", "lasio>=0.32"]'
  complements: '["welly", "petropy", "striplog"]'
  workflow_role: data-loading
  skill_type: domain
---

# DLIS/LIS reading and controlled LAS export

Use dlisio for binary RP66 DLIS and LIS79 input. It returns structured NumPy
arrays and metadata objects; it does not write DLIS. Use lasio for LAS.

## Select a logical file and frame

Inspect the physical file before selecting data. Logical files and frames may
have different depths, sampling rates and channel identities. `dlis.load()`
returns a `PhysicalFile` context manager, not a generator. Read array data
inside the context, then retain copied arrays or DataFrames after closing it.

```python
from dlisio import dlis

def inventory(path):
    items = []
    with dlis.load(str(path)) as files:
        for logical_index, logical in enumerate(files):
            for frame_index, frame in enumerate(logical.frames):
                items.append({
                    'logical_file': logical_index, 'frame': frame_index,
                    'fingerprint': frame.fingerprint,
                    'index_type': frame.index_type, 'index': frame.index,
                    'channels': [(ch.fingerprint, ch.units, ch.dimension)
                                 for ch in frame.channels],
                })
    return items
```

A channel's identity includes type, mnemonic, origin and copy number. Names
alone need not be unique. Use `channel.fingerprint` to access its array field;
`frame.curves()` uses fingerprints as dtype titles even when names are disambiguated.
The `FRAMENO` field records frame sequence numbers, not measured depth.

## Read scalar and array channels

```python
from dlisio import dlis
import pandas as pd

def read_frame(path, logical_file_index=0, frame_index=0):
    with dlis.load(str(path)) as files:
        if not 0 <= logical_file_index < len(files):
            raise ValueError('Logical file index out of range')
        logical = files[logical_file_index]
        if not 0 <= frame_index < len(logical.frames):
            raise ValueError('Frame index out of range')
        frame = logical.frames[frame_index]
        records = frame.curves()
        scalar = {name: records[name].copy() for name in records.dtype.names
                  if records[name].ndim == 1}
        arrays = {ch.fingerprint: records[ch.fingerprint].copy()
                  for ch in frame.channels if records[ch.fingerprint].ndim > 1}
        metadata = {'frame': frame.fingerprint, 'index_type': frame.index_type,
                    'index': frame.index,
                    'channels': {ch.fingerprint: {'name': ch.name, 'units': ch.units,
                                 'dimension': ch.dimension} for ch in frame.channels}}
        return pd.DataFrame(scalar), arrays, metadata
```

Keep array/image channels as arrays, preserving all trailing dimensions.
A structured array has `dtype.names`, not `.items()`. Direct DataFrame
conversion fails when it contains multidimensional fields. Do not average
image channels into scalars without a requested, documented reduction.

## Depth, missing values and conversion

- Check `frame.index_type` and the first channel's units before declaring an
  index to be depth. A time channel or `FRAMENO` is not a depth surrogate.
- Preserve increasing or decreasing depth order. Duplicate/nonmonotonic depths
  need explicit handling; do not silently sort or resample different passes.
- DLIS has no universal LAS-style null sentinel. Retain NaNs and apply a vendor
  null marker only when its meaning is documented. Preserve masks through export.
- Read [frame and channel handling](references/frame_channels.md) for identity,
  searching and separate lossless array export. Read [file structure and LIS](references/dlis_structure.md)
  for metadata, encodings and the separate LIS API.

The bundled [DLIS-to-LAS helper](scripts/dlis_to_las.py) always includes a
validated depth curve first, even when `--curves` requests only measurements.
It accepts a unique mnemonic or full fingerprint, preserves m/ft and depth
order, and writes `STEP=0` for irregular sampling. Arrays are excluded with a
diagnostic by default; explicitly requesting one fails instead of discarding it.
LAS is a lossy representation of DLIS metadata and multidimensional samples.

```bash
python scripts/dlis_to_las.py well.dlis --list
python scripts/dlis_to_las.py well.dlis scalar.las --logical-file 0 --frame 0 --curves GR
```

Resolve the script path relative to this installed skill directory. For a
non-depth-indexed frame, require an explicit `--depth-channel`. Supported
export depth units are m and ft; other units need a documented conversion.
`--null-value` records the operator's choice of a known vendor sentinel.

## Verification scope

Checked with dlisio 1.0.4 using project-generated binary DLIS, including multiple
logical files/frames, duplicate mnemonics, scalar/array channels, NaNs and LAS
roundtrips. These synthetic files are project-owned, not redistributed field
logs. LIS, damaged-file recovery and vendor-specific records need their own
fixtures; do not claim those branches were exercised by the DLIS tests.

[Official DLIS API](https://dlisio.readthedocs.io/en/latest/dlis/api.html), checked
2026-09-14. Use strict parsing unless an explicit, recorded recovery decision
justifies relaxing it; errors must not be reported as successful empty exports.
