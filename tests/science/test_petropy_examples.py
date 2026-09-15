"""Configured real PetroPy inverse mineral model against a known forward mixture."""
import copy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

import lasio
import numpy as np
import petropy as pp

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / 'petropy/references/example_config.json'
spec = importlib.util.spec_from_file_location('petro_eval', ROOT / 'petropy/scripts/formation_evaluation.py')
HELPER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(HELPER)


def example():
    text = (ROOT / 'petropy/SKILL.md').read_text()
    section = re.search(r'^## Run a configured model\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    block = re.search(r'^```python\n(.*?)^```', section[1], re.M | re.S)
    namespace = {}
    exec(compile(block[1], 'petropy/SKILL.md:Run a configured model', 'exec'), namespace)
    return namespace['run_configured']


class PetroPyExamples(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.source = self.directory / 'synthetic.las'
        self.config = json.loads(CONFIG.read_text())
        # Six observed depths define five intervals; spacing is deliberately irregular.
        depth = np.array([5000., 5000.25, 5000.75, 5001.5, 5002., 5002.5])
        raw = lasio.LASFile()
        for key, unit, values in [('DEPT', 'FT', depth), ('GR_N', 'API', np.full(6, 10.)),
                                 ('NPHI_N', 'V/V', np.full(6, .174)), ('RHOB_N', 'G/CC', np.full(6, 2.32)),
                                 ('RESDEEP_N', 'OHMM', np.full(6, 5.))]:
            raw.add_curve(key, values, unit=unit)
        raw.write(str(self.source), version=2.0, fmt='%.12g', STEP=0)
        fluid_log = pp.Log(str(self.source))
        fluid_log.fluid_properties(top=5000., bottom=5003., **self.config['fluid'])
        # Independent known bulk fractions: quartz .65, calcite .15, water .20.
        # PVT comes from the actual fluid API; this checks model consistency,
        # not the empirical PVT correlation's accuracy on real reservoirs.
        raw['RHOB_N'] = .65 * 2.65 + .15 * 2.71 + .2 * fluid_log['RHO_W']
        raw['NPHI_N'] = .65 * (-.04) + .15 * 0. + .2 * fluid_log['NPHI_W']
        raw['RESDEEP_N'] = fluid_log['RW'] / .2 ** 2
        raw.write(str(self.source), version=2.0, fmt='%.12g', STEP=0)

    def assert_mixture(self, log, valid):
        for key, expected in [('PHIE', .2), ('SW', 1.), ('BVQTZ', .65), ('BVCLC', .15),
                              ('BVW', .2), ('BVH', 0.), ('BVCLAY', 0.), ('BVOM', 0.), ('BVPYR', 0.)]:
            with self.subTest(curve=key):
                np.testing.assert_allclose(log[key][valid], expected, atol=2e-5)
        total = sum(log[k] for k in ('BVQTZ', 'BVCLC', 'BVCLAY', 'BVOM', 'BVPYR', 'PHIE'))
        np.testing.assert_allclose(total[valid], 1, atol=1e-10)
        np.testing.assert_allclose((log['BVW'] + log['BVH'])[valid], log['PHIE'][valid], atol=1e-10)
        np.testing.assert_allclose((log['BVWI'] + log['BVWF'])[valid], log['BVW'][valid], atol=1e-10)

    def test_actual_markdown_runs_configured_two_mineral_model(self):
        log = example()(self.source, CONFIG)
        self.assert_mixture(log, np.arange(5))
        self.assertTrue(np.isnan(log['PHIE'][-1]))

    def test_helper_closure_and_feet_temperature_pressure(self):
        log, summary = HELPER.evaluate(self.source, self.config)
        self.assert_mixture(log, np.arange(5))
        np.testing.assert_allclose(log['RES_TEMP'][:5], 67 + .015 * log.index[:5])
        np.testing.assert_allclose(log['PORE_PRESS'][:5], .5 * log.index[:5])
        self.assertEqual(summary['evaluated_samples'], 5)
        self.assertLess(summary['volume_closure_max_error'], 1e-10)
        self.assertEqual(summary['net_pay_ft'], 0)
        self.assertTrue(np.isnan(log['PAY'][-1]))

    def test_missing_sample_mask_and_irregular_interval_thickness(self):
        raw = lasio.read(str(self.source))
        raw['RHOB_N'][2] = np.nan
        raw.write(str(self.source), version=2.0, fmt='%.12g', STEP=0)
        self.config['pay']['sw_max'] = 1.
        log, summary = HELPER.evaluate(self.source, self.config)
        np.testing.assert_array_equal(np.isnan(log['PHIE']), [False, False, True, False, False, True])
        np.testing.assert_array_equal(np.isnan(log['PAY']), [False, False, True, False, False, True])
        self.assert_mixture(log, [0, 1, 3, 4])
        self.assertEqual(summary['missing_samples'], 1)
        self.assertAlmostEqual(summary['unknown_interval_ft'], .75)
        self.assertAlmostEqual(summary['net_pay_ft'], 1.75)

    def test_input_units_endpoints_and_measured_density_are_required(self):
        wrong_basis = copy.deepcopy(self.config)
        wrong_basis['depth_basis'] = 'measured_depth'
        with self.assertRaisesRegex(ValueError, 'deviated-well MD'):
            HELPER.evaluate(self.source, wrong_basis)
        wrong = copy.deepcopy(self.config)
        wrong['interval_ft'][1] = 5002.4
        with self.assertRaisesRegex(ValueError, 'match sampled depths'):
            HELPER.evaluate(self.source, wrong)
        raw = lasio.read(str(self.source))
        raw.curves[0].unit = 'M'
        raw.write(str(self.source), version=2.0, fmt='%.12g', STEP=0)
        with self.assertRaisesRegex(ValueError, 'depth in ft'):
            HELPER.evaluate(self.source, self.config)
        raw.curves[0].unit = 'FT'
        raw.delete_curve('RHOB_N')
        raw.add_curve('DPHI_N', np.full(6, .2), unit='V/V')
        raw.write(str(self.source), version=2.0, fmt='%.12g', STEP=0)
        with self.assertRaisesRegex(ValueError, 'measured, normalized'):
            HELPER.evaluate(self.source, self.config)

    def test_missing_config_unknown_parameters_and_uncalibrated_calcite_fail(self):
        with self.assertRaises(FileNotFoundError):
            HELPER.load_config(self.directory / 'absent.json')
        wrong = copy.deepcopy(self.config)
        wrong['multimineral']['rho_calcite'] = 2.71
        with self.assertRaisesRegex(ValueError, 'Unknown parameters'):
            HELPER.evaluate(self.source, wrong)
        del wrong['multimineral']['rho_calcite']
        del wrong['multimineral']['rho_clc']
        with self.assertRaisesRegex(ValueError, 'endpoints'):
            HELPER.evaluate(self.source, wrong)

    def test_cli_las_readback_provenance_and_input_protection(self):
        output = self.directory / 'evaluated.las'
        command = [sys.executable, str(ROOT / 'petropy/scripts/formation_evaluation.py'), str(self.source),
                   '--config', str(CONFIG), '--output', str(output)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        log = lasio.read(str(output))
        self.assert_mixture(log, np.arange(5))
        self.assertTrue(np.isnan(log['PHIE'][-1]))
        summary = json.loads(output.with_suffix('.json').read_text())
        self.assertEqual(summary['depth_basis'], 'tvd_below_surface')
        self.assertEqual(log.well.STEP.value, 0)
        self.assertEqual(summary['resolved_multimineral']['rho_clc'], 2.71)
        self.assertEqual(len(summary['source_sha256']), 64)
        before = self.source.read_bytes()
        result = subprocess.run(command[:-1] + [str(self.source)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('overwrite', result.stderr)
        self.assertEqual(self.source.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
