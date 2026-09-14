"""Execute the well-log workflow's documented examples on synthetic LAS data."""

import contextlib
import os
from pathlib import Path
import tempfile
import unittest

import lasio
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / 'workflows/well-log-evaluation/SKILL.md'


def stage_code(stage):
    section = SKILL.read_text(encoding='utf-8').split(f'### Stage {stage}:', 1)[1]
    return section.split('```python\n', 1)[1].split('```', 1)[0]


class WellLogExamplesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        previous = Path.cwd()
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, previous)
        self.depth = 1000.0 + np.arange(41) * 0.5

    def write_las(self, gr=None, rhob=None, rt=None, unit='M', rho_unit='G/C3'):
        las = lasio.LASFile()
        las.well.WELL = 'SYNTHETIC'
        las.append_curve('DEPTH', self.depth, unit=unit)
        for name, values, default, curve_unit in [
            ('GR', gr, 70.0, 'API'),
            ('RHOB', rhob, 2.32, rho_unit),
            ('RT', rt, 5.0, 'OHMM'),
        ]:
            las.append_curve(name, np.full(len(self.depth), default) if values is None else values,
                             unit=curve_unit)
        las.write('well_A.las', version=2.0)

    def run_stages(self, last=3):
        namespace = {}
        with open(os.devnull, 'w') as sink, contextlib.redirect_stdout(sink):
            for stage in range(1, last + 1):
                exec(compile(stage_code(stage), f'{SKILL}:stage{stage}', 'exec'), namespace)
        return namespace

    def test_qc_data_reaches_calculations_and_csv(self):
        gr = np.full(len(self.depth), 70.0)
        gr[20] = 200.0
        self.write_las(gr=gr)
        ns = self.run_stages()
        self.assertLess(ns['df'].loc[20, 'GR'], 150.0)
        self.assertLess(ns['df'].loc[20, 'VSH'], 1.0)
        # Independent analytic case: (2.65 - 2.32)/(2.65 - 1) = .2;
        # sqrt(.05 / (.2**2 * 5)) = .5.
        np.testing.assert_allclose(ns['phi_density'], 0.2)
        np.testing.assert_allclose(ns['Sw'], 0.5)
        result = pd.read_csv('well_A_evaluated.csv')
        np.testing.assert_allclose(result['DEPT'], self.depth)
        np.testing.assert_allclose(result['PHI_D'], 0.2)
        np.testing.assert_allclose(result['SW'], 0.5)
        self.assertTrue(result['QC_VALID'].all())

    def test_missing_and_invalid_resistivity_stay_missing(self):
        rt = np.full(len(self.depth), 5.0)
        rt[10:13] = [np.nan, 0.0, -1.0]
        self.write_las(rt=rt)
        with np.errstate(divide='raise', invalid='raise'):
            ns = self.run_stages(last=4)
        self.assertEqual(len(ns['df']), len(self.depth))
        self.assertTrue(ns['df'].loc[10:12, 'SW'].isna().all())
        self.assertFalse(ns['df'].loc[10:12, 'QC_VALID'].any())
        # Adjacent identical facies must not be merged across the missing span.
        self.assertEqual(len(ns['strip']), 2)
        self.assertLess(float(ns['strip'][0].base.z), float(ns['strip'][1].top.z))

    def test_stage_one_unit_conversion_reaches_qc_and_calculation(self):
        self.write_las(rhob=np.full(len(self.depth), 2320.0), rho_unit='KG/M3')
        ns = self.run_stages(last=1)
        ns['df']['RHOB'] /= 1000.0  # User's verified kg/m3 -> g/cm3 conversion.
        for stage in (2, 3):
            exec(compile(stage_code(stage), f'{SKILL}:stage{stage}', 'exec'), ns)
        np.testing.assert_allclose(ns['phi_density'], 0.2)
        np.testing.assert_allclose(ns['Sw'], 0.5)

    def test_zero_and_unphysical_porosity_do_not_create_infinities(self):
        rhob = np.full(len(self.depth), 2.32)
        rhob[0:3] = [2.65, 2.9, 0.5]
        self.write_las(rhob=rhob)
        with np.errstate(divide='raise', invalid='raise'):
            ns = self.run_stages()
        self.assertTrue(ns['df'].loc[0:2, 'SW'].isna().all())
        self.assertTrue(ns['df'].loc[1:2, 'PHI_D'].isna().all())

    def test_saturation_clipping_remains_auditable(self):
        self.write_las(rt=np.full(len(self.depth), 0.1))
        ns = self.run_stages()
        np.testing.assert_allclose(ns['Sw'], 1.0)
        self.assertTrue(ns['df']['SW_CLIPPED'].all())

    def test_non_metre_depth_requires_conversion(self):
        self.write_las(unit='FT')
        with self.assertRaisesRegex(ValueError, 'metres'):
            self.run_stages()

    def test_domain_curve_processing_uses_supported_api(self):
        from welly import Well
        skill = ROOT / 'welly/SKILL.md'
        section = skill.read_text(encoding='utf-8').split('### Process Curves', 1)[1]
        code = section.split('```python\n', 1)[1].split('```', 1)[0]
        values = np.linspace(20.0, 120.0, 41)
        values[20] = 1000.0
        well = Well.from_df(pd.DataFrame({'GR': values}, index=1500.0 + np.arange(41)))
        ns = {'w': well}
        exec(compile(code, str(skill), 'exec'), ns)
        self.assertLess(well.data['GR'].values.max(), 1000.0)
        self.assertAlmostEqual(np.nanmin(ns['gr_norm']), 0.0)
        self.assertAlmostEqual(np.nanmax(ns['gr_norm']), 1.0)
        self.assertAlmostEqual(ns['gr_resampled'].step, 0.5)
        self.assertEqual(ns['gr_window'].start, 1500.0)
        self.assertEqual(ns['gr_window'].stop, 1510.0)

    def test_survey_geometry_and_log_values_stay_aligned(self):
        self.write_las()
        survey = pd.DataFrame({
            'MD_M': [1000.0, 1010.0, 1020.0],
            'X_M': [400.0, 404.0, 410.0],
            'Y_M': [800.0, 801.0, 808.0],
            'TVDSS_M': [950.0, 957.0, 960.0],
        })
        survey.to_csv('trajectory.csv', index=False)
        ns = self.run_stages(last=5)
        path = ns['well_path']
        self.assertEqual(path.n_points, len(self.depth))
        np.testing.assert_allclose(path.points[[0, 20, 40]],
                                   [[400, 800, -950], [404, 801, -957], [410, 808, -960]])
        np.testing.assert_allclose(path['Porosity'], 0.2)
        # A saved product must retain the surveyed coordinates and point scalars.
        path.save('well.vtp')
        import pyvista as pv
        loaded = pv.read('well.vtp')
        np.testing.assert_allclose(loaded.points, path.points)
        np.testing.assert_allclose(loaded['GR'], 70.0)

    def test_survey_cannot_extrapolate_beyond_measured_range(self):
        self.write_las()
        pd.DataFrame({'MD_M': [1005, 1015], 'X_M': [0, 1],
                      'Y_M': [0, 1], 'TVDSS_M': [1000, 1009]}).to_csv('trajectory.csv', index=False)
        with self.assertRaisesRegex(ValueError, 'cover the log depth range'):
            self.run_stages(last=5)


if __name__ == '__main__':
    unittest.main()
