"""Execute new domain examples with real libraries and independent answers.

Requires the collection environment and MODFLOW_EXE. Missing dependencies or the
MODFLOW executable are errors. RockHound's network/cache boundary is replaced by
a real Pooch registry containing explicitly synthetic bytes; its CSV parser runs.
"""

import hashlib
import importlib
import importlib.util
import os
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pooch
import segyio


ROOT = Path(__file__).resolve().parents[2]


def example(skill, namespace=None):
    text = (ROOT / skill / "SKILL.md").read_text(encoding="utf-8")
    block = re.search(r"^```python\n(.*?)^```", text, re.M | re.S)
    if block is None:
        raise AssertionError(f"Missing executable example in {skill}")
    namespace = {} if namespace is None else namespace
    exec(compile(block[1], f"{skill}/SKILL.md", "exec"), namespace)
    return namespace


class MeshAndGeodesyTests(unittest.TestCase):
    def test_nonuniform_mesh_divergence_and_integral(self):
        ns = example("discretize")
        np.testing.assert_allclose(ns["divergence_s_inv"], -1, atol=1e-14)
        self.assertAlmostEqual(ns["integrated_divergence_m2_s"], -36)
        # Boundary integral from four physical rectangle sides, not the operator.
        boundary_flux = 12 * 6 - 18 * 6
        self.assertAlmostEqual(ns["integrated_divergence_m2_s"], boundary_flux)

    def test_nonuniform_cell_order_and_measure(self):
        mesh = example("discretize")["mesh"]
        np.testing.assert_array_equal(mesh.cell_volumes, [2, 4, 6, 4, 8, 12])
        np.testing.assert_allclose(mesh.cell_centers,
                                   [[.5, 1], [2, 1], [4.5, 1], [.5, 4], [2, 4], [4.5, 4]])

    def test_normal_gravity_units_and_reference_limits(self):
        ns = example("boule")
        np.testing.assert_allclose(ns["gravity_si"], ns["gravity_mgal"] * 1e-5)
        np.testing.assert_allclose(ns["gravity_si"][[0, 2]],
                                   [9.7803253359, 9.8321849378], atol=1e-9, rtol=0)
        self.assertTrue(np.all(np.diff(ns["gravity_si"]) > 0))

    def test_coordinate_roundtrip_and_geocentric_latitude(self):
        ns = example("boule")
        for expected, actual in zip(ns["geodetic"], ns["roundtrip"]):
            np.testing.assert_allclose(actual, expected, atol=2e-8)
        # tan(geocentric latitude) = (b/a)^2 tan(geodetic latitude), at h=0.
        flattening = 1 / 298.257223563
        expected = np.rad2deg(np.arctan((1 - flattening) ** 2))
        self.assertAlmostEqual(ns["spherical"][1][1], expected, places=10)


class PaleoclimateTests(unittest.TestCase):
    def test_irregular_sinusoid_recovers_declared_period(self):
        ns = example("pyleoclim")
        self.assertAlmostEqual(ns["peak_period_year"], 20, delta=.1)
        self.assertGreater(np.count_nonzero(ns["valid_spectrum"]), 990)
        self.assertGreater(np.min(ns["spectrum"].amplitude[ns["valid_spectrum"]]), 0)
        np.testing.assert_allclose(ns["spectrum"].frequency, ns["frequency_per_year"])

    def test_spectral_input_preserves_chronology_and_proxy(self):
        ns = example("pyleoclim")
        np.testing.assert_array_equal(ns["series"].time, ns["time_year"])
        np.testing.assert_array_equal(ns["series"].value, ns["proxy"])
        self.assertGreater(np.ptp(np.diff(ns["series"].time)), .1)


class LabelledSeismicTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "synthetic.sgy"
        spec = segyio.spec()
        spec.format, spec.sorting = 5, 2
        spec.ilines, spec.xlines = [10, 20], [100, 200]
        spec.samples = np.arange(6) * 2 + 100
        with segyio.create(str(self.path), spec) as handle:
            handle.bin[segyio.BinField.Interval] = 2000
            for index, (iline, xline) in enumerate([(10, 100), (10, 200), (20, 100), (20, 200)]):
                handle.header[index] = {
                    segyio.TraceField.INLINE_3D: iline,
                    segyio.TraceField.CROSSLINE_3D: xline,
                    segyio.TraceField.DelayRecordingTime: 100,
                    segyio.TraceField.TRACE_SAMPLE_INTERVAL: 2000,
                }
                handle.trace[index] = np.arange(6, dtype=np.float32) + 10 * index

    def test_labels_and_absolute_sample_time(self):
        ns = example("segysak", {"seismic_path": self.path})
        np.testing.assert_array_equal(ns["inline_labels"], [10, 20])
        np.testing.assert_array_equal(ns["crossline_labels"], [100, 200])
        np.testing.assert_array_equal(ns["sample_coordinate"], [100, 102, 104, 106, 108, 110])

    def test_labelled_samples_equal_original_traces(self):
        ns = example("segysak", {"seismic_path": self.path})
        with segyio.open(str(self.path), ignore_geometry=True) as handle:
            for index, (iline, xline) in enumerate([(10, 100), (10, 200), (20, 100), (20, 200)]):
                np.testing.assert_array_equal(
                    ns["amplitudes"].sel(iline=iline, xline=xline).values,
                    handle.trace[index])


class DatasetLoaderTests(unittest.TestCase):
    def test_ensaio_reads_hash_verified_published_cache(self):
        source = ROOT / "tests/fixtures/field/alps_gps/alps-gps-velocity.csv.xz"
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "v1"
            cache.mkdir()
            shutil.copyfile(source, cache / source.name)
            with patch.dict(os.environ, {"ENSAIO_DATA_DIR": tmp}):
                ns = example("ensaio")
            self.assertEqual(ns["source_sha256"],
                             "77f2907c2a019366e5f85de5aafcab2d0e90cc2c378171468a7705cab9938584")
            self.assertEqual(len(ns["gps"]), 186)
            self.assertEqual(ns["source_path"].parent, cache)

    def test_ensaio_rejects_unpublished_version(self):
        import ensaio
        with self.assertRaises(ValueError):
            ensaio.fetch_alps_gps(version=999)

    def test_legacy_rockhound_parser_preserves_boundaries_and_fluid_shear(self):
        # Project-owned synthetic rows; deliberately not a redistributed PREM model.
        rows = np.array([[6371, 0, 2.7, 6, 6, 3.5, 3.5, 1, 600, 1000],
                         [6000, 371, 3, 8, 8, 4, 4, 1, 600, 1000],
                         [6000, 371, 10, 9, 9, 0, 0, 1, 0, 1000]], dtype=float)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "PREM_1s.csv"
            np.savetxt(path, rows, delimiter=",")
            registry = pooch.create(path=tmp, base_url="https://invalid.example/",
                                    registry={path.name: hashlib.sha256(path.read_bytes()).hexdigest()})
            module = importlib.import_module("rockhound.prem")
            with patch.object(module, "REGISTRY", registry):
                ns = example("rockhound")
            np.testing.assert_allclose(ns["prem"].to_numpy(), rows)
            np.testing.assert_allclose(ns["radius_km"] + ns["depth_km"], 6371)
            self.assertEqual(ns["radius_km"][1], ns["radius_km"][2])
            self.assertEqual(ns["vsv_km_s"][-1], 0)


class GroundwaterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("confined_flow", ROOT / "flopy/scripts/confined_flow.py")
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_actual_modflow_head_gradient_and_water_balance(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.module.run(tmp, os.environ.get("MODFLOW_EXE", "mf6"))
            np.testing.assert_allclose(result["head_m"], np.linspace(10, 9, 11), atol=1e-7)
            np.testing.assert_allclose(sorted(result["boundary_flow_m3_day"]), [-2, 2], atol=1e-6)
            self.assertLess(abs(result["budget_net_m3_day"]), 1e-8)
            self.assertTrue(np.all(np.array(result["head_m"]) > result["aquifer_top_m"]))
            self.assertEqual(result["aquifer_top_m"] - result["aquifer_bottom_m"], 20)
            self.assertTrue((Path(tmp) / "confined.cbc").stat().st_size > 0)

    def test_missing_executable_fails_instead_of_skipping(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                self.module.run(tmp, str(Path(tmp) / "missing-mf6"))


if __name__ == "__main__":
    unittest.main()
