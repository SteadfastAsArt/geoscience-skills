---
name: segysak
description: Read SEG-Y as labelled xarray datasets with SEGY-SAK, inspect header-defined survey dimensions and process seismic volumes lazily. Use for SEG-Y/xarray/Dask workflows; use segyio for exact low-level trace and header editing.
license: MIT
metadata:
  version: "1.0.0"
  author: Geoscience Skills
  skill_type: domain
  tags: '["SEG-Y", "Seismic", "xarray", "Dask"]'
  dependencies: '["segysak==0.5.4"]'
  complements: '["segyio", "xarray", "bruges"]'
  workflow_role: data-loading
---

# SEGY-SAK

Map trace headers to labelled dimensions without losing the original survey
geometry. Header byte assignments are evidence to inspect, not safe guesses.

## Before opening

Inspect format/endian, trace count, sample count/interval, delay recording time,
inline/crossline or CDP headers, coordinate units and scalar. SEG-Y sample
intervals are stored in microseconds; the backend's vertical samples use
milliseconds for ordinary time sections. A depth section needs an explicit
depth convention. Confirm actual data units before labelling an axis.

Check dimension key uniqueness and missing traces. Sparse or irregular geometry
may not form a complete rectangular cube. Keep the original trace index for
exports. A dimension byte offset is one-based SEG-Y numbering (CDP ensemble is
21, inline is 189, crossline is 193); some upstream old examples use a wrong CDP
offset. Use the actual file's header convention.

## Labelled read

This fragment needs an existing, verified rectangular post-stack file. It uses
the 0.5 backend API; old `segy_loader` tutorials describe a different interface.

```python
# example: labelled-segy
import xarray as xr
import segysak  # registers accessors; the installed distribution provides the backend

with xr.open_dataset(
    seismic_path,
    engine="sgy_engine",
    dim_byte_fields={"iline": 189, "xline": 193},
) as seismic:
    inline_labels = seismic.iline.values.copy()
    crossline_labels = seismic.xline.values.copy()
    sample_coordinate = seismic.samples.values.copy()
    amplitudes = seismic["data"].load().copy(deep=True)
```

For large surveys, open with Dask chunks chosen for the access pattern and retain
lazy operations until the selected result fits memory. Avoid `.load()` on a
whole production cube. Inspect coordinate variables before `.sel()` and use
`.isel()` only for integer positions.

## Validation and exports

Compare several labelled traces against original trace samples using `segyio`,
including the last sample and nonzero start time. Verify shape, orientation,
missing-trace behavior and coordinate scalars. Round-trip any export and compare
headers as well as amplitudes; xarray labels alone do not preserve every SEG-Y
header or prove geographic CRS. Keep source hash, byte mapping and transforms.

Use the [current documentation](https://trhallam.github.io/segysak/latest/) and
[backend source](https://github.com/trhallam/segysak/blob/main/segysak/segy/_xarray.py).
