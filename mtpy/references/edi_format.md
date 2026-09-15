# EDI conventions and missingness

Use this reference when reading a direct-impedance EDI or checking an export.
Other EDI variants store spectra or resistivity/phase and need a corresponding
reader route. The bundled QC helper deliberately accepts direct impedance only.

| Section | Meaning and required checks |
| --- | --- |
| `HEAD` | Station identifier, coordinates, acquisition dates, datum and EMPTY sentinel. Elevation alone does not establish a vertical datum. |
| `INFO` | Processing and convention evidence; retain it with the raw source. |
| `DEFINEMEAS` | Channel geometry, orientations and distance units. |
| `MTSECT` | Frequency count and channel identifiers. |
| `FREQ` | Positive, unique frequencies in Hz; align every tensor component after ordering. |
| `ZROT` | Existing tensor orientation in degrees; an added rotation is not an absolute strike. |
| `ZXXR/ZXXI`, `ZXYR/ZXYI`, `ZYXR/ZYXI`, `ZYYR/ZYYI` | Real/imaginary impedance. Confirm units from the processing metadata. |
| `Zxx.VAR` etc. | Variance, whose square root is the standard-deviation error array. Missing variance must remain unknown. |

The tested positive-time NED convention has x=north, y=east and z=down. For
impedance in mV/km/nT, E/H in ohms is `z * mu0 * 1000`, and apparent resistivity
is `0.2 * abs(z)**2 / frequency_hz`. Retain signed phases from `angle(z)`.
Tensor indices name electric/magnetic directions; they are not inherently TE/TM.

```python
from mtpy import MT

station = MT("station.edi")
station.read(get_elevation=False)
z = station.Z.z
sigma = station.Z.z_error
rho = station.Z.resistivity
phase = station.Z.phase
has_tipper = station.has_tipper()  # method, not a boolean attribute
```

The mt-metadata 1.0.10 reader substitutes zero for some EMPTY values and missing
variances. Its writer can encode physical numeric zeros as EMPTY. Therefore an
unqualified write/read equality check cannot prove missingness preservation.
The [QC helper](../scripts/mt_analysis.py) retains original masks separately,
checks valid source numbers against the actual reader, and exports NaNs and
flags in CSV. It rejects rotation when tensor values or variances are incomplete.

For complete data with no physically meaningful zeros, the tested EDI export is:

```python
station.write(fn="copy.edi")
copy = MT("copy.edi")
copy.read(get_elevation=False)
```

Recheck source bytes, tensor values, errors, station identity, coordinates and
rotation at output precision. The reader normalizes some station punctuation;
keep both the original identifier and the reader's form in provenance.
See the [official reader/writer source](https://github.com/MTgeophysics/mt_metadata/blob/40b897dc977f13ec0cd15f4606aada9f95396b3b/mt_metadata/transfer_functions/io/edi/edi.py)
before depending on another EDI variant or version.
