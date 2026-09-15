# Kingstown groundwater and meteorology fixture

These are unchanged CSVs from the dedicated
[Pastas data repository](https://github.com/pastas/pastas-data/tree/dcc1363765c0a40ee9dfb2a418f8589b3a146580/collenteur_2019),
pinned to commit `dcc1363765c0a40ee9dfb2a418f8589b3a146580` and retrieved
2026-09-15. `provenance.json` records exact download URLs, byte counts and
SHA-256 values. Tests and the workflow verify these hashes without downloading
data at runtime. The raw files and `settings.upstream.json` retain the upstream
data repository's GPL-3.0 declaration; see `LICENSE.upstream`. They are not
relicensed under the project's or Pastas software's MIT license.

| File | Records | Date labels | Supplied unit | Model unit |
| --- | ---: | --- | --- | --- |
| `head.csv` | 5,737 | 2003-01-01–2018-12-25 | ft | m |
| `rain.csv` | 6,206 | 2001-12-17–2018-12-31 | ft/day | mm/day |
| `evap.csv` | 6,224 | 2001-12-17–2018-12-31 | ft/day | mm/day |

The head is from USGS well 412918071321001 near Kingstown, Rhode Island.
Rainfall is from Kingston GSOD/WBAN station 54796. Reference evaporation is
estimated from temperature using the published Thornthwaite/Pereira–Pruitt
method; it is not observed actual evapotranspiration. Source and unit evidence
is the [published example notebook](https://github.com/pastas/pastas/blob/fe740c1c270be41a95f4a8b8b0965f26c4ef6769/doc/examples/groundwater_paper/Ex1_simple_model/Example1.ipynb)
and [Collenteur et al. (2019)](https://doi.org/10.1111/gwat.12925).

Keep negative relative heads. These CSVs do not establish an absolute vertical
datum, screen interval, timezone or precise daily accumulation boundary.
Multiplying head by 0.3048 and stresses by 304.8 converts units only; it does
not resolve those reference systems. Preserve the supplied naive date labels.

The full head calendar has 101 omitted dates. Rainfall has 18 omitted dates
over its full source range, three within the required warmup/analysis range.
Missing head dates remain unscored. Missing rain is not zero: the fixed design
uses flagged calendar-month means learned exclusively from calibration
observations for 2008-11-11, 2014-07-26 and 2014-07-27.

`design.json` is the project's evaluation design, chosen before fitting:
2005–2013 calibration, 2014–2018 holdout, 730 days of observed warmup, Gamma
response, linear recharge, AR noise and three calibration-only baselines.
`settings.upstream.json` is retained for provenance, not used as a hidden
configuration override. There is no response search or holdout-based tuning.

Run the [workflow recipe](../../../../workflows/hydrogeological-analysis/references/field_case.md)
or the commands in the [validation report](../../../../docs/HYDRO_WORKFLOW_VALIDATION.md).
Updating this fixture requires an explicit new source commit, retained license,
recomputed hashes and renewed unit/missing-value review. Do not overwrite raw
observations with processed or imputed values.
