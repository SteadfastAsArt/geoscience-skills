"""Run Bruges/disba entrypoints and bundled examples against real libraries."""

import contextlib
import importlib.util
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import warnings

import bruges
from disba import GroupDispersion, PhaseDispersion
import numpy as np


ROOT = Path(__file__).resolve().parents[2]


def example(path, heading, namespace=None):
    """Execute the actual first Python block under the requested heading."""
    text = (ROOT / path).read_text(encoding="utf-8")
    section = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text,
                        flags=re.MULTILINE | re.DOTALL)
    if section is None:
        raise AssertionError(f"Missing section {heading!r} in {path}")
    block = re.search(r"^```python\n(.*?)^```", section[1],
                      flags=re.MULTILINE | re.DOTALL)
    if block is None:
        raise AssertionError(f"Missing Python example {heading!r} in {path}")
    namespace = {} if namespace is None else namespace
    exec(compile(block[1], f"{path}:{heading}", "exec"), namespace)
    return namespace


class BrugesDomainTests(unittest.TestCase):
    def test_avo_normal_incidence_and_gradient_api(self):
        ns = example("bruges/SKILL.md", "AVO at one interface")
        # Independent impedance contrast: (7.52 - 6.9) / (7.52 + 6.9).
        self.assertAlmostEqual(float(np.real(ns["r_exact"][0])), 31.0 / 721.0, places=10)
        for key in ("r_exact", "r_shuey", "r_aki"):
            self.assertEqual(ns[key].shape, (31,))
            self.assertTrue(np.all(np.isfinite(ns[key])))
        self.assertAlmostEqual(float(ns["intercept"]), ns["r_shuey"][0])
        self.assertLess(ns["gradient"], 0)
        self.assertLess(np.max(np.abs(ns["r_exact"] - ns["r_aki"])), 0.001)

    def test_synthetic_reproduces_scaled_wavelet_at_declared_interface(self):
        ns = example("bruges/SKILL.md", "Wavelet and time-domain synthetic")
        np.testing.assert_array_equal(np.flatnonzero(ns["reflectivity"]), [128])
        self.assertEqual(ns["synthetic"].shape, (257,))
        self.assertEqual(np.argmax(ns["synthetic"]), 128)
        self.assertAlmostEqual(ns["time_s"][128], 0.128)
        expected = np.zeros(257)
        expected[64:193] = (31.0 / 721.0) * ns["wavelet"].amplitude
        np.testing.assert_allclose(ns["synthetic"], expected, atol=1e-15)

    def test_wavelet_variants_have_amplitude_and_time_in_correct_order(self):
        for heading in ("Ricker", "Ormsby", "Klauder"):
            with self.subTest(wavelet=heading):
                ns = example("bruges/references/wavelets.md", heading)
                amplitude, time = ns["amplitude"], ns["time_s"]
                self.assertEqual(amplitude.shape, time.shape)
                self.assertTrue(np.all(np.isfinite(amplitude)))
                np.testing.assert_allclose(np.diff(time), 0.001, atol=1e-15)
                center = time.size // 2
                self.assertAlmostEqual(time[center], 0)
                self.assertAlmostEqual(amplitude[center], 1)
                self.assertEqual(np.argmax(amplitude), center)
                np.testing.assert_allclose(amplitude, amplitude[::-1], atol=1e-12)

    def test_phase_rotation_declares_sign_convention(self):
        rotate = example("bruges/references/wavelets.md", "Phase rotation")["phase_rotate"]
        phase = 2 * np.pi * np.arange(256) / 32
        np.testing.assert_allclose(rotate(np.cos(phase), 90), -np.sin(phase), atol=1e-13)
        np.testing.assert_allclose(rotate(np.cos(phase), 180), -np.cos(phase), atol=1e-13)

    def test_elastic_moduli_si_units_and_velocity_roundtrip(self):
        ns = example("bruges/references/rock_physics.md", "Elastic moduli and velocities")
        self.assertAlmostEqual(ns["bulk_gpa"], 35.512 / 3)
        self.assertAlmostEqual(ns["shear_pa"] / 1e9, 6.647)
        self.assertAlmostEqual(ns["poisson"], 161.0 / 611.0)
        self.assertAlmostEqual(ns["youngs_pa"] / ns["shear_pa"], 2 * (1 + ns["poisson"]))
        self.assertAlmostEqual(ns["vp_roundtrip"], 3000)
        self.assertAlmostEqual(ns["vs_roundtrip"], 1700)

    def test_gardner_and_castagna_units(self):
        ns = example("bruges/references/rock_physics.md", "Empirical estimates")
        self.assertAlmostEqual(ns["rho_kg_m3"][1], 2294.256694, places=6)
        self.assertAlmostEqual(ns["rho_g_cm3"][1], 2.294256694, places=9)
        np.testing.assert_allclose(ns["vs_m_s"], [16000 / 29, 41000 / 29, 66000 / 29])

    def test_fluid_substitution_density_shear_invariant_and_identity(self):
        ns = example("bruges/references/rock_physics.md", "Gassmann fluid substitution")
        self.assertAlmostEqual(ns["rho_new"], 2110)
        self.assertAlmostEqual(ns["mu_after"] / ns["mu_before"], 1)
        self.assertLess(ns["vp_new"], ns["vp_sat"])
        self.assertGreater(ns["vs_new"], ns["vs_sat"])
        unchanged = ns["avseth_fluidsub"](
            vp=ns["vp_sat"], vs=ns["vs_sat"], rho=ns["rho_sat"], phi=ns["phi"],
            rhof1=ns["rho_brine"], rhof2=ns["rho_brine"],
            kmin=ns["kmin"], kf1=ns["k_brine"], kf2=ns["k_brine"],
        )
        np.testing.assert_allclose(unchanged, [3000, 1700, 2300], atol=1e-10)


class DisbaDomainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ns = example("disba/SKILL.md", "Phase and group velocity")
        cls.model_ns = example("disba/references/velocity_models.md", "Solid-model validation")
        example("disba/references/velocity_models.md", "Forward function", cls.model_ns)

    def test_layer_columns_and_physical_phase_limits(self):
        ns = self.ns
        for attribute, key in (("thickness", "thickness"), ("velocity_p", "vp"),
                               ("velocity_s", "vs"), ("density", "rho")):
            np.testing.assert_array_equal(getattr(ns["phase_solver"], attribute), ns[key])
        for key in ("rayleigh", "love", "group"):
            curve = ns[key]
            np.testing.assert_array_equal(curve.period, ns["periods"])
            self.assertTrue(np.all(np.isfinite(curve.velocity)))
            self.assertTrue(np.all(curve.velocity > 0))
        self.assertGreater(ns["rayleigh"].velocity[0], 0.7)
        self.assertLess(ns["rayleigh"].velocity[0], 0.8)
        self.assertTrue(np.all(ns["love"].velocity > 0.8))
        self.assertTrue(np.all(ns["love"].velocity < 3.5))

    def test_three_layer_table_preserves_columns(self):
        ns = example("disba/references/velocity_models.md", "Solid-model validation")
        example("disba/references/velocity_models.md", "Layer table", ns)
        np.testing.assert_array_equal(ns["phase_solver"].thickness, [0.5, 1, 0])
        np.testing.assert_array_equal(ns["phase_solver"].velocity_s, [0.8, 1.4, 2.3])
        curve = ns["phase_solver"](np.array([0.5, 1, 2]))
        self.assertEqual(curve.period.size, 3)
        self.assertTrue(np.all(np.isfinite(curve.velocity)))

    def test_homogeneous_rayleigh_analytic_limit(self):
        forward = self.model_ns["forward_model"]
        vp = np.full(3, np.sqrt(3) * 3.0)
        vs, rho = np.full(3, 3.0), np.full(3, 2.5)
        curve = forward([0.5, 1.0, 0], vp, vs, rho, [0.5, 1, 2, 5])
        # Rayleigh secular-equation root for Poisson ratio 0.25: c/Vs.
        np.testing.assert_allclose(curve.velocity, 3 * 0.919401686761966, atol=1e-5)
        group = GroupDispersion(np.array([0.5, 1.0, 0]), vp, vs, rho)(curve.period)
        np.testing.assert_allclose(group.velocity, curve.velocity, atol=1e-5)

    def test_forward_rejects_missing_unstable_or_misaligned_inputs(self):
        forward = self.model_ns["forward_model"]
        valid = dict(thickness=[0.5, 0], vp=[3.0, 4.0], vs=[1.7, 2.3],
                     rho=[2.3, 2.5], periods=[0.5, 1, 2])
        cases = [dict(rho=[2.3]), dict(vp=[[3, 4]]), dict(rho=[2.3, np.nan]),
                 dict(thickness=[-0.5, 0]), dict(thickness=[0.5, 1]),
                 dict(vs=[0, 2.3]), dict(vp=[1.8, 4]), dict(periods=[]),
                 dict(periods=[1, 0.5]), dict(periods=[1, 1]),
                 dict(periods=[0, 1]), dict(periods=[np.nan, 1]),
                 dict(mode=-1), dict(wave="P")]
        for change in cases:
            with self.subTest(change=change), self.assertRaises(ValueError):
                forward(**(valid | change))

    def test_gardner_conversion_from_kilometers(self):
        density = example("disba/references/velocity_models.md", "Density estimates")["gardner_density"]
        self.assertAlmostEqual(float(density(10)), 3.1)
        self.assertAlmostEqual(float(density(3)), 2.294256694, places=9)
        with self.assertRaises(ValueError):
            density(np.nan)

    def test_group_conversion_analytic_and_numerical_curves(self):
        convert = example("disba/references/dispersion_curves.md", "Phase and group velocity")["group_from_phase"]
        periods = np.linspace(0.5, 2.0, 301)
        # Analytic linear phase curve, differentiated independently by hand.
        phase = 2.0 + 0.1 * periods
        np.testing.assert_allclose(convert(periods, phase), phase**2 / (2 + 0.2 * periods))
        ns = self.ns
        phase_curve = ns["phase_solver"](periods)
        group_curve = ns["group_solver"](periods)
        np.testing.assert_array_equal(phase_curve.period, group_curve.period)
        np.testing.assert_allclose(convert(phase_curve.period, phase_curve.velocity)[5:-5],
                                   group_curve.velocity[5:-5], rtol=0.01, atol=0.002)

    def test_higher_modes_keep_partial_returned_periods(self):
        ns = dict(self.ns)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            example("disba/references/dispersion_curves.md", "Higher modes", ns)
        self.assertEqual(ns["mode_errors"], {})
        overtone = ns["modes"][1]
        self.assertGreater(overtone.period.size, 0)
        self.assertLess(overtone.period.size, ns["periods"].size)
        self.assertEqual(overtone.period.shape, overtone.velocity.shape)
        self.assertTrue(np.all(np.isin(overtone.period, ns["periods"])))
        self.assertIn(f"Mode 1: {overtone.period.size} of 50 periods", output.getvalue())

    def test_sensitivity_agrees_with_independent_finite_perturbation(self):
        ns = dict(self.ns)
        example("disba/SKILL.md", "Sensitivity kernels", ns)
        np.testing.assert_allclose(ns["depth_km"], [0, 0.5, 1.5, 3.5])
        self.assertTrue(np.all(np.isfinite(ns["dc_dvs"])))
        changed_vs = ns["vs"].copy()
        changed_vs[0] += 0.001
        perturbed = PhaseDispersion(ns["thickness"], ns["vp"], changed_vs, ns["rho"])(np.array([1.0]))
        original = ns["phase_solver"](np.array([1.0]))
        derivative = (perturbed.velocity[0] - original.velocity[0]) / 0.001
        self.assertAlmostEqual(ns["dc_dvs"][0], derivative, delta=0.04)

    def test_plot_and_frequency_conversion_use_returned_axes(self):
        ns = dict(self.ns)
        example("disba/references/dispersion_curves.md", "Plot returned axes", ns)
        self.addCleanup(ns["plt"].close, ns["fig"])
        for line, curve in zip(ns["ax"].lines, [ns["rayleigh"], ns["love"]]):
            np.testing.assert_array_equal(line.get_xdata(), curve.period)
            np.testing.assert_array_equal(line.get_ydata(), curve.velocity)
        example("disba/references/dispersion_curves.md", "Frequency input", ns)
        self.assertTrue(np.all(np.diff(ns["periods_from_frequency"]) > 0))
        np.testing.assert_allclose(ns["returned_frequency_hz"], ns["frequencies_hz"][::-1])


class DispersionScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / "disba/scripts/dispersion_analysis.py"
        spec = importlib.util.spec_from_file_location("dispersion_analysis", cls.path)
        cls.script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.script)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.model = (np.array([0.5, 1.0, 2.0, 0.0]),
                      np.array([1.5, 2.5, 4.0, 6.0]),
                      np.array([0.8, 1.4, 2.3, 3.5]),
                      np.array([1.8, 2.0, 2.3, 2.6]))

    def run_cli(self, *arguments):
        return subprocess.run([sys.executable, str(self.path), *map(str, arguments)],
                              cwd=self.directory, capture_output=True, text=True,
                              timeout=60, env=os.environ.copy())

    def write_model(self, model=None):
        path = self.directory / "model.txt"
        np.savetxt(path, np.column_stack(self.model if model is None else model),
                   header="thickness vp vs rho", comments="")
        return path

    def test_three_layer_phase_and_group_match_homogeneous_analytic_limit(self):
        vp = np.full(3, 3 * np.sqrt(3))
        model = ([0.5, 1.0, 0.0], vp, np.full(3, 3.0), np.full(3, 2.5))
        results = self.script.compute_dispersion(*model, periods=[0.5, 1, 2, 5])
        self.assertEqual(results["errors"], {})
        for field in ("phase_velocity", "group_velocity"):
            np.testing.assert_allclose(results["modes"][0][field],
                                       3 * 0.919401686761966, atol=1e-5)

    def test_four_layer_partial_modes_roundtrip_to_csv_and_plot(self):
        periods = np.linspace(0.1, 5.0, 50)
        results = self.script.compute_dispersion(*self.model, periods=periods, max_modes=3)
        for kind, solver in (("phase", PhaseDispersion), ("group", GroupDispersion)):
            direct = solver(*self.model)(periods, mode=1)
            values = results["modes"][1][f"{kind}_velocity"]
            available = np.isfinite(values)
            self.assertGreater(np.count_nonzero(available), 0)
            self.assertLess(np.count_nonzero(available), periods.size)
            np.testing.assert_array_equal(periods[available], direct.period)
            np.testing.assert_allclose(values[available], direct.velocity)
        csv_path = self.directory / "curves.csv"
        plot_path = self.directory / "curves.png"
        with contextlib.redirect_stdout(io.StringIO()):
            self.script.print_dispersion(results)
            self.script.save_dispersion(results, csv_path)
            self.script.plot_dispersion(results, show=False, save_path=plot_path)
        saved = np.genfromtxt(csv_path, delimiter=",", names=True)
        self.assertEqual(saved.shape, (50,))
        np.testing.assert_array_equal(saved["period_s"], periods)
        for mode in range(3):
            for kind in ("phase", "group"):
                np.testing.assert_allclose(saved[f"{kind}_mode{mode}_km_s"],
                                           results["modes"][mode][f"{kind}_velocity"],
                                           equal_nan=True)
        from matplotlib.image import imread
        self.assertGreater(imread(plot_path).size, 0)

    def test_script_sensitivity_keeps_layer_depths_and_velocity_units(self):
        kernels = self.script.compute_sensitivity(*self.model, period=1.0)
        self.assertEqual(set(kernels), {"velocity_s", "velocity_p", "density"})
        for key, kernel in kernels.items():
            self.assertEqual(kernel.parameter, key)
            np.testing.assert_allclose(kernel.depth, [0, 0.5, 1.5, 3.5])
            self.assertTrue(np.all(np.isfinite(kernel.kernel)))
            self.assertGreater(kernel.velocity, 0.7)
            self.assertLess(kernel.velocity, 0.9)

    def test_model_file_validates_header_shape_and_halfspace(self):
        path = self.write_model()
        for actual, expected in zip(self.script.load_model_file(path), self.model):
            np.testing.assert_array_equal(actual, expected)
        for contents in ("0.5 1.5 0.8 1.8\n0 4 2.3 2.3\n",
                         "thickness vp vs rho\n0 4 2.3\n",
                         "thickness vp vs rho\n0 4 nan 2.3\n",
                         "thickness vp vs rho\n1 4 2.3 2.3\n"):
            path.write_text(contents)
            with self.subTest(contents=contents), self.assertRaises(ValueError):
                self.script.load_model_file(path)
        path.write_text("thickness vp vs rho\n0 4 2.3 2.3\n")
        self.assertEqual(self.script.load_model_file(path)[0].shape, (1,))

    def test_invalid_model_and_periods_fail_before_root_search(self):
        for periods in ([1, 0.5], [1, 1], [0, 1], [np.nan, 1], []):
            with self.subTest(periods=periods), self.assertRaises(ValueError):
                self.script.compute_dispersion(*self.model, periods=periods)
        with self.assertRaises(ValueError):
            self.script.compute_dispersion(*self.model, max_modes=0)
        with self.assertRaises(ValueError):
            self.script.compute_dispersion(*self.model, wave="P")
        with self.assertRaises(ValueError):
            self.script.compute_sensitivity(*self.model, period=0)
        with self.assertRaises(ValueError):
            self.script.compute_dispersion([1, 0], [1.8, 4], [1.7, 2.3], [2.3, 2.5])

    def test_cli_exports_three_layer_model_on_requested_period_grid(self):
        model = ([0.5, 1, 0], np.full(3, 3 * np.sqrt(3)), np.full(3, 3.0), np.full(3, 2.5))
        source = self.write_model(model)
        output = self.directory / "output.csv"
        result = self.run_cli("--model", "file", "--input", source, "--output", output,
                              "--modes", 1, "--period-min", 0.5, "--period-max", 2,
                              "--n-periods", 4)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = np.genfromtxt(output, delimiter=",", names=True)
        np.testing.assert_allclose(data["period_s"], [0.5, 1, 1.5, 2])
        np.testing.assert_allclose(data["phase_mode0_km_s"], 3 * 0.919401686761966, atol=1e-5)
        np.testing.assert_allclose(data["group_mode0_km_s"], 3 * 0.919401686761966, atol=1e-5)

    def test_cli_rejects_invalid_bounds_and_preserves_input_aliases(self):
        source = self.write_model()
        original = source.read_bytes()
        output = self.directory / "should-not-exist.csv"
        base = ("--model", "file", "--input", source, "--output", output)
        for arguments in (("--period-min", 2, "--period-max", 1),
                          ("--period-min", "nan"), ("--n-periods", 1), ("--modes", 0)):
            with self.subTest(arguments=arguments):
                result = self.run_cli(*base, *arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Error:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse(output.exists())
        result = self.run_cli("--model", "file", "--input", source, "--output", source)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(source.read_bytes(), original)
        alias = self.directory / "model-alias.txt"
        os.link(source, alias)
        result = self.run_cli("--model", "file", "--input", source, "--plot-file", alias)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(source.read_bytes(), original)
        self.assertEqual(alias.read_bytes(), original)

    def test_cli_does_not_report_success_when_no_love_roots_exist(self):
        model = ([0.5, 1, 0], np.full(3, 3 * np.sqrt(3)), np.full(3, 3.0), np.full(3, 2.5))
        source = self.write_model(model)
        output = self.directory / "no-roots.csv"
        result = self.run_cli("--model", "file", "--input", source, "--output", output,
                              "--wave", "love", "--modes", 1, "--n-periods", 3,
                              "--period-min", 0.5, "--period-max", 2)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No dispersion roots computed", result.stderr)
        self.assertFalse(output.exists())


class AvoScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = ROOT / "bruges/scripts/avo_analysis.py"
        spec = importlib.util.spec_from_file_location("avo_analysis", cls.path)
        cls.script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.script)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.upper = self.script.LayerProperties(3000, 1700, 2.3)
        self.lower = self.script.LayerProperties(3200, 1800, 2.35)
        self.arguments = ["--vp1", "3000", "--vs1", "1700", "--rho1", "2.3",
                          "--vp2", "3200", "--vs2", "1800", "--rho2", "2.35"]

    def run_cli(self, *arguments, block_bruges=False):
        command = [sys.executable, str(self.path), *self.arguments, *map(str, arguments)]
        if block_bruges:
            # Isolate dependency absence without uninstalling or mocking physics.
            blocker = """import importlib.abc, runpy, sys
class MissingBruges(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'bruges' or fullname.startswith('bruges.'):
            raise ModuleNotFoundError('Bruges deliberately unavailable in this test')
sys.meta_path.insert(0, MissingBruges())
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
"""
            command = [sys.executable, "-c", blocker, str(self.path),
                       *self.arguments, *map(str, arguments)]
        return subprocess.run(command, cwd=self.directory, capture_output=True,
                              text=True, timeout=60, env=os.environ.copy())

    def test_exact_normal_incidence_and_named_approximation(self):
        from bruges.reflection import shuey
        results = self.script.analyze_avo(self.upper, self.lower, theta_max=30)
        self.assertAlmostEqual(float(np.real(results["Rpp"][0])), 31 / 721, places=10)
        self.assertAlmostEqual(results["impedance_contrast"], 31 / 721, places=10)
        expected = shuey(3000, 1700, 2.3, 3200, 1800, 2.35, return_gradient=True)
        np.testing.assert_allclose([results["intercept"], results["gradient"]], expected)
        identical = self.script.zoeppritz(self.upper, self.upper, [0, 15, 30])
        np.testing.assert_allclose(identical, 0, atol=1e-14)
        report = io.StringIO()
        with contextlib.redirect_stdout(report):
            self.script.print_report(results)
        self.assertIn("Upper Zp: 6900000 kg/(m² s)", report.getvalue())
        self.assertIn("Heuristic AVO Class", report.getvalue())
        self.assertNotEqual(self.script.classify_avo(0.0, 0.01), "IIp")

    def test_angle_grid_and_invalid_elastic_inputs(self):
        results = self.script.analyze_avo(self.upper, self.lower, theta_max=30.5, theta_step=7)
        np.testing.assert_array_equal(results["theta"], [0, 7, 14, 21, 28, 30.5])
        zero = self.script.analyze_avo(self.upper, self.lower, theta_max=0)
        self.assertEqual(zero["Rpp"].shape, (1,))
        for change in (dict(theta_max=90), dict(theta_max=-1), dict(theta_max=np.nan),
                       dict(theta_step=0), dict(theta_step=-1), dict(theta_step=np.inf)):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.script.analyze_avo(self.upper, self.lower, **change)
        for properties in ((3000, 0, 2.3), (3000, 1700, np.nan),
                           (1800, 1700, 2.3), (3000, 1700, -2.3)):
            with self.subTest(properties=properties), self.assertRaises(ValueError):
                self.script.LayerProperties(*properties)

    def test_postcritical_plot_preserves_real_and_imaginary_reflectivity(self):
        upper = self.script.LayerProperties(2000, 1000, 2.2)
        lower = self.script.LayerProperties(4000, 2000, 2.4)
        results = self.script.analyze_avo(upper, lower, theta_max=45)
        self.assertGreater(np.max(np.abs(results["Rpp"].imag)), 0.5)
        output = self.directory / "postcritical.png"
        with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings(record=True) as caught:
            figure = self.script.plot_avo(results, output)
        self.assertFalse(any(w.category.__name__ == "ComplexWarning" for w in caught))
        lines = {line.get_label(): line for line in figure.axes[0].lines}
        np.testing.assert_allclose(lines["Zoeppritz (real)"].get_ydata(), results["Rpp"].real)
        np.testing.assert_allclose(lines["Zoeppritz (imaginary)"].get_ydata(), results["Rpp"].imag)
        from matplotlib.image import imread
        self.assertGreater(imread(output).size, 0)

    def test_missing_bruges_is_an_explicit_cli_failure(self):
        output = self.directory / "must-not-be-produced.png"
        result = self.run_cli("--plot", output, block_bruges=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Bruges is required for exact Zoeppritz", result.stderr)
        self.assertNotIn("AVO ANALYSIS REPORT", result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        self.assertFalse(output.exists())

    def test_cli_saves_requested_plot_even_when_display_suppressed(self):
        output = self.directory / "avo.png"
        result = self.run_cli("--plot", output, "--no-plot")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("AVO ANALYSIS REPORT", result.stdout)
        self.assertIn("R(0 deg): 0.0430", result.stdout)
        self.assertTrue(output.is_file())

    def test_cli_invalid_velocity_or_angle_exits_without_artifacts(self):
        output = self.directory / "invalid.png"
        for arguments in (("--vp1", "nan"), ("--rho1", "-1"),
                          ("--theta-max", "90"), ("--vp1", "1800")):
            with self.subTest(arguments=arguments):
                result = self.run_cli(*arguments, "--plot", output)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Error:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
