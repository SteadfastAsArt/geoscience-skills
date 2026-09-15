# MT transfer-function fixture

`test.edi` is copied byte for byte from the MIT-licensed
[mt_metadata regression data](https://github.com/MTgeophysics/mt_metadata/blob/40b897dc977f13ec0cd15f4606aada9f95396b3b/mt_metadata/data/transfer_functions/test.edi).
The exact commit, SHA-256 and retained upstream license are in `provenance.json`
and `UPSTREAM-LICENSE.txt`; copyright (c) 2020 JP.

The EDI identifies Phoenix station `14-IEB0537A`, Boulia/IEB, 2014-07-28.
It is a **field-derived upstream regression sample**, not the original instrument
time series. Its head declares WGS84, elevation 158 m (vertical datum unknown),
and mV/km/nT impedance units; INFO declares the positive time convention.
Its 80 frequencies are supplied with a 5-degree ZROT. No processing is undone
and no geological ground truth is inferred. The MT reader normalizes the station
identifier to `14_IEB0537A`.

Source orientation metadata is inconsistent: the original system information
gives Ey as 90 degrees true north, while INFO's `ey.measurement_azimuth` and
`translated_azimuth` give 116.61629962451384 degrees. The checks use the published
tensor and its 5-degree ZROT; they do not reconstruct acquisition channel geometry
or certify that those acquisition metadata are mutually consistent.

Tests also construct explicitly synthetic EDI records independently of the MTpy
writer. Those records check known impedance formulas, null sentinels, unknown
variance and output behavior; they are not labelled field observations.
