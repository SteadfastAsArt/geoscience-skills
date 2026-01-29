# Common LAS Curve Mnemonics

## Table of Contents
- [Depth and Position](#depth-and-position)
- [Porosity Logs](#porosity-logs)
- [Resistivity Logs](#resistivity-logs)
- [Lithology Logs](#lithology-logs)
- [Acoustic Logs](#acoustic-logs)
- [NMR Logs](#nmr-logs)
- [Computed Curves](#computed-curves)

## Depth and Position

| Mnemonic | Description | Unit |
|----------|-------------|------|
| DEPT, DEPTH | Measured depth | M, FT |
| TVDSS | True vertical depth subsea | M, FT |
| TVD | True vertical depth | M, FT |
| MD | Measured depth | M, FT |

## Porosity Logs

| Mnemonic | Description | Unit |
|----------|-------------|------|
| NPHI | Neutron porosity (limestone matrix) | V/V, PU, % |
| TNPH | Thermal neutron porosity | V/V |
| DPHI | Density porosity | V/V |
| SPHI | Sonic porosity | V/V |
| PHIE | Effective porosity | V/V |
| PHIT | Total porosity | V/V |

## Resistivity Logs

| Mnemonic | Description | Unit |
|----------|-------------|------|
| RT, ILD | Deep resistivity / Induction deep | OHMM |
| RXO, MSFL | Flushed zone resistivity | OHMM |
| RS, ILM | Shallow resistivity / Induction medium | OHMM |
| LLD | Laterolog deep | OHMM |
| LLS | Laterolog shallow | OHMM |
| AT10-AT90 | Array resistivity at various depths | OHMM |

## Lithology Logs

| Mnemonic | Description | Unit |
|----------|-------------|------|
| GR | Gamma ray | GAPI, API |
| SGR | Spectral gamma ray (total) | GAPI |
| CGR | Computed gamma ray (K + Th) | GAPI |
| URAN | Uranium content | PPM |
| THOR | Thorium content | PPM |
| POTA | Potassium content | % |
| SP | Spontaneous potential | MV |
| CALI | Caliper | IN, CM |

## Density Logs

| Mnemonic | Description | Unit |
|----------|-------------|------|
| RHOB | Bulk density | G/CC, KG/M3 |
| DRHO | Density correction | G/CC |
| PEF, PE | Photoelectric factor | B/E |
| RHOZ | Z-axis density (LWD) | G/CC |

## Acoustic Logs

| Mnemonic | Description | Unit |
|----------|-------------|------|
| DT, DTC | Compressional sonic transit time | US/F, US/M |
| DTS | Shear sonic transit time | US/F |
| DTCO | Compressional slowness | US/F |
| DTSM | Shear slowness | US/F |

## NMR Logs

| Mnemonic | Description | Unit |
|----------|-------------|------|
| TCMR | Total CMR porosity | V/V |
| CMRP | CMR porosity | V/V |
| CMFF | CMR free fluid | V/V |
| BVI | Bulk volume irreducible | V/V |
| BVM | Bulk volume movable | V/V |
| T2LM | T2 log mean | MS |

## Computed Curves

| Mnemonic | Description | Unit |
|----------|-------------|------|
| VSH | Volume of shale | V/V |
| SW | Water saturation | V/V |
| SXO | Flushed zone water saturation | V/V |
| PERM | Permeability | MD |
| VCL | Volume of clay | V/V |

## Unit Conversions

| From | To | Multiply by |
|------|-----|-------------|
| FT | M | 0.3048 |
| G/CC | KG/M3 | 1000 |
| US/FT | US/M | 3.28084 |
| PU | V/V | 0.01 |
| MD | M2 | 9.869e-16 |
