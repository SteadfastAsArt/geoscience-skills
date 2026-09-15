# File structure, metadata and LIS

A physical DLIS file contains independent logical files. Each logical file has
its own metadata objects and frames, and each frame describes channels sharing
a sampling index. Matching names in different logical files do not establish
that curves share a depth grid or belong to the same logging pass.

## Metadata inspection

```python
from dlisio import dlis

def well_metadata(path):
    with dlis.load(str(path)) as files:
        return [{'logical_file': number,
                 'origins': [{'name': origin.fingerprint,
                              'well': origin.well_name, 'field': origin.field_name,
                              'company': origin.company} for origin in logical.origins]}
                for number, logical in enumerate(files)]
```

Keep absent values as absent, not the string `"None"` or an invented well name.
Origin numbers and channel copy numbers are part of identity, not depth units.
Use `physical.describe()` / `logical.describe()` for human inspection; their
printed representations are not a stable machine-readable schema.

## Character encoding

Set an explicit encoding policy before opening files when the default fails:
`dlisio.common.set_encodings(['utf-8', 'latin-1'])`. The function belongs to
`common`, not `dlis`. It changes process-wide decoding preferences; preserve
and restore the previous policy in a reusable application. Do not use permissive
fallback decoding to conceal unknown provenance or malformed numeric records.

## LIS uses a separate API

This fragment requires a real LIS79 file and is not exercised by the synthetic
DLIS regression fixture:

```python
from dlisio import lis

def read_lis(path):
    frames = []
    with lis.load(str(path)) as files:
        for logical in files:
            for specification in logical.data_format_specs():
                frames.append(lis.curves(logical, specification).copy())
    return frames
```

LIS specifications can describe multiple sampling rates and index semantics;
read the associated specification before joining arrays or writing LAS.

## Sources and limits

- [DLIS format and API](https://dlisio.readthedocs.io/en/latest/dlis/api.html)
- [LIS API](https://dlisio.readthedocs.io/en/latest/lis/api.html)
- [Common encoding API](https://dlisio.readthedocs.io/en/latest/common-api.html)

Checked 2026-09-14. dlisio reads DLIS and LIS; generated DLIS fixtures use a
separate writer. A library's software licence does not license external well
measurements, so record dataset permission separately for any future field file.
