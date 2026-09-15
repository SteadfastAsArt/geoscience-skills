---
name: pyleoclim
description: Analyse paleoclimate proxy time series with Pyleoclim, including irregular sampling, spectra and comparisons across uncertain chronologies. Use for proxy Series and EnsembleSeries analysis, spectral peaks and age-model sensitivity; use xarray for gridded climate fields.
license: MIT
metadata:
  version: "1.0.0"
  author: Geoscience Skills
  skill_type: domain
  tags: '["Paleoclimate", "Time Series", "Spectral Analysis"]'
  dependencies: '["pyleoclim==1.3.0"]'
  complements: '["xarray", "pooch"]'
  workflow_role: analysis
---

# Pyleoclim

Analyse proxy variability while retaining the chronology and sampling assumptions.
Version 1.3.0 requires Python 3.12 or newer; use an isolated environment.

## Inputs and method selection

Establish the proxy units, archive type, time direction and origin: years CE,
years before 1950 and ka BP are different coordinate systems. Record missing
values, duplicate times and age uncertainties before sorting or removing rows.
Do not interpolate across hiatuses silently. A proxy is not automatically a
calibrated temperature or precipitation observation.

Use Lomb–Scargle for an explicitly retained irregular chronology; use methods
requiring regular sampling only after justified resampling and sensitivity checks.
Compare spectral peaks with an appropriate autocorrelated null model, sampling
window and multiple-testing policy. Power alone is not a significance level.

## Irregular synthetic series

This deterministic 20-year sinusoid is an API and frequency-recovery check, not
a significance test on field data. Time is elapsed years, never a BP chronology.

```python
# example: irregular-spectrum
import numpy as np
import pyleoclim as pyleo

time_year = np.arange(200, dtype=float) + 0.15 * np.sin(np.arange(200))
proxy = np.sin(2 * np.pi * time_year / 20)
series = pyleo.Series(time=time_year, value=proxy, time_name="Elapsed time",
                     time_unit="year", value_name="Synthetic proxy",
                     value_unit="dimensionless", verbose=False)
frequency_per_year = np.linspace(0.01, 0.2, 1000)
spectrum = series.spectral(method="lomb_scargle", freq=frequency_per_year,
                           settings={"n50": 1, "window": "boxcar"})
valid_spectrum = np.isfinite(spectrum.amplitude)
if not valid_spectrum.any():
    raise ValueError("No finite spectral estimates")
peak_period_year = 1 / spectrum.frequency[valid_spectrum][
    np.argmax(spectrum.amplitude[valid_spectrum])]
```

The benchmark uses a single full-length, untapered segment. Pyleoclim's default
overlapping tapered segments smooth the spectrum; record that choice explicitly
when comparing peak locations or resolutions across methods.
The method can mark unstable edge estimates as NaN. Retain that mask and report
the usable frequency range; an unchecked `argmax` can select a NaN edge instead
of the signal peak.

## Chronology and uncertainty

For age ensembles, obtain defensible age realizations from the age model; do not
generate independent random age offsets that violate stratigraphic order. Analyse
each realization with the same documented settings, summarize frequency/phase
variation and separate age, measurement and model uncertainty. Correlation after
choosing a favorable age realization is subject to selection bias.

Keep original and processed values, excluded intervals, processing settings,
seeds and package versions. Report the spectral window and uncertainty assumptions
alongside figures. Consult the [official documentation](https://pyleoclim-util.readthedocs.io/en/latest/)
for methods available in the installed version.
