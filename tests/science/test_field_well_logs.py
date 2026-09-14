"""Actual FDB-1 borehole observations through the real lasio path (core stack)."""

import csv
from io import StringIO
from pathlib import Path
import tempfile
import unittest

import lasio
import numpy as np

from field_case_support import verify_case
from field_well_log_support import (
    CURVES, DEPTH, REMARK, SONIC, depth_referenced_rows, export_observed_las,
    interval_diagnostic, load_well_table, well_report,
)


class FieldWellLogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="geoscience-field-well-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.output = Path(cls.temporary.name) / "FDB-1.converted.las"
        cls.selected = export_observed_las(cls.output)
        cls.las = lasio.read(cls.output)
        cls.table, cls.metadata = load_well_table()
        cls.report = interval_diagnostic(cls.table)

    def test_dataset_license_hash_and_observed_borehole_identity(self):
        directory, metadata = verify_case("well_logs")
        self.assertEqual(metadata["dataset"]["license"], "CC-BY-4.0")
        self.assertEqual(metadata["files"]["FDB-1_wireline_original.tab"]["sha256"],
                         "1834fbb42939f03c54ec3869d02ef3bbcca84f7c142f7ff182436809366e89d7")
        self.assertEqual(self.las.well.WELL.value, "FDB-1")
        self.assertIn("CC BY 4.0", self.las.other)
        self.assertIn("source does not name CRS", self.las.well.LOC.value)

    def test_las_values_and_nulls_match_independent_original_table_reader(self):
        directory, _ = verify_case("well_logs")
        body = (directory / "FDB-1_wireline_original.tab").read_text().split("*/\n", 1)[1]
        raw = list(csv.DictReader(StringIO(body), delimiter="\t"))
        indexes = [i for i, row in enumerate(raw) if row[DEPTH]]
        self.assertEqual(len(raw), 3646)
        self.assertEqual(len(indexes), 3508)
        np.testing.assert_array_equal(self.las["SRC_ROW"], np.array(indexes) + 1)
        np.testing.assert_allclose(self.las.index, [float(raw[i][DEPTH]) for i in indexes], atol=1e-9)
        for name, (column, unit) in CURVES.items():
            expected = np.array([float(raw[i][column]) if raw[i][column] else np.nan for i in indexes])
            np.testing.assert_allclose(self.las[name], expected, rtol=0, atol=1e-8, equal_nan=True)
            self.assertEqual(self.las.curves[name].unit, unit)
        self.assertEqual(self.las.well.NULL.value, -999.25)
        self.assertEqual(self.report["rows_without_depth"], 138)

    def test_sonic_units_and_inverse_slowness_obey_exact_foot_definition(self):
        source = np.array([float(v) * 1000 if v else np.nan for v in self.selected[SONIC]])
        np.testing.assert_allclose(self.las["VP"], source, rtol=0, atol=1e-8, equal_nan=True)
        self.assertEqual(self.las.curves["VP"].unit, "M/S")
        self.assertEqual(self.las.curves["DT"].unit, "US/FT")
        finite = np.isfinite(source)
        # One foot divided by the seconds needed to cross that foot is m/s.
        recovered = 0.3048 / (self.las["DT"][finite] * 1e-6)
        np.testing.assert_allclose(recovered, source[finite], rtol=0, atol=5e-7)
        np.testing.assert_array_equal(np.isnan(self.las["DT"]), np.isnan(source))

    def test_original_remarks_and_depth_gaps_are_retained(self):
        expected = np.array([bool(value) for value in self.selected[REMARK]])
        np.testing.assert_array_equal(self.las["SONIC_REMARK"], expected.astype(int))
        self.assertGreater(expected.sum(), 0)
        self.assertTrue(np.any(np.diff(self.las.index) > 0.1 + 1e-9))
        self.assertEqual(self.las.well.STEP.value, 0)
        self.assertTrue((np.diff(self.las.index) > 0).all())

    def test_time_integral_is_bounded_and_never_spans_missing_or_remarked_intervals(self):
        report = self.report
        pairs = np.flatnonzero(report["adjacent"])
        self.assertTrue(report["qualified"][pairs].all())
        self.assertTrue(report["qualified"][pairs + 1].all())
        np.testing.assert_allclose(np.diff(report["depth"])[pairs], 0.1, atol=1e-9)
        speed = report["velocity"][report["qualified"]]
        self.assertGreater(report["covered_one_way_time_s"], report["covered_depth_m"] / speed.max())
        self.assertLess(report["covered_one_way_time_s"], report["covered_depth_m"] / speed.min())
        low, high = report["quantization_only_time_bounds_s"]
        self.assertLess(low, report["covered_one_way_time_s"])
        self.assertGreater(high, report["covered_one_way_time_s"])
        self.assertIsNone(report["measurement_uncertainty"])
        self.assertLess(report["covered_depth_m"], self.las.index[-1] - self.las.index[0])

    def test_fixed_holdout_excludes_targets_and_preserves_interpolation_bounds(self):
        report = self.report
        indexes = report["holdout"]
        self.assertGreater(len(indexes), 100)
        self.assertFalse(report["training"][indexes].any())
        self.assertTrue(report["training"][indexes - 1].all())
        self.assertTrue(report["training"][indexes + 1].all())
        neighbours = np.stack((report["velocity"][indexes - 1], report["velocity"][indexes + 1]))
        self.assertTrue(np.all(report["prediction"] >= neighbours.min(axis=0) - 1e-9))
        self.assertTrue(np.all(report["prediction"] <= neighbours.max(axis=0) + 1e-9))
        self.assertGreater(well_report()["holdout_rmse_m_s"], 0)

    def test_ambiguous_depths_fail_instead_of_getting_sorted_or_guessed(self):
        bad = self.table.copy()
        bad.loc[1, DEPTH] = bad.loc[0, DEPTH]
        with self.assertRaisesRegex(ValueError, "unique"):
            depth_referenced_rows(bad)


if __name__ == "__main__":
    unittest.main()
