# NOAA GHCN-Daily station snapshot

NOAA National Centers for Environmental Information, *Global Historical
Climatology Network – Daily (GHCN-Daily), Version 3*,
[DOI 10.7289/V5D21VHZ](https://doi.org/10.7289/V5D21VHZ).

The [official US government dataset catalog](https://catalog.data.gov/dataset/global-historical-climatology-network-daily-ghcn-daily-version-3)
assigns this dataset [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).
This is data-level evidence, not an inference from a software or website license.
NOAA does not endorse this project or its interpretations.

The fixture is the complete, unedited NCEI API CSV response retrieved on
2026-09-15 for twelve preselected stations and 2018–2020 TMAX. It is losslessly
gzip-compressed with `mtime=0`. [provenance.json](provenance.json) records the
exact query, both hashes, units, quality attributes and limitations. API snapshots
may change as NOAA revises observations or station metadata; the hashes identify
these retained bytes. Compression-library versions can change gzip bytes without
changing the decompressed CSV.

`recorded-report.json` is a project-derived diagnostic with source and executable
hashes. Its model estimates and holdout errors are not additional observations
or known climate truth. The output NetCDF is generated offline; its recorded
hash refers to the documented dependency baseline, not a cross-platform byte
identity requirement. Numerical and metadata comparisons provide portability.
