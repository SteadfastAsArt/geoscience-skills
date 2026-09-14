"""Small, real LAS and SEG-Y round-trip regressions (no mocked scientific I/O)."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

try:
    import lasio
    import numpy as np
    import pandas  # noqa: F401 -- required by the LAS merge script
    import segyio
    if not hasattr(lasio, "LASFile") or not hasattr(segyio, "create"):
        raise ImportError("Repository directories are not installed Python libraries")
except ImportError as error:
    raise ImportError("Install numpy, pandas, lasio, and segyio: " + str(error)) from error


ROOT = Path(__file__).resolve().parents[2]


def load_script(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


subset = load_script("segy_subset_regression", "segyio/scripts/extract_subset.py")
merge = load_script("las_merge_regression", "lasio/scripts/merge_curves.py")


class FileFixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="geoscience-io-test-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)

    def las(self, name, depth, curves, *, depth_name="DEPT", unit="m"):
        path = self.directory / name
        data = lasio.LASFile()
        data.well["WELL"].value = "Synthetic regression well"
        data.append_curve(depth_name, np.asarray(depth, dtype=float), unit=unit)
        for mnemonic, values in curves.items():
            data.append_curve(mnemonic, np.asarray(values, dtype=float), unit="test")
        data.write(str(path))
        return str(path)

    def segy(self, name="source.sgy", *, records=None, start=0, interval=2,
             scalar=0, sorting=2, iline_byte=189, xline_byte=193, extra_text=False):
        records = records or [(10, 100, 0), (10, 200, 0)]
        path = self.directory / name
        spec = segyio.spec()
        spec.format = 5
        spec.sorting = sorting
        spec.samples = start + np.arange(5) * interval
        spec.tracecount = len(records)
        spec.ext_headers = int(extra_text)
        scale = 1 / abs(scalar) if scalar < 0 else scalar or 1
        with segyio.create(str(path), spec) as data:
            if extra_text:
                data.text[1] = b"C01 SYNTHETIC EXTENDED HEADER".ljust(3200, b" ")
            for index, (inline, xline, offset) in enumerate(records):
                data.trace[index] = np.arange(5, dtype=np.float32) + 10 * index
                data.header[index] = {
                    segyio.TraceField.CDP: 9000 + index,
                    iline_byte: inline,
                    xline_byte: xline,
                    segyio.TraceField.offset: offset,
                    segyio.TraceField.TRACE_SAMPLE_COUNT: 5,
                    segyio.TraceField.TRACE_SAMPLE_INTERVAL: int(interval * 1000),
                    segyio.TraceField.DelayRecordingTime: int(start / scale),
                    segyio.TraceField.ScalarTraceHeader: scalar,
                }
        return str(path)


class SegySubsetTests(FileFixture):
    def test_time_crop_preserves_absolute_time_and_extended_header(self):
        source = self.segy(start=100, extra_text=True)
        output = str(self.directory / "cropped.sgy")
        self.assertEqual(subset.extract_by_traces(source, output, (0, 2), (104, 108)), 2)
        with segyio.open(output, ignore_geometry=True) as data:
            np.testing.assert_allclose(data.samples, [104, 106, 108])
            np.testing.assert_allclose(data.trace[0], [2, 3, 4])
            np.testing.assert_allclose(data.trace[1], [12, 13, 14])
            self.assertEqual(data.bin[segyio.BinField.Samples], 3)
            self.assertEqual(data.ext_headers, 1)
            for index in range(2):
                self.assertEqual(data.header[index][segyio.TraceField.DelayRecordingTime], 104)
                self.assertEqual(data.header[index][segyio.TraceField.TRACE_SAMPLE_COUNT], 3)
            with segyio.open(source, ignore_geometry=True) as original:
                self.assertEqual(data.text[1], original.text[1])

    def test_geometry_preserves_sort_order_offsets_and_time(self):
        for sorting in (1, 2):
            with self.subTest(sorting=sorting):
                if sorting == 2:
                    records = [(i, x, o) for i in (10, 20) for x in (100, 200) for o in (50, 150)]
                else:
                    records = [(i, x, o) for x in (100, 200) for i in (10, 20) for o in (50, 150)]
                source = self.segy(f"source-{sorting}.sgy", records=records, sorting=sorting)
                output = str(self.directory / f"geometry-{sorting}.sgy")
                count = subset.extract_by_geometry(source, output, (10, 21), (100, 101), (4, 8))
                selected = [index for index, (_, x, _) in enumerate(records) if x == 100]
                self.assertEqual(count, 4)
                with segyio.open(output) as data:
                    np.testing.assert_allclose(data.samples, [4, 6, 8])
                    np.testing.assert_array_equal(data.ilines, [10, 20])
                    np.testing.assert_array_equal(data.xlines, [100])
                    np.testing.assert_array_equal(data.offsets, [50, 150])
                    for output_index, input_index in enumerate(selected):
                        np.testing.assert_allclose(data.trace[output_index], np.arange(2, 5) + 10 * input_index)
                        self.assertEqual(data.header[output_index][segyio.TraceField.CDP], 9000 + input_index)
                        self.assertEqual(data.header[output_index][segyio.TraceField.offset], records[input_index][2])

    def test_custom_geometry_fields_are_preserved(self):
        source = self.segy(records=[(0, 1, 0), (0, 2, 0), (1, 1, 0)], iline_byte=9, xline_byte=21)
        output = str(self.directory / "custom.sgy")
        self.assertEqual(subset.extract_by_geometry(source, output, (0, 1), (2, 3), iline_byte=9, xline_byte=21), 1)
        with segyio.open(output, ignore_geometry=True) as data:
            np.testing.assert_allclose(data.trace[0], np.arange(5) + 10)
            self.assertEqual(data.header[0][9], 0)
            self.assertEqual(data.header[0][21], 2)
            self.assertEqual(data.header[0][segyio.TraceField.INLINE_3D], 0)
            self.assertEqual(data.header[0][segyio.TraceField.CROSSLINE_3D], 0)

    def test_existing_time_scalar_encodes_fractional_crop(self):
        source = self.segy(start=1.5, interval=0.5, scalar=-1000)
        output = str(self.directory / "fractional.sgy")
        subset.extract_by_traces(source, output, (0, 1), (2, 3))
        with segyio.open(output, ignore_geometry=True) as data:
            np.testing.assert_allclose(data.samples, [2, 2.5, 3])
            np.testing.assert_allclose(data.trace[0], [1, 2, 3])
            self.assertEqual(data.header[0][segyio.TraceField.DelayRecordingTime], 2000)
            self.assertEqual(data.header[0][segyio.TraceField.ScalarTraceHeader], -1000)

    def test_unrepresentable_time_crop_fails_before_creating_output(self):
        source = self.segy(interval=0.5)
        output = str(self.directory / "unrepresentable.sgy")
        with self.assertRaisesRegex(ValueError, "cannot be represented"):
            subset.extract_by_traces(source, output, (0, 1), (0.5, 1.5))
        self.assertFalse(Path(output).exists())

    def test_heterogeneous_trace_times_are_not_silently_mislabelled(self):
        source = self.segy()
        with segyio.open(source, "r+", ignore_geometry=True) as data:
            data.header[1][segyio.TraceField.DelayRecordingTime] = 2
        output = str(self.directory / "different-starts.sgy")
        with self.assertRaisesRegex(ValueError, "common trace start"):
            subset.extract_by_traces(source, output, (0, 2), (4, 8))
        self.assertFalse(Path(output).exists())

    def test_empty_negative_and_reversed_ranges_leave_no_output(self):
        source = self.segy()
        cases = [((0, 0), None), ((-1, 2), None), ((20, 30), None),
                 ((0, 1), (20, 30)), ((0, 1), (8, 4))]
        for index, (traces, times) in enumerate(cases):
            with self.subTest(traces=traces, times=times):
                output = str(self.directory / f"invalid-{index}.sgy")
                with self.assertRaises(ValueError):
                    subset.extract_by_traces(source, output, traces, times)
                self.assertFalse(Path(output).exists())

    def test_open_time_bounds_and_time_only_cli(self):
        source = self.segy()
        output = str(self.directory / "time-only.sgy")
        result = subprocess.run(
            [sys.executable, str(ROOT / "segyio/scripts/extract_subset.py"), source, output, "--time", "4:"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        with segyio.open(output, ignore_geometry=True) as data:
            self.assertEqual(data.tracecount, 2)
            np.testing.assert_allclose(data.samples, [4, 6, 8])

    def test_in_place_extraction_does_not_truncate_input(self):
        source = self.segy()
        before = Path(source).read_bytes()
        for extract in (
            lambda: subset.extract_by_traces(source, source, (0, 1)),
            lambda: subset.extract_by_geometry(source, source, (10, 11)),
        ):
            with self.assertRaisesRegex(ValueError, "different files"):
                extract()
            self.assertEqual(Path(source).read_bytes(), before)

    def test_hard_link_output_cannot_overwrite_source(self):
        source = self.segy()
        alias = self.directory / "alias.sgy"
        try:
            alias.hardlink_to(source)
        except OSError as error:
            self.skipTest(f"Hard links are unavailable: {error}")
        before = Path(source).read_bytes()
        with self.assertRaisesRegex(ValueError, "different files"):
            subset.extract_by_traces(source, str(alias), (0, 1))
        self.assertEqual(Path(source).read_bytes(), before)


class LasMergeTests(FileFixture):
    def test_resampling_uses_each_curves_original_grid_and_keeps_endpoint(self):
        first = self.las("first.las", [0, 2, 4], {"GR": [0, 20, 40]})
        second = self.las("second.las", [1, 3, 5], {"RHOB": [1, 3, 5]})
        output = str(self.directory / "merged.las")
        merge.merge_las_files([first, second], output, resample_step=0.5)
        data = lasio.read(output)
        np.testing.assert_allclose(data.index, np.arange(0, 5.1, 0.5))
        np.testing.assert_allclose(data["GR"], [0, 5, 10, 15, 20, 25, 30, 35, 40, np.nan, np.nan], equal_nan=True)
        np.testing.assert_allclose(data["RHOB"], [np.nan, np.nan, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5], equal_nan=True)
        self.assertEqual(data.well["STEP"].value, 0.5)
        self.assertEqual(data.well["STOP"].value, 5)
        self.assertEqual(data.curves[0].unit, "m")

    def test_original_missing_samples_remain_gaps(self):
        first = self.las("gaps.las", [0, 2, 4, 6], {"GR": [0, np.nan, 40, 60]})
        second = self.las("other.las", [1, 3, 5], {"RHOB": [1, 3, 5]})
        output = str(self.directory / "gaps-merged.las")
        merge.merge_las_files([first, second], output, resample_step=1)
        data = lasio.read(output)
        np.testing.assert_allclose(data["GR"], [0, np.nan, np.nan, np.nan, 40, 50, 60], equal_nan=True)
        np.testing.assert_allclose(data["RHOB"], [np.nan, 1, 2, 3, 4, 5, np.nan], equal_nan=True)

    def test_descending_depth_and_different_index_names(self):
        first = self.las("descending.las", [4, 2, 0], {"GR": [40, 20, 0]})
        second = self.las("depth.las", [1, 3, 5], {"RHOB": [1, 3, 5]}, depth_name="DEPTH")
        output = str(self.directory / "normalised.las")
        merge.merge_las_files([first, second], output, resample_step=1)
        data = lasio.read(output)
        self.assertEqual(data.curves[0].mnemonic, "DEPT")
        self.assertNotIn("DEPTH", data.keys())
        np.testing.assert_allclose(data["GR"], [0, 10, 20, 30, 40, np.nan], equal_nan=True)

    def test_unaligned_grid_does_not_extrapolate_past_last_depth(self):
        first = self.las("first.las", [0, 1], {"GR": [0, 10]})
        output = str(self.directory / "unaligned.las")
        merge.merge_las_files([first], output, resample_step=0.3)
        data = lasio.read(output)
        np.testing.assert_allclose(data.index, [0, 0.3, 0.6, 0.9])
        np.testing.assert_allclose(data["GR"], [0, 3, 6, 9])

    def test_outer_union_updates_actual_step_without_resampling(self):
        first = self.las("first.las", [0, 2, 4], {"GR": [0, 20, 40]})
        second = self.las("second.las", [1, 3, 5], {"RHOB": [1, 3, 5]})
        output = str(self.directory / "union.las")
        merge.merge_las_files([first, second], output)
        data = lasio.read(output)
        np.testing.assert_allclose(data.index, np.arange(6))
        self.assertEqual(data.well["STEP"].value, 1)
        self.assertTrue(np.isnan(data["GR"][1]))

    def test_invalid_sampling_depths_and_units_leave_no_output(self):
        first = self.las("first.las", [0, 2, 4], {"GR": [0, 20, 40]})
        for step in (0, -0.5, np.nan, np.inf):
            with self.subTest(step=step):
                output = str(self.directory / "bad-step.las")
                with self.assertRaisesRegex(ValueError, "finite and positive"):
                    merge.merge_las_files([first], output, resample_step=step)
                self.assertFalse(Path(output).exists())
        duplicate = self.las("duplicate.las", [0, 0, 2], {"GR": [0, 10, 20]})
        missing_depth = self.las("missing-depth.las", [0, np.nan, 2], {"GR": [0, 10, 20]})
        feet = self.las("feet.las", [0, 2, 4], {"RHOB": [1, 2, 3]}, unit="ft")
        for files, message in (([duplicate], "duplicate"), ([missing_depth], "finite"), ([first, feet], "depth units")):
            with self.subTest(message=message):
                output = str(self.directory / f"invalid-{message.replace(' ', '-')}.las")
                with self.assertRaisesRegex(ValueError, message):
                    merge.merge_las_files(files, output, resample_step=1)
                self.assertFalse(Path(output).exists())

    def test_in_place_merge_preserves_source(self):
        source = self.las("first.las", [0, 2, 4], {"GR": [0, 20, 40]})
        before = Path(source).read_bytes()
        with self.assertRaisesRegex(ValueError, "overwrite an input"):
            merge.merge_las_files([source], source, resample_step=1)
        self.assertEqual(Path(source).read_bytes(), before)

    def test_hard_link_output_cannot_overwrite_source(self):
        source = self.las("first.las", [0, 2, 4], {"GR": [0, 20, 40]})
        alias = self.directory / "alias.las"
        try:
            alias.hardlink_to(source)
        except OSError as error:
            self.skipTest(f"Hard links are unavailable: {error}")
        before = Path(source).read_bytes()
        with self.assertRaisesRegex(ValueError, "overwrite an input"):
            merge.merge_las_files([source], str(alias), resample_step=1)
        self.assertEqual(Path(source).read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
