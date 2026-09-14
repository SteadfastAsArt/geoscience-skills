"""Real FDI/PLI interpolation, Markdown execution, and VTK scientific readback."""
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

from LoopStructural import GeologicalModel
import numpy as np
import pyvista as pv

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('loop_builder', ROOT / 'loopstructural/scripts/build_model.py')
HELPER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(HELPER)


def example(heading, namespace=None):
    text = (ROOT / 'loopstructural/SKILL.md').read_text()
    section = re.search(rf'^## {re.escape(heading)}\n(.*?)(?=^## |\Z)', text, re.M | re.S)
    block = re.search(r'^```python\n(.*?)^```', section[1], re.M | re.S)
    namespace = {} if namespace is None else namespace
    exec(compile(block[1], f'loopstructural/SKILL.md:{heading}', 'exec'), namespace)
    return namespace


def plane(points):
    return points[:, 2] - 3030 + .1 * (points[:, 0] - 1050) - .05 * (points[:, 1] - 2100)


class LoopExamples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = example('A constrained planar model')
        example('Evaluate a VTK grid', cls.ns)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def test_markdown_world_coordinate_values_match_independent_plane(self):
        np.testing.assert_allclose(self.ns['values'], [-10, 10, 0], atol=.002)
        model = self.ns['model']
        actual = model.evaluate_feature_value('strat', self.ns['data'][['X', 'Y', 'Z']].to_numpy())
        np.testing.assert_allclose(actual, self.ns['data']['val'], atol=.005)

    def test_markdown_grid_point_order_and_surface_geometry(self):
        grid = self.ns['grid']
        self.assertEqual(grid.dimensions, (9, 7, 5))
        np.testing.assert_allclose(grid.points[:3], [[1000, 2000, 3000], [1012.5, 2000, 3000], [1025, 2000, 3000]])
        np.testing.assert_allclose(grid['strat'], plane(grid.points), atol=.05)
        surface = self.ns['surface']
        self.assertGreater(surface.n_cells, 0)
        np.testing.assert_allclose(plane(surface.points), 0, atol=.05)

    def test_helper_fdi_vtk_and_surface_readback_preserve_scalars_and_bounds(self):
        model = HELPER.build_model(self.ns['data'], origin=self.ns['origin'], maximum=self.ns['maximum'])
        path = HELPER.export_grid(model, self.directory / 'grid', nsteps=[9, 7, 5])
        grid = pv.read(path)
        self.assertEqual(grid.n_points, 315)
        np.testing.assert_allclose(grid.bounds, [1000, 1100, 2000, 2200, 3000, 3060])
        np.testing.assert_allclose(grid['strat'], plane(grid.points), atol=.05)
        paths = HELPER.export_surfaces(model, self.directory / 'surface', 'strat', [0], [9, 7, 5])
        self.assertEqual(len(paths), 1)
        surface = pv.read(paths[0])
        self.assertGreater(surface.n_cells, 0)
        np.testing.assert_allclose(plane(surface.points), 0, atol=.05)
        with self.assertRaisesRegex(ValueError, 'No surface'):
            HELPER.export_surfaces(model, self.directory / 'empty', 'strat', [1e6], [9, 7, 5])
        self.assertFalse(list(self.directory.glob('empty*.vtk')))

    def test_helper_pli_recovers_planar_values(self):
        model = HELPER.build_model(self.ns['data'], interpolator='PLI', nelements=1000,
                                   origin=self.ns['origin'], maximum=self.ns['maximum'])
        np.testing.assert_allclose(model.evaluate_feature_value('strat', self.ns['query']), [-10, 10, 0], atol=.02)

    def test_invalid_constraints_extent_and_grid_are_rejected(self):
        bad = self.ns['data'].copy()
        bad.loc[0, 'X'] = np.nan
        with self.assertRaisesRegex(ValueError, 'finite'):
            HELPER.build_model(bad)
        bad = self.ns['data'].copy()
        bad.loc[0, ['gx', 'gy', 'gz']] = 0
        with self.assertRaisesRegex(ValueError, 'nonzero'):
            HELPER.build_model(bad)
        bad = self.ns['data'].copy()
        bad['Z'] = 3000
        with self.assertRaisesRegex(ValueError, 'zero-span'):
            HELPER.build_model(bad)
        with self.assertRaisesRegex(ValueError, 'Grid shape'):
            HELPER.evaluated_grid(self.ns['model'], [1, 4, 4])

    def test_cli_writes_model_values_and_fails_empty_surface(self):
        source = self.directory / 'constraints.csv'
        self.ns['data'].to_csv(source, index=False)
        command = [sys.executable, str(ROOT / 'loopstructural/scripts/build_model.py'), str(source),
                   '--output', str(self.directory / 'cli'), '--origin', '1000', '2000', '3000',
                   '--maximum', '1100', '2200', '3060', '--nsteps', '9', '7', '5']
        result = subprocess.run(command + ['--grid'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        grid = pv.read(self.directory / 'cli.vtk')
        np.testing.assert_allclose(grid['strat'], plane(grid.points), atol=.05)
        result = subprocess.run(command + ['--isovalue', '1000000'], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('No surface', result.stderr)


if __name__ == '__main__':
    unittest.main()
