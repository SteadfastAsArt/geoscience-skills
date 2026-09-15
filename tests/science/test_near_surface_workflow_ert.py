"""Field observations→real inversion→complete read-back response/residual artifacts."""
import csv
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd
from scipy.stats import chi2

from field_ert_support import image_series_response, load_survey, RHO
from near_surface_ert_support import GEOMETRY_NOTE, prepare_field_inputs

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'workflows/near-surface-geophysics/scripts/ert_layered_diagnostic.py'
spec = importlib.util.spec_from_file_location('ert_workflow', SCRIPT)
HELPER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(HELPER)


class NearSurfaceERTTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='geoscience-ert-workflow-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.directory = Path(cls.temp.name)
        cls.observations, cls.electrodes = prepare_field_inputs(cls.directory / 'input')
        cls.output = cls.directory / 'field-result'
        HELPER.run_workflow(cls.observations, cls.electrodes, cls.output, geometry_note=GEOMETRY_NOTE)
        cls.responses, cls.report = HELPER.read_result(cls.output)

    def test_normalized_input_retains_source_identity_values_and_negative_voltage(self):
        original = load_survey()[0]
        responses = self.responses
        np.testing.assert_array_equal(responses.measurement_id, original.meas_num)
        np.testing.assert_array_equal(responses.rhoa_ohm_m, original[RHO])
        np.testing.assert_array_equal(responses.voltage_mV, original.iloc[:, 8])
        np.testing.assert_array_equal(responses.current_mA, original.iloc[:, 9])
        self.assertGreater((responses.loc[responses.included, 'voltage_mV'] < 0).sum(), 100)
        self.assertEqual(self.report['counts'], {'original': 318, 'retained': 316, 'holdout': 74})

    def test_csv_readback_independently_reconstructs_residual_and_report(self):
        with (self.output / 'responses.csv').open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        keep = [row for row in rows if row['included'] == 'True']
        observed = np.array([float(row['rhoa_ohm_m']) for row in keep])
        predicted = np.array([float(row['predicted_all_fit_ohm_m']) for row in keep])
        sigma = np.array([float(row['log_sigma']) for row in keep])
        standardized = np.log(predicted / observed) / sigma
        np.testing.assert_allclose(standardized, [float(row['normalized_log_residual']) for row in keep], atol=1e-12)
        self.assertAlmostEqual(float(standardized @ standardized), self.report['chi_square'], places=8)
        self.assertEqual(self.report['degrees_of_freedom'], len(keep) - 3)
        excluded = [row for row in rows if row['included'] == 'False']
        self.assertEqual(len(excluded), 2)
        self.assertTrue(all(row['exclusion_reason'] and not row['predicted_all_fit_ohm_m'] for row in excluded))

    def test_saved_model_reproduces_saved_predictions_and_rejection(self):
        _, _, geometry = HELPER.load_inputs(self.observations, self.electrodes)
        retained = self.responses.included.to_numpy()
        predicted = np.asarray(HELPER.forward_operator(geometry[:, retained]).response(
                               self.report['model_h_rho_top_rho_bottom']))
        np.testing.assert_allclose(predicted, self.responses.loc[retained, 'predicted_all_fit_ohm_m'], rtol=1e-12)
        self.assertEqual(self.report['fit_status'], 'combined_model_and_error_assumptions_rejected')
        self.assertTrue(self.report['local_refinement']['converged'])
        self.assertEqual(self.report['local_refinement']['rank'], 3)
        self.assertIsNone(self.report['ground_truth'])

    def test_held_out_targets_cannot_change_training_model(self):
        table = pd.read_csv(self.observations)
        test = self.responses.holdout.to_numpy()
        training = self.responses.included.to_numpy() & ~test
        self.assertTrue(set(self.responses.loc[test, 'group']).isdisjoint(self.responses.loc[training, 'group']))
        table.loc[test, 'rhoa_ohm_m'] *= 1.3
        changed = self.directory / 'changed-targets.csv'
        table.to_csv(changed, index=False)
        output = self.directory / 'holdout-perturbation'
        result = HELPER.run_workflow(changed, self.electrodes, output, geometry_note=GEOMETRY_NOTE)
        np.testing.assert_allclose(result['training_only_model'], self.report['training_only_model'], rtol=1e-12)
        reread, _ = HELPER.read_result(output)
        np.testing.assert_allclose(reread.loc[test, 'predicted_holdout_ohm_m'],
                                   self.responses.loc[test, 'predicted_holdout_ohm_m'], rtol=1e-12)

    def test_separate_image_series_truth_recovers_parameters_with_declared_noise(self):
        original = load_survey()[0]
        table = pd.read_csv(self.observations)
        truth = np.array([5., 100., 300.])
        signal = image_series_response(original, *truth)
        refined = image_series_response(original, *truth, terms=160)
        np.testing.assert_allclose(signal, refined, rtol=1e-13)
        rng = np.random.default_rng(20260915)
        values = signal * np.exp(rng.normal(0, .02, len(signal)))
        table.rhoa_ohm_m = values
        source = self.directory / 'controlled-synthetic.csv'
        table.to_csv(source, index=False)
        _, _, geometry = HELPER.load_inputs(source, self.electrodes)
        model, predicted = HELPER.fit(geometry, values, np.full(len(values), .02), [3., 150., 200.])
        np.testing.assert_allclose(model, truth, rtol=.05)
        statistic = np.sum((np.log(predicted / values) / .02) ** 2)
        lower, upper = chi2.ppf([.005, .995], len(values) - 3)
        self.assertTrue(lower < statistic < upper)

    def test_invalid_geometry_errors_and_existing_output_fail(self):
        with self.assertRaisesRegex(ValueError, 'new output'):
            HELPER.run_workflow(self.observations, self.electrodes, self.output, geometry_note=GEOMETRY_NOTE)
        bad = pd.read_csv(self.observations)
        bad['a'] = bad['a'].astype(float)
        bad.loc[0, 'a'] = 1.5
        source = self.directory / 'bad-identities.csv'
        bad.to_csv(source, index=False)
        with self.assertRaisesRegex(ValueError, 'integers'):
            HELPER.run_workflow(source, self.electrodes, self.directory / 'bad-result', geometry_note=GEOMETRY_NOTE)
        with self.assertRaisesRegex(ValueError, 'log-error'):
            HELPER.run_workflow(self.observations, self.electrodes, self.directory / 'bad-sigma',
                                geometry_note=GEOMETRY_NOTE, extra_log_sigma=0)

    def test_cli_exports_requested_response_products_and_reads_them_back(self):
        output = self.directory / 'cli-output'
        result = subprocess.run([sys.executable, str(SCRIPT), '--observations', str(self.observations),
             '--electrodes', str(self.electrodes), '--output', str(output), '--geometry-note', GEOMETRY_NOTE],
             capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        responses, report = HELPER.read_result(output)
        self.assertEqual(len(responses), 318)
        self.assertEqual(report['fit_status'], self.report['fit_status'])

    def test_modified_response_artifact_fails_checksum(self):
        output = self.directory / 'corrupt-export'
        shutil.copytree(self.output, output)
        with (output / 'responses.csv').open('a') as stream:
            stream.write('changed\n')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            HELPER.read_result(output)


if __name__ == '__main__':
    unittest.main()
