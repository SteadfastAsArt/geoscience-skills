# Alps GNSS field-data fixture

The third-party data in this directory are **not covered by the repository's
MIT license**. They are redistributed unchanged with the following attribution.

## Original observations and published station solutions

Sánchez, Laura; Völksen, Christof; Sokolov, Alexandr; Arenz, Herbert; Seitz,
Florian (2018): *Present-day surface deformation of the Alpine Region inferred
from geodetic techniques (data).* PANGAEA,
[doi:10.1594/PANGAEA.886889](https://doi.pangaea.de/10.1594/PANGAEA.886889).

`ALPS2017_NEH.CRD`, `ALPS2017_NEH.VEL`, and `ALPS2017_REP.VEL` retain their
[Creative Commons Attribution 3.0 Unported license](https://creativecommons.org/licenses/by/3.0/).
The files' original headers and solution descriptions are preserved. Their
source URLs and immutable content hashes are in [provenance.json](provenance.json).

## Curated table

The Fatiando a Terra Developers (2022), *Alps GPS velocities*, release `v1`,
[doi:10.5281/zenodo.5879163](https://zenodo.org/records/5879163),
Git revision `123af5d44f4e872300c6eda5455f1fed8f9d5acf`.

`alps-gps-velocity.csv.xz` is the unmodified upstream curated table under
[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/),
with attribution also due to the original data authors above. The upstream
[README](https://github.com/fatiando-data/alps-gps-velocity/blob/123af5d44f4e872300c6eda5455f1fed8f9d5acf/README.md)
specifies both licenses; [FATIANDO-LICENSE.txt](FATIANDO-LICENSE.txt) is the
unmodified upstream license notice.

We make no further changes to these data. The test helper independently
reconstructs the table using the upstream station selection, first-solution
selection, two station-ID corrections, unit conversion, and decimal rounding.
Those curation changes are recorded in `provenance.json` and in the upstream
[preparation notebook](https://github.com/fatiando-data/alps-gps-velocity/blob/123af5d44f4e872300c6eda5455f1fed8f9d5acf/prepare.ipynb).
Neither the data authors nor Fatiando endorse this project's diagnostic model.
