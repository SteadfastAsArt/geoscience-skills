"""Real GE.MATE data: use the isolated core stack; no network during tests."""

from pathlib import Path
import tempfile
import unittest
from xml.etree import ElementTree

import numpy as np
from obspy import UTCDateTime, read
from scipy.signal import periodogram

from field_case_support import verify_case
from field_waveform_support import contained_window, corrected_velocity, load_waveform, waveform_report


class FieldWaveformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trace, cls.inventory, cls.provenance = load_waveform()
        cls.velocity = corrected_velocity(cls.trace, cls.inventory)

    def test_original_snapshot_and_network_data_license(self):
        directory, metadata = verify_case("seismic_waveform")
        self.assertEqual(metadata["dataset"]["license"], "CC-BY-4.0")
        self.assertEqual(metadata["dataset"]["doi"], "10.14470/TR560404")
        self.assertEqual(metadata["files"]["GE.MATE.BHZ.20160824.mseed"]["sha256"],
                         "99f5619ca6823f1b4a6b8ec49e7c2bfb6d27803359db144ee6916e188bd81ec4")
        # Read source XML independently of ObsPy's inventory decoder.
        xml = ElementTree.parse(directory / "GE.MATE.BHZ.20160824.xml")
        ns = {"s": "http://www.fdsn.org/xml/station/1"}
        channel = xml.find(".//s:Channel", ns)
        self.assertEqual(float(channel.find("s:SampleRate", ns).text), 20.0)
        self.assertEqual(float(channel.find("s:Dip", ns).text), -90.0)
        self.assertEqual(float(channel.find("s:Depth", ns).text), 5.0)
        self.assertEqual(float(channel.find("s:Elevation", ns).text), 494.0)
        sensitivity = channel.find("s:Response/s:InstrumentSensitivity", ns)
        source_gain = float(sensitivity.find("s:Value", ns).text)
        self.assertEqual(source_gain, 588000000.0)
        self.assertEqual(sensitivity.find("s:InputUnits/s:Name", ns).text, "M/S")
        self.assertEqual(sensitivity.find("s:OutputUnits/s:Name", ns).text, "COUNTS")
        actual = self.inventory[0][0][0].response.instrument_sensitivity
        self.assertEqual(actual.value, source_gain)

    def test_archive_padding_and_fractional_sample_phase_are_preserved(self):
        trace = self.trace
        self.assertEqual(trace.stats.npts, 6047)
        self.assertEqual(trace.stats.starttime, UTCDateTime("2016-08-24T01:34:57.895"))
        self.assertEqual(trace.stats.endtime.ns - trace.stats.starttime.ns,
                         (6047 - 1) * 50_000_000)
        start, end = UTCDateTime("2016-08-24T01:35:00"), UTCDateTime("2016-08-24T01:40:00")
        actual = contained_window(trace, start, end)
        # Integer nanoseconds provide an independent oracle for inclusion.
        times = trace.stats.starttime.ns + np.arange(6047, dtype=np.int64) * 50_000_000
        selected = (times >= start.ns) & (times <= end.ns)
        np.testing.assert_array_equal(actual.data, trace.data[selected])
        self.assertEqual(actual.stats.starttime.ns, int(times[selected][0]))
        self.assertNotEqual(actual.stats.starttime, start)

    def test_mseed_roundtrip_retains_observed_samples_and_time(self):
        with tempfile.TemporaryDirectory(prefix="geoscience-field-waveform-") as directory:
            path = Path(directory) / "observed.mseed"
            self.trace.write(str(path), format="MSEED", encoding="STEIM2")
            actual = read(str(path))[0]
            np.testing.assert_array_equal(actual.data, self.trace.data)
            self.assertEqual(actual.stats.starttime, self.trace.stats.starttime)
            self.assertEqual(actual.stats.endtime, self.trace.stats.endtime)
            self.assertEqual(actual.id, self.trace.id)

    def test_velocity_calibration_uses_all_stages_and_preserves_time_axis(self):
        self.assertEqual(self.velocity.stats.units, "m/s")
        self.assertEqual(self.velocity.stats.npts, self.trace.stats.npts)
        self.assertEqual(self.velocity.stats.starttime, self.trace.stats.starttime)
        self.assertEqual(self.velocity.stats.endtime, self.trace.stats.endtime)
        self.assertTrue(np.isfinite(self.velocity.data).all())
        self.assertTrue(any("remove_response" in step for step in self.velocity.stats.processing))
        self.assertGreater(float(np.std(self.velocity.data)), 0)

    def test_sensor_response_agrees_with_independent_pole_zero_formula(self):
        response = self.inventory[0][0][0].response
        stage = response.response_stages[0]
        frequencies = np.array([0.1, 1.0, 4.0])
        s = 2j * np.pi * frequencies
        numerator = np.prod(s[:, None] - np.asarray(stage.zeros), axis=1)
        denominator = np.prod(s[:, None] - np.asarray(stage.poles), axis=1)
        reference = 2j * np.pi * stage.stage_gain_frequency
        reference_gain = abs(np.prod(reference - np.asarray(stage.zeros))
                             / np.prod(reference - np.asarray(stage.poles)))
        expected = stage.stage_gain * numerator / denominator / reference_gain
        # This stage-only calculation intentionally excludes digitizer gain. Its
        # mismatch with the overall counts sensitivity is not a sensor fault.
        actual = response.get_evalresp_response_for_frequencies(
            frequencies, output="VEL", start_stage=1, end_stage=1,
            hide_sensitivity_mismatch_warning=True)
        np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-10)

    def test_one_sided_spectral_density_conserves_observed_variance(self):
        values = self.velocity.data
        frequencies, density = periodogram(values, fs=20.0, window="boxcar",
                                            detrend="constant", scaling="density")
        # Discrete Parseval identity: PSD units are (m/s)^2/Hz. Do not use
        # trapezoidal endpoint half-weights for this discrete-bin equality.
        variance_from_spectrum = np.sum(density) * (frequencies[1] - frequencies[0])
        self.assertAlmostEqual(variance_from_spectrum / np.var(values), 1.0, places=12)
        report = waveform_report()
        self.assertGreater(report["later_window_rms_m_s"], report["noise_window_rms_m_s"])
        self.assertIn("Not supplied", report["amplitude_uncertainty"])

    def test_gaps_and_extrapolated_time_requests_fail(self):
        with self.assertRaises(ValueError):
            contained_window(self.trace, self.trace.stats.starttime - 1, self.trace.stats.endtime)
        broken = self.trace.copy()
        broken.data = np.ma.array(broken.data, mask=False)
        broken.data.mask[10] = True
        with self.assertRaisesRegex(ValueError, "gaps"):
            contained_window(broken, broken.stats.starttime, broken.stats.endtime)


if __name__ == "__main__":
    unittest.main()
