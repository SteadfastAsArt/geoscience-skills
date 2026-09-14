"""Execute the actual marked Markdown examples with the real scientific stack.

Install requirements-models.txt in a separate Python 3.11 environment, then run:
    python -m unittest discover -s tests/science -p test_model_examples.py -v

No missing-dependency skips or mocked scientific libraries are used. These small
synthetic problems check calculations and geometry, not field-survey reliability.
"""

from contextlib import contextmanager
import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
GEOLOGY = ROOT / "workflows/geological-modelling/SKILL.md"
INVERSION = ROOT / "workflows/geophysical-inversion/SKILL.md"


def example(path, name):
    blocks = re.findall(r"```python\n(.*?)\n```", path.read_text(encoding="utf-8"), re.S)
    matches = [block for block in blocks if block.startswith(f"# example: {name}\n")]
    if len(matches) != 1:
        raise AssertionError(f"Expected one Markdown example {name!r} in {path}")
    return compile(matches[0], f"{path}::{name}", "exec")


@contextmanager
def working_directory(path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class ModelExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="geoscience-model-examples-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.workspace = Path(cls.temporary.name)
        for folder in (".cache", ".config", "matplotlib", "gempy", "simpeg", "pygimli"):
            (cls.workspace / folder).mkdir()
        cls.environment = patch.dict(os.environ, {
            "MPLBACKEND": "Agg",
            "MPLCONFIGDIR": str(cls.workspace / "matplotlib"),
            "XDG_CONFIG_HOME": str(cls.workspace / ".config"),
            "XDG_CACHE_HOME": str(cls.workspace / ".cache"),
        })
        cls.environment.start()
        cls.addClassCleanup(cls.environment.stop)
        import pyvista as pv
        cls.pv = pv

        # Each branch gets a fresh namespace: it cannot inherit the other
        # framework's mesh, recovered model, imports, or conductivity variable.
        cls.geology = cls.run_examples(
            "gempy", GEOLOGY, ["gempy-model", "gempy-export"]
        )
        cls.simpeg = cls.run_examples(
            "simpeg", INVERSION,
            ["simpeg-inversion", "simpeg-result", "inversion-gridding", "inversion-export"],
        )
        cls.pygimli = cls.run_examples(
            "pygimli", INVERSION,
            ["pygimli-synthetic", "pygimli-inversion", "pygimli-result",
             "inversion-gridding", "inversion-export"],
        )

    @classmethod
    def run_examples(cls, folder, path, names):
        namespace = {}
        with working_directory(cls.workspace / folder):
            for name in names:
                exec(example(path, name), namespace)
        return namespace

    def test_gempy_recovers_two_sides_of_synthetic_inclined_contact(self):
        namespace = self.geology
        centers = namespace["geo_model"].grid.regular_grid.values
        lithology = namespace["sol"].raw_arrays.lith_block
        contact_elevation = -227.5 - 0.125 * (centers[:, 0] - 1000.0)
        # This analytical plane is independent of GemPy's interpolation engine.
        # Ignore a 1 m band at the contact itself, where categorical boundaries
        # are sensitive to numerical tolerance and grid sampling.
        above = centers[:, 2] > contact_elevation + 1.0
        below = centers[:, 2] < contact_elevation - 1.0
        self.assertTrue(np.any(above) and np.any(below))
        np.testing.assert_array_equal(lithology[above], 1)
        np.testing.assert_array_equal(lithology[below], 2)

    def test_gempy_export_preserves_bounds_cell_centres_and_axis_order(self):
        namespace = self.geology
        grid = namespace["grid"]
        regular = namespace["geo_model"].grid.regular_grid
        self.assertEqual(grid.n_cells, int(np.prod(regular.resolution)))
        self.assertIn("lithology", grid.cell_data)
        self.assertNotIn("lithology", grid.point_data)
        np.testing.assert_allclose(grid.bounds, [1000, 1200, 2000, 2120, -300, -180])
        np.testing.assert_allclose(grid.spacing, [25, 20, 24])
        # Ask VTK to locate GemPy's world-coordinate sample positions. This
        # verifies the conversion without repeating its reshape/flatten logic.
        vtk_ids = grid.find_containing_cell(regular.values)
        self.assertTrue(np.all(vtk_ids >= 0))
        self.assertEqual(len(np.unique(vtk_ids)), grid.n_cells)
        np.testing.assert_allclose(grid.cell_centers().points[vtk_ids], regular.values)
        np.testing.assert_array_equal(
            grid.cell_data["lithology"][vtk_ids], namespace["sol"].raw_arrays.lith_block,
        )

    def test_gempy_vti_round_trip_keeps_categorical_cell_data(self):
        original = self.geology["grid"]
        loaded = self.pv.read(self.workspace / "gempy/geological_model.vti")
        np.testing.assert_allclose(loaded.bounds, original.bounds)
        np.testing.assert_allclose(loaded.cell_centers().points, original.cell_centers().points)
        np.testing.assert_array_equal(loaded.cell_data["lithology"], original.cell_data["lithology"])

    def test_simpeg_forward_and_inversion_reduce_weighted_data_misfit(self):
        namespace = self.simpeg
        self.assertTrue(np.all(np.isfinite(namespace["clean_data"])))
        self.assertTrue(np.all(namespace["standard_deviation"] > 0))
        self.assertLess(namespace["dmis"](namespace["mrec"]), namespace["dmis"](namespace["m0"]))
        rho = namespace["resistivity_ohm_m"]
        self.assertTrue(np.all(np.isfinite(rho) & (rho > 0)))
        np.testing.assert_allclose(rho * namespace["sigma_rec"], 1.0)

    def test_simpeg_adapter_preserves_nonuniform_cells_and_vertical_coordinates(self):
        from discretize import TensorMesh
        mesh = TensorMesh([np.array([1., 3., 2.]), np.array([2., 4.])], origin=[100., -20.])
        conductivity = np.array([0.1, 0.2, 0.4, 0.5, 1.0, 2.0])
        namespace = {"mesh": mesh, "sigma_rec": conductivity}
        exec(example(INVERSION, "simpeg-result"), namespace)
        vtk = namespace["model_vtk"]
        np.testing.assert_allclose(vtk.bounds, [100, 106, 0, 0, -20, -14])
        np.testing.assert_allclose(vtk.cell_centers().points[:, [0, 2]], mesh.cell_centers)
        np.testing.assert_allclose(vtk.compute_cell_sizes().cell_data["Area"], mesh.cell_volumes)
        np.testing.assert_allclose(vtk.cell_data["resistivity_ohm_m"], [10, 5, 2.5, 2, 1, 0.5])

    def test_pygimli_runs_independently_on_its_parameter_domain(self):
        namespace = self.pygimli
        self.assertNotIn("sigma_rec", namespace)
        self.assertNotIn("mesh", namespace)
        rho = namespace["resistivity_ohm_m"]
        manager = namespace["mgr"]
        self.assertEqual(rho.size, manager.paraDomain.cellCount())
        self.assertLess(manager.paraDomain.cellCount(), manager.fop.mesh().cellCount())
        self.assertTrue(np.all(np.isfinite(rho) & (rho > 0)))
        self.assertTrue(np.isfinite(manager.inv.chi2()))
        # A coarse homogeneous-earth experiment should remain near its 100
        # ohm-m input; this is not a claim about resolving heterogeneous earth.
        self.assertLess(abs(np.median(rho) - 100.0), 20.0)
        vtk = namespace["model_vtk"]
        self.assertEqual(vtk.n_cells, rho.size)
        np.testing.assert_allclose(vtk.cell_centers().points[:, [0, 2]], namespace["cell_centers_xz_m"], atol=1e-4)
        np.testing.assert_allclose(vtk.cell_centers().points[:, 1], 0.0)
        np.testing.assert_allclose(vtk.cell_data["resistivity_ohm_m"], rho, rtol=1e-5)

    def test_shared_gridding_has_finite_log_resistivity_for_both_branches(self):
        for name, namespace in (("simpeg", self.simpeg), ("pygimli", self.pygimli)):
            with self.subTest(branch=name):
                raster = namespace["raster"]
                self.assertEqual(raster.log10_resistivity.dims, ("elevation_m", "distance_m"))
                self.assertTrue(np.all(np.isfinite(raster.log10_resistivity.values)))
                for axis, coordinate in ((0, "distance_m"), (1, "elevation_m")):
                    np.testing.assert_allclose(
                        [raster[coordinate].min(), raster[coordinate].max()],
                        [namespace["cell_centers_xz_m"][:, axis].min(),
                         namespace["cell_centers_xz_m"][:, axis].max()],
                    )

    def test_shared_vtu_export_preserves_each_branch_geometry_and_values(self):
        for name, namespace in (("simpeg", self.simpeg), ("pygimli", self.pygimli)):
            with self.subTest(branch=name):
                loaded = self.pv.read(self.workspace / name / "recovered_resistivity.vtu")
                original = namespace["model_vtk"]
                self.assertEqual(loaded.n_cells, original.n_cells)
                np.testing.assert_allclose(loaded.bounds, original.bounds)
                np.testing.assert_allclose(loaded.cell_centers().points, original.cell_centers().points)
                np.testing.assert_array_equal(loaded.cell_data["resistivity_ohm_m"], original.cell_data["resistivity_ohm_m"])


if __name__ == "__main__":
    unittest.main()
