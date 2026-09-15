"""Actual GEOFON waveform processing, with explicit instrument and time units."""

import numpy as np
from obspy import UTCDateTime, read, read_inventory

from field_case_support import verify_case


def load_waveform(directory=None):
    directory, provenance = verify_case("seismic_waveform", directory)
    stream = read(str(directory / "GE.MATE.BHZ.20160824.mseed"))
    inventory = read_inventory(str(directory / "GE.MATE.BHZ.20160824.xml"))
    if len(stream) != 1 or stream.get_gaps() or np.ma.isMaskedArray(stream[0].data):
        raise ValueError("Expected one contiguous, unmasked observed trace")
    trace = stream[0]
    if trace.id != "GE.MATE..BHZ" or not np.isfinite(trace.data).all():
        raise ValueError("Unexpected waveform identity or missing samples")
    response = inventory.get_response(trace.id, trace.stats.starttime)
    if (response.instrument_sensitivity.input_units.upper() != "M/S"
            or response.instrument_sensitivity.output_units.upper() != "COUNTS"):
        raise ValueError("Expected a velocity-to-counts instrument response")
    return trace, inventory, provenance


def contained_window(trace, start, end):
    """Select actual samples wholly inside bounds; do not invent sample alignment."""
    start, end = UTCDateTime(start), UTCDateTime(end)
    if start >= end or start < trace.stats.starttime or end > trace.stats.endtime:
        raise ValueError("Window must be ordered and within the observed trace")
    if np.ma.isMaskedArray(trace.data) or not np.isfinite(trace.data).all():
        raise ValueError("Do not interpolate or silently fill waveform gaps")
    return trace.copy().trim(start, end, nearest_sample=False, pad=False)


def corrected_velocity(trace, inventory):
    """Deconvolve all response stages; return band-limited velocity in m/s.

    Frequency corners are fixed before validation. This excludes endpoint and
    out-of-band ground motion, and supplies no total instrument-error model.
    """
    result = trace.copy()
    result.remove_response(inventory=inventory, output="VEL", water_level=None,
                           pre_filt=(0.05, 0.1, 4.0, 5.0), zero_mean=True,
                           taper=True, taper_fraction=0.05)
    result.stats.units = "m/s"
    if not np.isfinite(result.data).all():
        raise ValueError("Instrument correction produced nonfinite ground velocity")
    return result


def waveform_report():
    trace, inventory, _ = load_waveform()
    velocity = corrected_velocity(trace, inventory)
    noise = contained_window(velocity, "2016-08-24T01:35:10", "2016-08-24T01:36:10")
    later = contained_window(velocity, "2016-08-24T01:37:00", "2016-08-24T01:38:00")
    return {"trace": trace.id, "samples": trace.stats.npts,
            "observed_start_utc": str(trace.stats.starttime),
            "sample_rate_hz": trace.stats.sampling_rate,
            "noise_window_rms_m_s": float(np.sqrt(np.mean(noise.data ** 2))),
            "later_window_rms_m_s": float(np.sqrt(np.mean(later.data ** 2))),
            "amplitude_uncertainty": "Not supplied by this snapshot; RMS is not a confidence interval.",
            "scope": "Recorded waveform, timestamps, spectral energy and instrument correction; "
                     "no event detection, arrival picking or source inversion claim."}


if __name__ == "__main__":
    import json
    print(json.dumps(waveform_report(), indent=2))
