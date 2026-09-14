"""Execute the published seismic/rock-physics Markdown examples on small data."""

import contextlib
import os
from pathlib import Path
import re
import tempfile
import unittest

import lasio
import numpy as np
import pyvista as pv
import segyio


ROOT = Path(__file__).resolve().parents[2] / "workflows"


def stage_code(workflow, number):
    text = (ROOT / workflow / "SKILL.md").read_text(encoding="utf-8")
    section = re.search(rf"^### Stage {number}:.*?(?=^### |^## |\Z)",
                        text, flags=re.MULTILINE | re.DOTALL)
    if section is None:
        raise AssertionError(f"Missing Stage {number} in {workflow}")
    block = re.search(r"^```python\n(.*?)^```", section[0],
                      flags=re.MULTILINE | re.DOTALL)
    if block is None:
        raise AssertionError(f"Missing Python example in {workflow} Stage {number}")
    return compile(block[1], f"{workflow}/SKILL.md:Stage {number}", "exec")


@contextlib.contextmanager
def working_directory(path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class SeismicExampleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def write_las(self, dt, dts=None, sonic_unit="US/FT", depth_unit="M"):
        dt = np.asarray(dt, dtype=float)
        las = lasio.LASFile()
        las.append_curve("DEPT", 1000 + np.arange(len(dt)) * 0.5, unit=depth_unit)
        las.append_curve("DT", dt, unit=sonic_unit)
        if dts is not None:
            las.append_curve("DTS", np.asarray(dts, dtype=float), unit=sonic_unit)
        las.append_curve("RHOB", np.full(len(dt), 2.3), unit="G/CC")
        las.append_curve("PHIE", np.full(len(dt), 0.2), unit="V/V")
        las.append_curve("GR", np.full(len(dt), np.nan), unit="API")
        las.write(str(self.directory / "well.las"), fmt="%.8f")

    def run_rock(self, stages, namespace=None):
        namespace = {} if namespace is None else namespace
        with working_directory(self.directory):
            for stage in stages:
                exec(stage_code("rock-physics-avo", stage), namespace)
        return namespace

    def seismic_functions(self):
        namespace = {}
        for stage in (1, 2, 5):
            exec(stage_code("seismic-interpretation", stage), namespace)
        return namespace

    def write_segy(self, crossline_fast=False, scalar=-10, measurement=1, units=1):
        path = self.directory / "survey.sgy"
        n_samples = 256
        sample = np.arange(n_samples)
        signal = np.sin(2 * np.pi * 32 * sample / n_samples)
        signal += 0.5 * np.sin(2 * np.pi * 112 * sample / n_samples)
        cube = np.empty((2, 3, n_samples), dtype=np.float32)
        spec = segyio.spec()
        spec.ilines = [10, 20]
        spec.xlines = [30, 40, 50]
        spec.offsets = [1]
        spec.samples = 100 + sample * 4  # ms, including nonzero recording delay
        spec.format = 5
        spec.sorting = 1 if crossline_fast else 2
        order = ([(i, j) for j in range(3) for i in range(2)] if crossline_fast
                 else [(i, j) for i in range(2) for j in range(3)])
        factor = scalar if scalar > 0 else 1 / abs(scalar) if scalar < 0 else 1
        with segyio.create(str(path), spec) as handle:
            handle.bin[segyio.BinField.MeasurementSystem] = measurement
            handle.bin[segyio.BinField.Interval] = 4000
            for trace_number, (i, j) in enumerate(order):
                cube[i, j] = signal + 10 * i + j
                x, y = 500000 + 20 * i - 6 * j, 4500000 + 15 * i + 8 * j
                handle.header[trace_number] = {
                    segyio.TraceField.INLINE_3D: spec.ilines[i],
                    segyio.TraceField.CROSSLINE_3D: spec.xlines[j],
                    segyio.TraceField.offset: 1,
                    segyio.TraceField.CDP_X: round(x / factor),
                    segyio.TraceField.CDP_Y: round(y / factor),
                    segyio.TraceField.SourceGroupScalar: scalar,
                    segyio.TraceField.CoordinateUnits: units,
                    segyio.TraceField.TRACE_SAMPLE_INTERVAL: 4000,
                    segyio.TraceField.DelayRecordingTime: 100,
                }
                handle.trace[trace_number] = cube[i, j]
        return path, cube

    def test_sonic_units_and_missing_unrelated_curve_preserve_rows(self):
        self.write_las([60, 60, 60], [120, 120, 120], depth_unit="FT")
        data = self.run_rock([1])
        np.testing.assert_allclose(data["vp"], 5080)
        np.testing.assert_allclose(data["vs"], 2540)
        np.testing.assert_allclose(data["rho"], 2300)
        self.assertEqual(len(data["df"]), 3)  # All GR values are null.
        self.assertAlmostEqual(data["depth_m"][0], 304.8)
        self.assertFalse(data["vs_estimated"])
        self.write_las([200, 200, 200], [400, 400, 400], sonic_unit="US/M")
        metric = self.run_rock([1])
        np.testing.assert_allclose(metric["vp"], 5000)
        np.testing.assert_allclose(metric["vs"], 2500)
        self.write_las([60] * 3, [120] * 3)
        decoded = self.run_rock([1])
        for unit in ("µs/ft", "μs/ft"):
            with self.subTest(unit=unit):
                # Test correctly decoded metadata; file encoding is a separate I/O decision.
                decoded["las"].curves["DT"].unit = unit
                np.testing.assert_allclose(decoded["sonic_velocity"]("DT"), 5080)

    def test_missing_dts_uses_documented_estimate_before_access(self):
        self.write_las([101.6] * 3)
        data = self.run_rock([1])
        self.assertTrue(data["vs_estimated"])
        np.testing.assert_allclose(data["vp"], 3000)
        np.testing.assert_allclose(data["vs"], 1413.9)

    def test_invalid_sonic_values_and_unknown_units_are_rejected(self):
        for values, unit in (([60, 0, 60], "US/FT"),
                             ([60, np.nan, 60], "US/FT"),
                             ([60, 60, 60], "UNKNOWN")):
            with self.subTest(values=values, unit=unit):
                self.write_las(values, sonic_unit=unit)
                with self.assertRaises(ValueError):
                    self.run_rock([1])

    def test_rock_stages_execute_with_moduli_fluid_and_time_domain_handoffs(self):
        dt = np.r_[np.full(64, 101.6), np.full(65, 95.25)]
        self.write_las(dt, dt * 2)
        depth = 1000 + np.arange(len(dt)) * 0.5
        times = 1 + np.arange(len(dt)) * 0.004
        np.savetxt(self.directory / "time_depth.csv", np.c_[depth, times],
                   delimiter=",", header="depth_m,twt_s", comments="")
        data = self.run_rock(range(1, 6))
        self.assertTrue(np.all(data["K"] > 0))
        self.assertTrue(np.all(data["E"] > 0))
        np.testing.assert_allclose(data["rho_gas_sat"], data["rho"] - 190)
        np.testing.assert_allclose(data["rho_gas_sat"] * data["vs_gas"]**2,
                                   data["G"], rtol=1e-12)
        self.assertEqual(data["rc"].shape, (40, 128))
        normal_reflection = np.diff(data["AI"]) / (data["AI"][:-1] + data["AI"][1:])
        np.testing.assert_allclose(data["rc_exact"][0].real, normal_reflection,
                                   atol=1e-12)
        self.assertEqual(data["synthetic"].shape, data["twt_regular_s"].shape)
        self.assertEqual(len(data["synthetic"]), 257)  # Time resampling, not 129 depth samples.
        center = len(data["wavelet"]) // 2
        self.assertAlmostEqual(data["wavelet"][center], 1)
        self.assertAlmostEqual(data["wavelet_time"][center], 0)
        self.assertGreater(np.max(np.abs(data["synthetic"])), 0)

    def test_time_depth_extrapolation_is_rejected(self):
        self.write_las([101.6] * 3, [203.2] * 3)
        np.savetxt(self.directory / "time_depth.csv", [[1000.5, 1.0], [1001, 1.1]],
                   delimiter=",", header="depth_m,twt_s", comments="")
        with self.assertRaisesRegex(ValueError, 'must cover'):
            self.run_rock([1, 2, 5])

    def time_logs(self):
        return {"np": np, "vp": np.r_[np.full(64, 3000.), np.full(65, 3200.)],
                "vs": np.full(129, 1500.), "rho": np.full(129, 2300.),
                "porosity": np.full(129, 0.2), "twt_s": 1 + np.arange(129) * 0.002}

    def test_seismic_synthetic_is_a_scaled_ricker_at_the_interface(self):
        data = self.time_logs()
        exec(stage_code("seismic-interpretation", 3), data)
        self.assertEqual(np.argmax(data["synthetic"]), 64)
        self.assertAlmostEqual(data["synthetic"][64], 1 / 31, places=12)
        half = len(data["wavelet"]) // 2
        np.testing.assert_allclose(data["synthetic"][64-half:65+half], data["wavelet"] / 31,
                                   atol=1e-12)
        data = self.time_logs()
        data["twt_s"][10] += 0.0005
        with self.assertRaisesRegex(ValueError, 'uniform two-way time'):
            exec(stage_code("seismic-interpretation", 3), data)
        data = self.time_logs()
        data["vp"][0] *= -1
        with self.assertRaisesRegex(ValueError, 'physically valid'):
            exec(stage_code("seismic-interpretation", 3), data)

    def test_disba_example_has_near_surface_units_and_finite_dispersion(self):
        data = {"np": np}
        exec(stage_code("seismic-interpretation", 4), data)
        model = data["velocity_model"]
        np.testing.assert_allclose(model.thickness, [0.005, 0.01, 0.02, 0])
        velocities = data["phase_velocity_m_s"]
        self.assertTrue(np.all(np.isfinite(velocities)))
        self.assertEqual(len(velocities), len(data["dispersion"].period))
        # Short-period Rayleigh waves approach ~0.93 Vs in the top layer (Vs=150 m/s).
        self.assertGreater(velocities[0], 0.90 * 150)
        self.assertLess(velocities[0], 150)
        self.assertGreater(velocities[-1], velocities[0])
        self.assertLess(velocities[-1], 1200)

    def test_segy_geometry_and_trace_order_survive_grid_export(self):
        functions = self.seismic_functions()
        for crossline_fast in (False, True):
            with self.subTest(crossline_fast=crossline_fast):
                path, expected_cube = self.write_segy(crossline_fast=crossline_fast)
                survey = functions["load_poststack"](str(path), crs="EPSG:32632")
                np.testing.assert_array_equal(survey["amplitude"], expected_cube)
                grid = functions["make_seismic_grid"](survey)
                self.assertEqual(grid.dimensions, expected_cube.shape)
                for i, j, k in ((0, 0, 0), (1, 2, 255), (1, 1, 47)):
                    index = np.ravel_multi_index((i, j, k), expected_cube.shape, order="F")
                    np.testing.assert_allclose(grid.points[index],
                        [500000 + 20 * i - 6 * j, 4500000 + 15 * i + 8 * j, -(100 + 4 * k)])
                    self.assertEqual(grid.point_data["amplitude"][index], expected_cube[i, j, k])
                exported = self.directory / "seismic.vts"
                grid.save(exported)
                loaded = pv.read(exported)
                np.testing.assert_allclose(loaded.bounds, grid.bounds)
                self.assertEqual(loaded.field_data["crs"][0], "EPSG:32632")
                self.assertIn("ms", loaded.field_data["axis_units"][2])

    def test_segy_scalars_measurement_units_and_time_axis_validation(self):
        functions = self.seismic_functions()
        for scalar in (0, 1, 10, -10):
            with self.subTest(scalar=scalar):
                path, _ = self.write_segy(scalar=scalar, measurement=2)
                survey = functions["load_poststack"](str(path), crs="projected CRS in metres")
                self.assertAlmostEqual(survey["easting_m"][0, 0], 152400)
        path, _ = self.write_segy(units=3)
        with self.assertRaisesRegex(ValueError, 'length units'):
            functions["load_poststack"](str(path), crs="EPSG:32632")
        path, _ = self.write_segy()
        with segyio.open(str(path), 'r+') as handle:
            handle.header[1][segyio.TraceField.DelayRecordingTime] = 104
        with self.assertRaisesRegex(ValueError, 'time axes differ'):
            functions["load_poststack"](str(path), crs="EPSG:32632")

    def test_filter_processes_every_trace_and_preserves_raw_cube_and_geometry(self):
        functions = self.seismic_functions()
        path, raw = self.write_segy()
        survey = functions["load_poststack"](str(path), crs="EPSG:32632")
        processed = functions["filter_poststack"](survey)
        np.testing.assert_array_equal(survey["amplitude"], raw)
        np.testing.assert_array_equal(processed["easting_m"], survey["easting_m"])
        for i in range(2):
            for j in range(3):
                before = np.abs(np.fft.rfft(raw[i, j]))
                after = np.abs(np.fft.rfft(processed["amplitude"][i, j]))
                self.assertGreater(after[32], 0.5 * before[32])
                self.assertLess(after[112], 0.2 * before[112])
        grid = functions["make_seismic_grid"](processed)
        np.testing.assert_allclose(grid.point_data['amplitude'],
                                   processed['amplitude'].ravel(order='F'))
        with self.assertRaisesRegex(ValueError, 'Nyquist'):
            functions["filter_poststack"](survey, freqmax=200)


if __name__ == "__main__":
    unittest.main()
