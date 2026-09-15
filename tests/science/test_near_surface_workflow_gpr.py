"""Actual raw-file→GPRPy→NPZ/JSON workflow; real observations and separate truth."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'tests/fixtures/workflows/near_surface/gpr'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


HELPER = module('gpr_process', ROOT / 'gprpy/scripts/process_gpr.py')
GENERATOR = module('gpr_fixture', FIXTURE / 'generate.py')


class NearSurfaceGPRTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='geoscience-gpr-workflow-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.source, self.metadata, expected = GENERATOR.generate(self.directory / 'raw')
        self.expected = np.asarray(expected).T
        self.output = self.directory / 'result'

    def run_controlled(self, **kwargs):
        HELPER.process_gpr(self.source, self.output, self.metadata, **kwargs)
        return HELPER.read_result(self.output)

    def test_field_fixture_has_dataset_license_and_fixed_original_bytes(self):
        manifest = json.loads((FIXTURE / 'provenance.json').read_text())
        for name, record in manifest['files'].items():
            raw = (FIXTURE / name).read_bytes()
            self.assertEqual(sha256(raw).hexdigest(), record['sha256'])
        upstream = json.loads((FIXTURE / 'zenodo-record.json').read_text())
        self.assertEqual(upstream['metadata']['license']['id'], 'cc-by-4.0')
        self.assertEqual(upstream['doi'], '10.5281/zenodo.18769571')

    def test_real_segy_samples_match_independent_binary_decoder_and_dc_oracle(self):
        source = FIXTURE / 'site2_ground_p1.SGY'
        encoded = source.read_bytes()
        # Source SEG-Y format 2, big-endian int32, no extended textual headers.
        self.assertEqual(struct.unpack_from('>H', encoded, 3224)[0], 2)
        ns = struct.unpack_from('>H', encoded, 3220)[0]
        self.assertEqual(ns, 494)
        size = 240 + ns * 4
        self.assertEqual((len(encoded) - 3600) % size, 0)
        original = np.stack([np.frombuffer(encoded, dtype='>i4', count=ns,
                             offset=3600 + trace * size + 240)
                             for trace in range((len(encoded) - 3600) // size)], axis=1)
        HELPER.process_gpr(source, self.output, FIXTURE / 'field_sampling.json', dewow_samples=ns)
        result, report = HELPER.read_result(self.output)
        np.testing.assert_array_equal(result['raw_amplitude'], original)
        np.testing.assert_allclose(result['processed_amplitude'], original - original.mean(axis=0), atol=1e-11)
        np.testing.assert_allclose(result['processed_amplitude'].mean(axis=0), 0, atol=1e-10)
        self.assertEqual(original.shape, (494, 312))
        self.assertFalse(report['known_time_ns'])
        self.assertFalse(report['known_profile_m'])
        self.assertNotIn('scenario_depth_m', result)
        np.testing.assert_array_equal(result['interval_encoded'], 293)
        np.testing.assert_array_equal(result['coordinate_units_code'], 0)
        self.assertEqual(source.read_bytes(), encoded)

    def test_native_mala_units_order_and_generated_impulse_depth_roundtrip(self):
        arrays, report = self.run_controlled(dewow_samples=64, velocity_m_ns=0.1)
        np.testing.assert_array_equal(arrays['raw_amplitude'], self.expected)
        np.testing.assert_array_equal(arrays['twtt_ns'], np.arange(64) * 2.5)
        np.testing.assert_array_equal(arrays['position_m'], np.arange(9) * 0.25)
        np.testing.assert_array_equal(arrays['native_twtt'], arrays['twtt_ns'])
        np.testing.assert_array_equal(np.argmax(arrays['processed_amplitude'], axis=0), 32)
        # Known 80 ns two-way impulse: one-way path is 4 m at the declared 0.1 m/ns.
        self.assertEqual(arrays['scenario_depth_m'][32], 4.0)
        np.testing.assert_allclose(arrays['scenario_depth_m'] / 0.1 * 2, arrays['twtt_ns'])
        self.assertTrue(report['known_time_ns'] and report['known_profile_m'])
        self.assertIn('3b1f75eba820764b2147568fc0cc40f3a47919d5', report['library_source']['url'])

    def test_local_dewow_window_is_samples_with_declared_actual_support(self):
        arrays, report = self.run_controlled(dewow_samples=4)
        # Independent convolution checks the interior of GPRPy's actual 5-point
        # kernel. Special upstream edge windows are retained, not hidden.
        expected = np.stack([np.convolve(trace, np.ones(5) / 5, mode='same')
                             for trace in self.expected.T], axis=1)
        np.testing.assert_allclose(arrays['after_dewow'][3:-3],
                                   (self.expected - expected)[3:-3], atol=1e-10)
        self.assertEqual(report['operations'][0]['interior_support_samples'], 5)

    def test_background_and_time_gain_record_distinct_changed_amplitudes(self):
        arrays, report = self.run_controlled(background_traces=9, gain_power=1.0)
        expected = self.expected - self.expected.mean(axis=1, keepdims=True)
        np.testing.assert_allclose(arrays['after_background'], expected)
        np.testing.assert_allclose(arrays['processed_amplitude'], expected * (np.arange(64) * 2.5)[:, None])
        self.assertEqual(len(report['operations']), 2)

    def test_unknown_field_time_cannot_become_depth_or_time_gain(self):
        for kwargs in ({'velocity_m_ns': 0.1}, {'gain_power': 1.0}):
            with self.subTest(kwargs=kwargs), self.assertRaisesRegex(ValueError, 'known'):
                HELPER.process_gpr(FIXTURE / 'site2_ground_p1.SGY', self.output,
                                   FIXTURE / 'field_sampling.json', **kwargs)
            self.assertFalse(self.output.exists())

    def test_invalid_windows_and_unknown_formats_fail_before_output(self):
        for value in (0, -1, 65, 2.5):
            with self.subTest(window=value), self.assertRaises(ValueError):
                self.run_controlled(dewow_samples=value)
        with self.assertRaisesRegex(ValueError, 'supports'):
            HELPER.process_gpr(self.source.with_suffix('.gpr'), self.output, self.metadata)
        self.assertFalse(self.output.exists())

    def test_cli_real_export_readback_and_existing_output_failure(self):
        command = [sys.executable, str(ROOT / 'gprpy/scripts/process_gpr.py'), str(self.source),
                   '--metadata', str(self.metadata), '--output', str(self.output), '--dewow-samples', '64']
        completed = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        arrays, _ = HELPER.read_result(self.output)
        np.testing.assert_array_equal(arrays['raw_amplitude'], self.expected)
        before = (self.output / 'profile.npz').read_bytes()
        repeated = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(repeated.returncode, 0)
        self.assertEqual((self.output / 'profile.npz').read_bytes(), before)

    def test_corrupted_export_is_not_reported_as_valid(self):
        self.run_controlled()
        with (self.output / 'profile.npz').open('ab') as output:
            output.write(b'corrupt')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            HELPER.read_result(self.output)


if __name__ == '__main__':
    unittest.main()
