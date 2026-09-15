# Processing details and supported scope

## Sampling before filtering

Record sample count, trace order, actual sample interval and time origin, line
spacing/positions, antenna separation, time-zero policy, CRS and vertical datum.
GPRPy reader axes are not a substitute for acquisition metadata. For example,
its MALA reader substitutes a spacing of 1 when the header spacing is effectively
zero. The helper retains native axes separately and uses only explicitly
supplied physical sampling for derived axes; unknown coordinates remain
sample/trace indices.

The helper's sample interval and spacing are authoritative user-supplied
metadata, not estimates fitted from amplitudes. Record any disagreement with
vendor headers before physical interpretation. Raw source bytes remain intact.

## Dewow and background

`profile.dewow(window)` takes a number of samples. In the pinned implementation,
a local window argument `w` uses `2*ceil(w/2)+1` interior samples, with distinct
edge windows. Thus `w=4` uses a five-sample interior mean. A window at least as
large as the trace subtracts its complete mean. The helper records the effective
support and stores the intermediate array. Tests independently check the local
interior convolution and full-trace zero-mean property; edge amplitudes are not
claimed to have the same filter response as interior samples.

`profile.remMeanTrace(ntraces)` subtracts a mean across traces. The full-profile
case has zero mean across traces at each sample; this can also erase a true
horizontal reflector. Neither operation is automatically appropriate to every
survey. Window parameters must refer to samples/traces, not ns or metres.

## Gain and depth scenarios

`tpowGain(power)` multiplies by `twtt**power`, using GPRPy time values in ns.
Changing the time unit changes the numerical gain. This operation is display
scaling; it does not preserve relative amplitudes across travel times or
establish an attenuation model. AGC also changes amplitude relationships and
requires a separately checked zero-energy policy. The tested helper does not
apply AGC, migration, bandpass filtering or topographic shifts.

For an explicit constant velocity in m/ns and zero source-receiver offset,
`setVelocity` computes half the two-way path length. A reference depth or picked
reflection is not established just by choosing a plausible velocity. Negative
or unresolved time prevents the helper's depth scenario; no synthetic time-zero
correction is silently applied to the observed line.

## Output audit

`profile.npz` stores numeric arrays without Python objects, including raw and
processed amplitudes and every requested intermediate stage. Known coordinates
use explicit `twtt_ns`, `position_m` and `scenario_depth_m` names. Uncalibrated
field SEG-Y uses `sample_index` and `trace_index`; original interval, delay,
coordinate scalar/units and source coordinates remain encoded arrays, without
an inferred CRS. `processing.json` records source/sidecar hashes, raw header
summary, library version, parameters, scope and the archive checksum.

Read the result with the helper's `read_result(output_dir)` or independently
with NumPy and JSON, and verify shape, units and checksums. NPZ is the tested
portable array export. A PNG is only a visualization; SEG-Y export would require
a separate writer and careful handling of radar sample-time conventions.

## Tested source

The project tests GPRPy **1.0.14**, source commit
`3b1f75eba820764b2147568fc0cc40f3a47919d5`. It is not available from the PyPI
`gprpy` project endpoint at the verification date. Install this source only in
an isolated scientific environment, after the ordinary dependency pins; skill
installation does not install this Python package.

```bash
python -m pip install https://github.com/NSGeophysics/GPRPy/archive/3b1f75eba820764b2147568fc0cc40f3a47919d5.zip
```

The tested environment uses Python 3.11, NumPy 1.26.4, SciPy 1.17.1,
Matplotlib 3.10.8 and segyio 1.9.14. Optional migration/GUI paths are not exercised;
the upstream optional-migration notice does not imply migration validation.

[Fixed GPRPy implementation](https://github.com/NSGeophysics/GPRPy/blob/3b1f75eba820764b2147568fc0cc40f3a47919d5/gprpy/gprpy.py),
[fixed processing operators](https://github.com/NSGeophysics/GPRPy/blob/3b1f75eba820764b2147568fc0cc40f3a47919d5/gprpy/toolbox/gprpyTools.py),
[segyio API](https://segyio.readthedocs.io/en/stable/), checked 2026-09-15.
The source software license does not license arbitrary vendor field files.
