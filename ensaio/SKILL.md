---
name: ensaio
description: Fetch versioned Fatiando geoscience datasets with Ensaio and preserve their hashes, citations and data conventions. Use for reproducible sample-data acquisition and replacing supported RockHound datasets; the fetchers return paths for format-specific readers.
license: MIT
metadata:
  version: "1.0.0"
  author: Geoscience Skills
  skill_type: domain
  tags: '["Datasets", "Provenance", "Geophysics"]'
  dependencies: '["ensaio==0.7.1", "pandas>=2.3"]'
  complements: '["pooch", "boule", "verde", "xarray"]'
  workflow_role: data-loading
---

# Ensaio

Retrieve an explicit data version, then read it with a suitable format library.
A package version and a dataset version identify different things.

## Acquisition

Select a fetcher from the installed API, review the original data license and
citation, and estimate download/storage needs. `ENSAIO_DATA_DIR` selects a project
cache. Preserve original downloaded bytes; write derived products elsewhere.
The underlying Pooch registry verifies the expected content hash.

## Versioned GPS data

```python
# example: alps-gps
from pathlib import Path
import hashlib
import ensaio
import pandas as pd

source_path = Path(ensaio.fetch_alps_gps(version=1))
source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
gps = pd.read_csv(source_path)
```

This returns a compressed CSV path, not a DataFrame. A first fetch requires
network access unless the verified bytes are already cached. A network failure
is not a validated empty dataset, and disabling hash verification is not a fix.

## Scientific checks

Inspect column units, coordinate/velocity reference frames, epochs and uncertainty
definitions from the **original source**. For this dataset, the published solution
uses IGb08/ITRF2008 and the GRS80 ellipsoid, with horizontal velocities relative
to Eurasia. Ensaio's short fetcher description says WGS84; do not use that shorthand
to override the detailed source provenance or perform an unrecorded conversion.

Check station identifiers and missing values; keep velocity components and their
standard deviations paired. Position uncertainty and velocity uncertainty are
not interchangeable. Resampling or gridding must carry the reference frame and
does not improve the observation accuracy automatically.

Record dataset version, source hash, package version, retrieval date and citation.
See the [fetcher documentation](https://www.fatiando.org/ensaio/latest/api/generated/ensaio.fetch_alps_gps.html),
[original data](https://doi.org/10.1594/PANGAEA.886889) and
[redistributed v1 release](https://doi.org/10.5281/zenodo.5879163).
