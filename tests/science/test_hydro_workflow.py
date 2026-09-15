"""Public-data Pastas workflow: actual Markdown/CLI, calibration isolation and readback."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd
import pastas as ps

from hydro_case_support import ROOT, FIXTURE, WORKFLOW, PIPELINE, HELPER, example, inputs


class HydroWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        cls.output = Path(cls.directory.name) / 'case'
        runner = example('workflows/hydrogeological-analysis/references/field_case.md',
                         'Run from a project checkout')['run_local_case']
        cls.result = runner(WORKFLOW, FIXTURE, cls.output)
        cls.head, cls.rain, cls.evap, cls.design = inputs()
        cls.prepared = PIPELINE.prepare_inputs(cls.head, cls.rain, cls.evap, cls.design)

    def test_field_provenance_hashes_units_and_real_date_gaps(self):
        provenance = json.loads((FIXTURE / 'provenance.json').read_text())
        self.assertEqual(provenance['well']['site_id'], '412918071321001')
        self.assertTrue(provenance['license'].startswith('GPL-3.0'))
        for name, metadata in provenance['files'].items():
            self.assertEqual(hashlib.sha256((FIXTURE / name).read_bytes()).hexdigest(), metadata['sha256'])
        self.assertEqual(len(self.head), 5737)
        self.assertEqual(len(self.rain), 6206)
        self.assertEqual(len(self.evap), 6224)
        qc = self.result['head_qc']
        self.assertAlmostEqual(qc.loc['2003-01-01', 'head_m'], -3.273552)
        self.assertEqual(int((~qc.observed).sum()), 101)
        self.assertTrue(np.isnan(qc.loc['2003-02-06', 'head_m']))
        self.assertIsNone(qc.index.tz)

    def test_fixed_partition_and_no_holdout_heads_stored_in_model(self):
        model = self.result['model']
        self.assertEqual(str(model.oseries.series.index.min().date()), '2005-01-01')
        self.assertEqual(str(model.oseries.series.index.max().date()), '2013-12-31')
        self.assertEqual(len(model.oseries.series), 3232)
        self.assertEqual(self.result['report']['holdout']['simulated_m']['n'], 1811)
        self.assertLess(self.result['report']['response_tmax_days'], self.design['warmup_days'])
        self.assertTrue(self.result['report']['solver_success'])

    def test_explicit_missing_rain_imputation_uses_calibration_only(self):
        qc = self.result['stress_qc']
        dates = qc.index[qc.precipitation_imputed]
        self.assertEqual(dates.strftime('%Y-%m-%d').tolist(), ['2008-11-11', '2014-07-26', '2014-07-27'])
        raw_train = self.rain.loc['2005-01-01':'2013-12-31'] * 304.8
        july_mean = raw_train[raw_train.index.month == 7].mean()
        self.assertAlmostEqual(qc.loc['2014-07-26', 'precipitation_used_mm_day'], july_mean)
        self.assertGreater(july_mean, 0)
        self.assertTrue(np.isnan(qc.loc['2014-07-26', 'precipitation_observed_mm_day']))
        self.assertFalse(qc.evaporation_imputed.any())

    def test_holdout_scores_recomputed_independently_and_beat_fixed_baselines(self):
        table = self.result['simulation']
        actual = self.head.loc['2014-01-01':'2018-12-25'] * .3048
        predicted = table.simulated_m.reindex(actual.index)
        expected = float(np.sqrt(np.mean((actual.to_numpy() - predicted.to_numpy()) ** 2)))
        score = self.result['report']['holdout']
        self.assertAlmostEqual(expected, score['simulated_m']['rmse_m'], places=12)
        self.assertLess(expected, .15)
        for name in ('calibration_mean_m', 'calibration_monthly_mean_m', 'last_calibration_head_fixed_m'):
            self.assertLess(expected, score[name]['rmse_m'])
            self.assertEqual(score[name]['n'], len(actual))
        self.assertAlmostEqual(score['calibration_monthly_mean_m']['rmse_m'], .2692305096, places=8)

    def test_residual_and_innovation_diagnostics_report_remaining_dependence(self):
        diagnostics = self.result['diagnostics'].set_index(['series', 'lag_days'])
        residual = diagnostics.loc[('calibration_residual', 1.)]
        innovation = diagnostics.loc[('calibration_noise', 1.)]
        self.assertGreater(residual['acf'], .9)
        self.assertLess(innovation['acf'], residual['acf'])
        self.assertGreater(innovation['acf'], innovation['conf'])
        self.assertGreater(innovation['n'], 1000)
        self.assertIn('retain autocorrelation', self.result['report']['uncertainty_limit'])

    def test_model_and_csv_roundtrip_with_contribution_closure(self):
        restored = ps.io.load(self.output / 'model.pas')
        simulation = restored.simulate(tmin='2005-01-01', tmax='2018-12-25')
        table = pd.read_csv(self.output / 'simulation.csv', index_col=0, parse_dates=True)
        np.testing.assert_allclose(table.simulated_m, simulation, atol=1e-8, rtol=0)
        self.assertTrue(np.isnan(table.loc['2005-02-04', 'head_m']))
        contribution = pd.read_csv(self.output / 'recharge_contribution.csv', index_col=0, parse_dates=True).squeeze('columns')
        constant = restored.parameters.loc['constant_d', 'optimal']
        np.testing.assert_allclose(contribution + constant, simulation, atol=1e-8, rtol=0)
        report = json.loads((self.output / 'report.json').read_text())
        self.assertLess(report['save_load_max_difference_m'], 1e-8)
        self.assertEqual(report['software']['pastas'], '2.0.0')
        self.assertEqual(restored.oseries.series.index.max(), pd.Timestamp('2013-12-31'))

    def test_repeat_fit_and_heldout_head_perturbation_do_not_change_parameters(self):
        altered_head = self.head.copy()
        altered_head.loc['2014-01-01':] += 100.
        repeated = PIPELINE.evaluate_case(altered_head, self.rain, self.evap, self.design)
        np.testing.assert_allclose(repeated['model'].parameters.optimal,
                                   self.result['model'].parameters.optimal, atol=1e-9, rtol=1e-9)
        np.testing.assert_allclose(repeated['simulation'].simulated_m,
                                   self.result['simulation'].simulated_m, atol=1e-10, rtol=0)
        self.assertGreater(repeated['report']['holdout']['simulated_m']['rmse_m'], 30.)

    def test_future_stress_perturbation_changes_hindcast_but_not_fit_or_imputation(self):
        altered_rain = self.rain.copy()
        altered_rain.loc['2014-01-01':] += 1. / 304.8  # +1 mm/day at observed future dates
        changed = PIPELINE.evaluate_case(self.head, altered_rain, self.evap, self.design)
        np.testing.assert_allclose(changed['model'].parameters.optimal,
                                   self.result['model'].parameters.optimal, atol=1e-9, rtol=1e-9)
        np.testing.assert_allclose(changed['simulation'].loc[:'2013-12-31', 'simulated_m'],
                                   self.result['simulation'].loc[:'2013-12-31', 'simulated_m'], atol=1e-10, rtol=0)
        delta = changed['simulation'].loc['2016':, 'simulated_m'] - self.result['simulation'].loc['2016':, 'simulated_m']
        self.assertGreater(delta.mean(), .2)
        self.assertEqual(changed['report']['imputation'], self.result['report']['imputation'])

    def test_missing_coverage_negative_stress_and_overlap_fail(self):
        with self.assertRaisesRegex(ValueError, 'warmup'):
            PIPELINE.prepare_inputs(self.head, self.rain.loc['2005':], self.evap, self.design)
        invalid = self.rain.copy()
        invalid.iloc[0] = -1
        with self.assertRaisesRegex(ValueError, 'negative'):
            PIPELINE.prepare_inputs(self.head, invalid, self.evap, self.design)
        design = copy.deepcopy(self.design)
        design['holdout_start'] = design['calibration_end']
        with self.assertRaisesRegex(ValueError, 'disjoint'):
            PIPELINE.prepare_inputs(self.head, self.rain, self.evap, design)
        invalid = self.rain.copy()
        invalid.loc['2007'] = np.nan
        with self.assertRaisesRegex(ValueError, 'too many missing'):
            PIPELINE.prepare_inputs(self.head, invalid, self.evap, self.design)

    def test_csv_duplicate_timezone_and_multicolumn_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.csv'
            for content in ['date,head\n2005-01-01,1\n2005-01-01,2\n',
                            'date,head\n2005-01-01T00:00:00Z,1\n2005-01-02T00:00:00Z,2\n',
                            'date,a,b\n2005-01-01,1,2\n']:
                path.write_text(content)
                with self.subTest(content=content), self.assertRaises(ValueError):
                    PIPELINE.read_series(path)

    def test_domain_markdown_calibration_and_real_pumping_response_sign(self):
        train, _, _, stresses, _, _ = self.prepared
        fit = example('pastas/SKILL.md', 'Calibrate a checked recharge model')['fit_recharge']
        model = fit(train.copy(), stresses['precipitation'].loc[:'2013-12-31'].copy(),
                    stresses['evaporation'].loc[:'2013-12-31'].copy(), '2005-01-01', '2013-12-31', 730)
        self.assertLess(model.stats.rmse(), .15)
        pumping = pd.Series(0., index=stresses['precipitation'].index, name='abstraction')
        pumping.loc['2010-01-01':'2011-12-31'] = 100.
        signed = HELPER.create_model(train, stresses['precipitation'], stresses['evaporation'], pumping,
                                      calibration_start='2005-01-01', calibration_end='2013-12-31', warmup_days=730)
        contribution = signed.get_contribution('pumping')
        self.assertLess(contribution.loc['2010':'2011'].min(), 0)
        self.assertLessEqual(contribution.max(), 1e-10)

    def test_workflow_cli_readback_and_existing_output_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'cli'
            command = [sys.executable, str(WORKFLOW / 'scripts/run_pastas_workflow.py'),
                       '--data-dir', str(FIXTURE), '--output-dir', str(output)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((output / 'report.json').read_text())
            self.assertAlmostEqual(report['holdout']['simulated_m']['rmse_m'],
                                   self.result['report']['holdout']['simulated_m']['rmse_m'], places=10)
            before = (output / 'report.json').read_bytes()
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('not overwritten', result.stderr)
            self.assertEqual((output / 'report.json').read_bytes(), before)

    def test_domain_helper_cli_persistence_and_optional_plot(self):
        train, _, _, stresses, _, _ = self.prepared
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            for name, series in [('head', train), ('precip', stresses['precipitation']), ('evap', stresses['evaporation'])]:
                series.to_csv(directory / f'{name}.csv', float_format='%.17g')
            command = [sys.executable, str(ROOT / 'pastas/scripts/groundwater_model.py'),
                       str(directory / 'head.csv'), str(directory / 'precip.csv'), str(directory / 'evap.csv'),
                       '--calibration-start', '2005-01-01', '--calibration-end', '2013-12-31',
                       '--noise', '--output', str(directory / 'fitted.pas'), '--plot', str(directory / 'diagnostics.png')]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            model = ps.io.load(directory / 'fitted.pas')
            self.assertLess(model.stats.rmse(), .15)
            self.assertTrue((directory / 'diagnostics.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
            self.assertEqual(model.oseries.series.index.max(), pd.Timestamp('2013-12-31'))


if __name__ == '__main__':
    unittest.main()
