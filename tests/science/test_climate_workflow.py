"""Real NOAA TMAX pipeline plus independent calendar, area and leakage checks."""

from collections import defaultdict
import csv
import gzip
from hashlib import sha256
import importlib.util
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

import cftime
import numpy as np
from scipy.integrate import quad
import xarray as xr


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/fixtures/workflows/climate"
SOURCE = FIXTURE / "ghcnd-tmax-2018-2020.csv.gz"
PROVENANCE = FIXTURE / "provenance.json"
SCRIPT = ROOT / "workflows/climate-analysis/scripts/station_pipeline.py"
spec = importlib.util.spec_from_file_location("climate_station_pipeline", SCRIPT)
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


class ObservedClimateWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="geoscience-climate-test-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.output = Path(cls.temporary.name) / "case"
        cls.product, cls.report, cls.folds = pipeline.run_case(SOURCE, PROVENANCE, cls.output)
        cls.table, cls.metadata = pipeline.read_verified_source(SOURCE, PROVENANCE)
        cls.daily = pipeline.prepare_daily(cls.table)
        cls.monthly = pipeline.monthly_summary(cls.daily)

    def test_complete_source_license_units_and_original_bytes(self):
        self.assertEqual(self.metadata["dataset"]["license"], "CC0-1.0")
        original = gzip.decompress(SOURCE.read_bytes())
        self.assertEqual(len(original), 1491604)
        self.assertEqual(sha256(original).hexdigest(),
                         "8f3c60133f21efb7936d72d2850fd0c90bbe4e8138e2f857ed8fba024ffef1d3")
        rows = list(csv.DictReader(StringIO(original.decode())))
        stations = self.daily.station.values.tolist()
        station_index = {name: i for i, name in enumerate(stations)}
        date_index = {value.strftime("%Y-%m-%d"): i for i, value in enumerate(self.daily.time.values)}
        for row in rows:
            actual = self.daily.raw_tmax.values[date_index[row["DATE"]], station_index[row["STATION"]]]
            self.assertAlmostEqual(actual - 273.15, float(row["TMAX"]), places=10)
        self.assertEqual(len(rows), 13152)
        self.assertEqual(self.daily.tmax.attrs["units"], "K")
        self.assertEqual(self.report["missing_station_days"], 0)
        self.assertEqual(self.report["quality_rejected_station_days"], 0)

    def test_monthly_means_and_calendar_duration_match_direct_daily_reader(self):
        raw = csv.DictReader(StringIO(gzip.decompress(SOURCE.read_bytes()).decode()))
        values = defaultdict(list)
        for row in raw:
            values[(row["DATE"][:7], row["STATION"])].append(float(row["TMAX"]) + 273.15)
        for time in self.monthly.time.values:
            for station in self.monthly.station.values:
                observed = values[(time.strftime("%Y-%m"), station)]
                selected = self.monthly.sel(time=time, station=station)
                self.assertAlmostEqual(float(selected.monthly_tmax), sum(observed) / len(observed), places=10)
                self.assertEqual(int(selected.valid_days), len(observed))
                self.assertEqual(float(selected.monthly_coverage), 1)
        self.assertEqual(int(self.monthly.expected_days.sel(time=cftime.DatetimeProlepticGregorian(2020, 2, 1))), 29)

    def test_reference_and_annual_anomaly_equal_independent_daily_aggregation(self):
        records = list(csv.DictReader(StringIO(gzip.decompress(SOURCE.read_bytes()).decode())))
        reference = defaultdict(list)
        for row in records:
            if row["DATE"][:4] in ("2018", "2019"):
                reference[int(row["DATE"][5:7])].append(float(row["TMAX"]) + 273.15)
        reference = {month: sum(values) / len(values) for month, values in reference.items()}
        np.testing.assert_allclose(self.product.reference_tmax, [reference[m] for m in range(1, 13)], atol=1e-10)
        anomalies = defaultdict(list)
        for row in records:
            if row["DATE"].startswith("2020"):
                anomalies[row["STATION"]].append(float(row["TMAX"]) + 273.15 - reference[int(row["DATE"][5:7])])
        for station, values in anomalies.items():
            self.assertEqual(len(values), 366)
            self.assertAlmostEqual(self.report["station_anomaly_K"][station], sum(values) / len(values), places=10)
        local_reference = defaultdict(list)
        for row in records:
            if row["DATE"][:4] in ("2018", "2019"):
                local_reference[(row["STATION"], int(row["DATE"][5:7]))].append(float(row["TMAX"]))
        local_reference = {key: sum(value) / len(value) for key, value in local_reference.items()}
        local_anomalies = defaultdict(list)
        for row in records:
            if row["DATE"].startswith("2020"):
                local_anomalies[row["STATION"]].append(float(row["TMAX"])
                    - local_reference[(row["STATION"], int(row["DATE"][5:7]))])
        for station, values in local_anomalies.items():
            self.assertAlmostEqual(self.report["station_local_reference_anomaly_K"][station],
                                   sum(values) / len(values), places=10)

    def test_future_observations_cannot_change_the_predeclared_reference(self):
        changed = self.monthly.copy(deep=True)
        changed["monthly_tmax"] = changed.monthly_tmax.where(changed.time.dt.year != 2020,
                                                            changed.monthly_tmax + 100)
        actual = pipeline.reference_climatology(changed, changed.station.values)
        np.testing.assert_array_equal(actual.values, self.product.reference_tmax.values)

    def test_spatial_holdout_never_fits_any_values_from_test_stations(self):
        longitude, latitude = self.daily.station_longitude.values, self.daily.station_latitude.values
        seen = np.zeros(len(longitude), dtype=int)
        for fold in self.folds:
            seen += fold["test"]
            changed = self.monthly.copy(deep=True)
            station_mask = xr.DataArray(fold["test"], dims="station", coords={"station": changed.station})
            changed["monthly_tmax"] = changed.monthly_tmax.where(~station_mask, changed.monthly_tmax + 80)
            poisoned = pipeline.spatial_fold(changed, longitude, latitude, fold["test"])
            for name in ["reference", "coefficients", "prediction"]:
                np.testing.assert_array_equal(poisoned[name], fold[name])
            self.assertEqual(poisoned["constant_prediction"], fold["constant_prediction"])
            np.testing.assert_allclose(poisoned["observed"] - fold["observed"], 80, atol=1e-10)
        np.testing.assert_array_equal(seen, 1)

    def test_actual_verde_predictions_match_independent_linear_least_squares(self):
        longitude, latitude = self.daily.station_longitude.values, self.daily.station_latitude.values
        x, y = pipeline.PROJECT.transform(longitude, latitude)
        matrix = np.column_stack([np.ones(len(x)), x, y])
        for fold in self.folds:
            reference = xr.DataArray(fold["reference"], dims="climate_month",
                                     coords={"climate_month": np.arange(1, 13)})
            values = pipeline.annual_anomaly(self.monthly, reference)[0].values
            coefficients, _, rank, _ = np.linalg.lstsq(matrix[fold["train"]], values[fold["train"]], rcond=None)
            self.assertEqual(rank, 3)
            np.testing.assert_allclose(matrix[fold["test"]] @ coefficients, fold["prediction"], rtol=0, atol=1e-9)
            self.assertAlmostEqual(fold["constant_prediction"], values[fold["train"]].mean())

    def test_qc_flags_missing_rows_and_incomplete_months_are_not_filled(self):
        altered = self.table.copy()
        station = altered.STATION.iloc[0]
        idx = altered.index[(altered.STATION == station) & altered.DATE.str.startswith("2018-01")]
        # Controlled faults applied only in memory; never change the field file.
        altered.loc[idx[0], "TMAX_ATTRIBUTES"] = ",X,W"
        altered["TMAX"] = altered.TMAX.astype(object)
        altered.loc[idx[1], "TMAX"] = ""
        altered.loc[idx[1], "TMAX_ATTRIBUTES"] = ""
        altered = altered.drop(index=idx[2:5])
        daily = pipeline.prepare_daily(altered)
        selected = daily.sel(station=station, time=slice("2018-01-01", "2018-01-31"))
        self.assertEqual(int((selected.qc_status == 2).sum()), 1)
        self.assertEqual(int((selected.qc_status == 1).sum()), 4)
        self.assertTrue(np.isfinite(float(selected.raw_tmax.isel(time=0))))
        self.assertTrue(np.isnan(float(selected.tmax.isel(time=0))))
        self.assertEqual(str(selected.source_attributes.isel(time=0).item()), ",X,W")
        month = pipeline.monthly_summary(daily).sel(station=station, time=cftime.DatetimeProlepticGregorian(2018, 1, 1))
        self.assertEqual(int(month.valid_days), 26)
        self.assertTrue(np.isnan(float(month.monthly_tmax)))
        self.assertAlmostEqual(float(month.monthly_coverage), 26 / 31)

    def test_duplicate_rows_and_wrong_query_units_fail(self):
        import pandas as pd
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            pipeline.prepare_daily(pd.concat([self.table, self.table.iloc[:1]]))
        path = Path(self.temporary.name) / "wrong-provenance.json"
        metadata = json.loads(PROVENANCE.read_text())
        metadata["query"]["units"] = "standard"
        path.write_text(json.dumps(metadata))
        with self.assertRaisesRegex(ValueError, "metric TMAX"):
            pipeline.read_verified_source(SOURCE, path)

    def test_original_hash_corruption_is_rejected(self):
        directory = Path(self.temporary.name) / "bad-source"
        directory.mkdir()
        copied = directory / SOURCE.name
        content = bytearray(SOURCE.read_bytes())
        content[100] ^= 1
        copied.write_bytes(content)
        with self.assertRaisesRegex(ValueError, "integrity"):
            pipeline.read_verified_source(copied, PROVENANCE)

    def test_export_retains_calendar_source_qc_crs_coverage_and_model_labels(self):
        path = self.output / "climate-workflow.nc"
        with xr.open_dataset(path, engine="scipy", decode_times=xr.coders.CFDatetimeCoder(use_cftime=True)) as actual:
            self.assertIsInstance(actual.time.values[0], cftime.DatetimeProlepticGregorian)
            self.assertEqual(actual.time.encoding["calendar"], "proleptic_gregorian")
            self.assertEqual(actual.observing_date.encoding["calendar"], "proleptic_gregorian")
            self.assertEqual(actual.attrs["reference_period"], "2018-01-01/2019-12-31")
            self.assertEqual(actual.attrs["source_csv_sha256"], self.report["source_csv_sha256"])
            self.assertIn("datum", actual.crs.attrs["comment"])
            self.assertIn("not observed", actual.model_anomaly.attrs["comment"])
            self.assertEqual(actual.qc_status.attrs["flag_meanings"], self.daily.qc_status.attrs["flag_meanings"])
            unsupported = actual.spatial_support.values == 0
            self.assertTrue(np.isnan(actual.model_anomaly.values[unsupported]).all())
            self.assertTrue(unsupported.any())
            np.testing.assert_array_equal(actual.monthly_coverage, 1)
            xr.testing.assert_allclose(actual, self.product)
        self.assertEqual(self.report["output_sha256"], sha256(path.read_bytes()).hexdigest())
        with self.assertRaisesRegex(ValueError, "empty output"):
            pipeline.run_case(SOURCE, PROVENANCE, self.output)


class CalendarAndAreaBenchmarks(unittest.TestCase):
    def test_non_gregorian_duration_weights_and_calendar_export(self):
        for calendar, lengths in [("360_day", [30, 30, 30]), ("noleap", [31, 28, 31])]:
            time = xr.date_range("2001-01-01", periods=3, freq="MS", calendar=calendar, use_cftime=True)
            values = xr.DataArray([0., 0., 30.], dims="time", coords={"time": time}, attrs={"units": "K"})
            days = values.time.dt.days_in_month
            np.testing.assert_array_equal(days, lengths)
            actual, coverage = pipeline.duration_weighted(values, days, days)
            self.assertAlmostEqual(float(actual), 30 * lengths[2] / sum(lengths))
            self.assertEqual(float(coverage), 1)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "calendar.nc"
                values.to_dataset(name="synthetic").to_netcdf(path, engine="scipy")
                with xr.open_dataset(path, engine="scipy", decode_times=xr.coders.CFDatetimeCoder(use_cftime=True)) as reopened:
                    self.assertEqual(reopened.time.encoding["calendar"], calendar)
                    xr.testing.assert_equal(reopened.synthetic, values)

    def test_duration_coverage_and_all_missing_never_become_zero(self):
        values = xr.DataArray([2., np.nan, 8.], dims="time")
        days = xr.DataArray([30., 30., 30.], dims="time")
        mean, coverage = pipeline.duration_weighted(values, days, days)
        self.assertTrue(np.isnan(float(mean)))
        self.assertAlmostEqual(float(coverage), 2 / 3)
        accepted, _ = pipeline.duration_weighted(values, days, days, min_coverage=0.6)
        self.assertEqual(float(accepted), 5)
        empty, support = pipeline.duration_weighted(values * np.nan, days, days, min_coverage=0)
        self.assertTrue(np.isnan(float(empty)))
        self.assertEqual(float(support), 0)
        with self.assertRaises(ValueError):
            pipeline.duration_weighted(values, days * 2, days)

    def test_spherical_cell_areas_against_quadrature_and_global_surface(self):
        lat = np.array([[-90., 0.], [0., 30.], [30., 90.]])
        lon = np.array([[-180., 0.], [0., 180.]])
        actual = pipeline.spherical_cell_areas(lat, lon)
        reference = np.array([[quad(np.cos, np.deg2rad(south), np.deg2rad(north))[0]
                               * np.deg2rad(east - west) * pipeline.EARTH_RADIUS_M ** 2
                               for west, east in lon] for south, north in lat])
        np.testing.assert_allclose(actual, reference, rtol=1e-14)
        self.assertAlmostEqual(actual.sum() / (4 * np.pi * pipeline.EARTH_RADIUS_M ** 2), 1)
        with self.assertRaises(ValueError):
            pipeline.spherical_cell_areas([[30, -30]], lon)

    def test_area_missingness_uses_fixed_support_and_valid_area(self):
        data = xr.DataArray([[2., 8.], [99., np.nan]], dims=("lat", "lon"))
        area = xr.DataArray([[1., 3.], [100., 2.]], dims=("lat", "lon"))
        support = xr.DataArray([[True, True], [False, True]], dims=("lat", "lon"))
        rejected, coverage = pipeline.area_weighted(data, area, support)
        self.assertTrue(np.isnan(float(rejected)))
        self.assertAlmostEqual(float(coverage), 4 / 6)
        accepted, _ = pipeline.area_weighted(data, area, support, min_coverage=0.6)
        self.assertEqual(float(accepted), (2 * 1 + 8 * 3) / 4)
        empty, coverage = pipeline.area_weighted(data * np.nan, area, support, min_coverage=0)
        self.assertTrue(np.isnan(float(empty)))
        self.assertEqual(float(coverage), 0)
        with self.assertRaisesRegex(ValueError, "no area"):
            pipeline.area_weighted(data, area, support & False)


if __name__ == "__main__":
    unittest.main()
