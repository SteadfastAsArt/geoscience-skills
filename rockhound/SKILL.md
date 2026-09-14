---
name: rockhound
description: Maintain or migrate legacy RockHound geoscience dataset downloads, caches and loaders such as PREM. Use when an existing project imports RockHound; prefer maintained Ensaio fetchers for supported new dataset workflows.
license: MIT
metadata:
  version: "1.0.0"
  author: Geoscience Skills
  skill_type: domain
  tags: '["Legacy", "Datasets", "Migration", "PREM"]'
  dependencies: '["rockhound==0.2.0"]'
  complements: '["ensaio", "pooch", "xarray", "disba"]'
  workflow_role: data-loading
---

# RockHound maintenance and migration

RockHound's repository was archived in 2022 and recommends Ensaio. Preserve a
working legacy environment while assessing supported replacements; there is no
universal one-to-one mapping of fetcher names or return objects.

## Inspect an existing workflow

Identify the exact fetcher, data version, source URL/hash, cache location, parser
and scientific conventions. Set `ROCKHOUND_DATA_DIR` before importing RockHound
if a separate cache is needed. Never delete a user's cache to test a migration.

## Legacy PREM load

This fragment uses the upstream registry and may download from EarthScope/IRIS.
It loads the 1 s PREM radial Earth model, not a local field observation.
The registry URL returned HTTP 404 during the 2026-09-14 check. This example
currently needs an existing hash-verified cache or a separately verified source;
it is not a successful fresh-download recipe. The test suite exercises the real
loader with a clearly synthetic cache fixture, without claiming PREM validation.

```python
# example: legacy-prem
import rockhound

prem = rockhound.fetch_prem()
radius_km = prem["radius"].to_numpy()
depth_km = prem["depth"].to_numpy()
density_g_cm3 = prem["density"].to_numpy()
vpv_km_s = prem["Vpv"].to_numpy()
vsv_km_s = prem["Vsv"].to_numpy()
```

The table contains discontinuities and distinct vertical/horizontal velocities.
Preserve repeated boundary radii and choose a side explicitly for interpolation.
Zero shear velocity in a fluid region is meaningful, not a missing value. Do not
send the full radial model directly to a plane-layer surface-wave solver.

## Migration steps

1. Find a maintained dataset release, its redistribution license and immutable
   identifier. If Ensaio has no matching dataset, use a documented Pooch registry
   and the original provider instead of substituting unrelated sample data.
2. Compare downloaded hashes or document changed releases; inspect units, grid
   registration, coordinates, missingness and source preprocessing.
3. Adapt the return contract: an Ensaio path still needs a CSV/NetCDF reader,
   while RockHound may return a DataFrame or xarray object.
4. Verify representative values and downstream results before replacing imports.
   Diagnose failed old URLs; do not bypass TLS or checksum checks.

See the [archived project notice](https://github.com/fatiando/rockhound),
[PREM loader contract](https://www.fatiando.org/rockhound/latest/api/generated/rockhound.fetch_prem.html)
and [Ensaio catalog](https://www.fatiando.org/ensaio/latest/).
