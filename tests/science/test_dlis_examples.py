"""Read real synthetic RP66 bytes and execute actual DLIS Markdown examples."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from dlisio import dlis
from dliswriter import enums
import lasio
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / 'tests/fixtures/domain_audits/dlis/synthetic.dlis'


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HELPER = load_module('dlis_export', 'dlisio/scripts/dlis_to_las.py')
GENERATOR = load_module('dlis_fixture', 'tests/fixtures/domain_audits/dlis/generate.py')


def example(path, heading):
    text = (ROOT / path).read_text()
    section = re.search(rf'^## {re.escape(heading)}\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    block = re.search(r'^```python\n(.*?)^```', section[1], re.M | re.S)
    namespace = {}
    exec(compile(block[1], str(path), 'exec'), namespace)
    return namespace


class DlisExamples(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / 'out.las'

    def export(self, source=FIXTURE, **kwargs):
        with contextlib.redirect_stderr(io.StringIO()):
            HELPER.dlis_to_las(source, self.output, **kwargs)
        return lasio.read(self.output)

    def test_inventory_selects_multiple_logical_files_and_frames(self):
        provenance = json.loads(FIXTURE.with_name('provenance.json').read_text())
        self.assertEqual(hashlib.sha256(FIXTURE.read_bytes()).hexdigest(), provenance['sha256'])
        rows = example('dlisio/SKILL.md', 'Select a logical file and frame')['inventory'](FIXTURE)
        self.assertEqual([(r['logical_file'], r['frame']) for r in rows], [(0, 0), (0, 1), (1, 0)])
        self.assertEqual(rows[0]['index_type'], 'BOREHOLE-DEPTH')
        self.assertEqual(rows[0]['channels'][-1][1:], ('mV', [4]))

    def test_documentation_keeps_array_shape_identity_and_nan_after_close(self):
        read = example('dlisio/SKILL.md', 'Read scalar and array channels')['read_frame']
        table, arrays, metadata = read(FIXTURE)
        np.testing.assert_array_equal(table['FRAMENO'], [1, 2, 3, 4])
        np.testing.assert_array_equal(table['DEPTH'], [1000, 1000.5, 1001.5, 1002])
        np.testing.assert_array_equal(arrays['T.CHANNEL-I.IMAGE-O.0-C.0'], np.arange(16.).reshape(4, 4))
        self.assertTrue(np.isnan(table['GAMMA_X.1.0'][2]))
        self.assertEqual(table['GAMMA_X.1.0'][1], -999.25)
        self.assertIn('T.CHANNEL-I.GAMMA_X-O.2-C.0', metadata['channels'])

    def test_las_preserves_identity_units_irregular_depth_and_missing_mask(self):
        log = self.export()
        self.assertEqual(log.keys(), ['DEPTH', 'GAMMA_X__O1_C0', 'GAMMA_X__O2_C0'])
        np.testing.assert_array_equal(log.index, [1000, 1000.5, 1001.5, 1002])
        np.testing.assert_allclose(log['GAMMA_X__O1_C0'], [10, -999.25, np.nan, 40], equal_nan=True)
        self.assertEqual(log.curves[0].unit, 'M')
        self.assertEqual(log.well.STEP.value, 0)
        self.assertNotEqual(log.well.NULL.value, -999.25)
        self.assertIn('T.CHANNEL-I.GAMMA_X-O.1-C.0', log.curves[1].descr)

    def test_curve_selection_keeps_depth_and_explicit_vendor_null(self):
        log = self.export(curves=['T.CHANNEL-I.GAMMA_X-O.1-C.0'], null_value=-999.25)
        self.assertEqual(log.keys(), ['DEPTH', 'GAMMA_X__O1_C0'])
        np.testing.assert_array_equal(np.isnan(log.data[:, 1]), [False, True, True, False])
        self.assertIn('vendor null marker -999.25', log.other)

    def test_duplicate_name_and_array_requests_fail(self):
        for selected in [['GAMMA_X'], ['IMAGE'], ['MISSING']]:
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                self.export(curves=selected)
        self.assertFalse(self.output.exists())

    def test_second_logical_file_and_frame_are_not_merged(self):
        log = self.export(logical_file_index=1)
        np.testing.assert_array_equal(log.index, [20, 21, 22, 23])
        np.testing.assert_array_equal(log['GR'], [101, 102, 103, 104])
        self.assertEqual(log.curves[0].unit, 'FT')
        log = self.export(frame_index=1)
        self.assertEqual(log.keys(), ['DEPTH2', 'GAMMA2'])
        np.testing.assert_array_equal(log['GAMMA2'], [11, 22, 33, 44])

    def test_descending_depth_preserved_but_duplicates_and_time_units_rejected(self):
        source = Path(self.temp.name) / 'generated.dlis'
        GENERATOR.generate(source, depths=[1002, 1001.5, 1000.5, 1000])
        np.testing.assert_array_equal(self.export(source).index, [1002, 1001.5, 1000.5, 1000])
        GENERATOR.generate(source, depths=[1000, 1000, 1001, 1002])
        with self.assertRaisesRegex(ValueError, 'strictly monotonic'):
            self.export(source)
        GENERATOR.generate(source, unit='s', index_type=enums.FrameIndexType.NON_STANDARD)
        with self.assertRaisesRegex(ValueError, 'no depth index'):
            self.export(source)
        with self.assertRaisesRegex(ValueError, 'Unsupported depth unit'):
            self.export(source, depth_channel='DEPTH')

    def test_cli_failure_status_and_input_overwrite_protection(self):
        before = FIXTURE.read_bytes()
        with self.assertRaisesRegex(ValueError, 'overwrite'):
            HELPER.dlis_to_las(FIXTURE, FIXTURE)
        self.assertEqual(FIXTURE.read_bytes(), before)
        result = subprocess.run([sys.executable, str(ROOT / 'dlisio/scripts/dlis_to_las.py'),
                                 str(FIXTURE), str(self.output), '--frame', '99'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Frame index', result.stderr)
        self.assertFalse(self.output.exists())

    def test_float64_depth_precision_survives_las_write(self):
        source = Path(self.temp.name) / 'precise.dlis'
        depths = np.array([1000., 1000.0000001, 1000.0000002, 1000.0000003])
        GENERATOR.generate(source, depths=depths)
        log = self.export(source)
        np.testing.assert_array_equal(log.index, depths)
        self.assertTrue(np.all(np.diff(log.index) > 0))
        np.testing.assert_allclose(np.diff(log.index), log.well.STEP.value, atol=1e-12)


if __name__ == '__main__':
    unittest.main()
