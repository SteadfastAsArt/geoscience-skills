"""Exercise actual GMT rendering and coordinate-aware grid sampling offline."""

from pathlib import Path
import re
import tempfile
import unittest

import numpy as np
import pygmt
import xarray as xr

ROOT = Path(__file__).resolve().parents[2]


class PyGMTTests(unittest.TestCase):
    def test_documented_map_exports_a_pdf_with_real_gmt(self):
        text = (ROOT / "pygmt/SKILL.md").read_text(encoding="utf-8")
        block = re.search(r"^```python\n(.*?)^```", text, re.M | re.S)[1]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic-map.pdf"
            exec(compile(block, "pygmt/SKILL.md", "exec"), {"output_pdf": str(path)})
            self.assertTrue(path.read_bytes().startswith(b"%PDF-"))
            self.assertGreater(path.stat().st_size, 1000)

    def test_real_gmt_samples_grid_nodes_in_correct_axis_order(self):
        longitude = np.arange(5., 11.)
        latitude = np.arange(44., 49.)
        xx, yy = np.meshgrid(longitude, latitude)
        grid = xr.DataArray(2 * xx - 3 * yy, coords={"lat": latitude, "lon": longitude},
                            dims=("lat", "lon"), name="synthetic_m")
        points = np.array([[6, 45], [9, 47], [5, 44]], dtype=float)
        sampled = pygmt.grdtrack(points=points, grid=grid, newcolname="value")
        np.testing.assert_allclose(sampled.iloc[:, 2], [-123, -123, -122], atol=1e-6)


if __name__ == "__main__":
    unittest.main()
