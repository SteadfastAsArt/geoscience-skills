"""Verify hand-built fixtures with real libraries in the isolated core stack."""

from pathlib import Path
import sys
import tempfile
import unittest

import lasio
import numpy as np
import segyio

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evals.cases import make_fixture


class FixtureReadbackTests(unittest.TestCase):
    def test_las_readback(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            oracle = make_fixture("las-qc", directory)["expected"]
            las = lasio.read(directory / "well.las")
            self.assertEqual(las.data.shape, (oracle["row_count"], 3))
            self.assertEqual(las.curves[0].unit, oracle["depth"]["unit"])
            self.assertEqual(len(las.index) - len(np.unique(las.index)), 1)
            for name, expected in oracle["curves"].items():
                self.assertEqual(las.curves[name].unit, expected["unit"])
                self.assertEqual(int(np.isnan(las[name]).sum()), expected["null_count"])
                self.assertAlmostEqual(float(np.nanmean(las[name])), expected["mean"])

    def test_segy_readback(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            expected = make_fixture("segy-subset", directory)["expected"]
            with segyio.open(str(directory / "survey.sgy"), ignore_geometry=True) as source:
                self.assertEqual(source.tracecount, 9)
                self.assertEqual(int(source.bin[segyio.BinField.Interval]), 2000)
                self.assertEqual(int(source.bin[segyio.BinField.Samples]), 12)
                indices = [i for i in range(source.tracecount)
                           if 310 <= source.header[i][segyio.TraceField.INLINE_3D] <= 315]
                self.assertEqual(len(indices), len(expected["traces"]))
                for i, trace in zip(indices, expected["traces"]):
                    np.testing.assert_array_equal(source.trace[i], trace["samples"])
                    for name, value in trace["headers"].items():
                        self.assertEqual(source.header[i][getattr(segyio.TraceField, name)], value)


if __name__ == "__main__":
    unittest.main()
