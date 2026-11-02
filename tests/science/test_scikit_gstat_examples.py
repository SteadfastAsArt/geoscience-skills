"""Execute SciKit-GStat instructions and helpers with independent numerical checks."""

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import skgstat as skg
from skgstat.Kriging import KrigingWarning


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "scikit-gstat"
SCRIPT = SKILL / "scripts/variogram_analysis.py"
spec = importlib.util.spec_from_file_location("variogram_analysis", SCRIPT)
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def example(path, heading, namespace=None):
    text = path.read_text()
    section = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if section is None:
        raise AssertionError(f"Missing section {heading!r}")
    block = re.search(r"^```python\n(.*?)^```", section[1], re.M | re.S)
    if block is None:
        raise AssertionError(f"Missing example {heading!r}")
    namespace = {} if namespace is None else namespace
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(block[1], str(path) + ":" + heading, "exec"), namespace)
    return namespace


def samples():
    rng = np.random.default_rng(13)
    coords = rng.uniform(0, 100, (90, 2))
    values = np.sin(coords[:, 0] / 25) + np.cos(coords[:, 1] / 30) + rng.normal(0, .08, 90)
    return coords, values


def spherical_kriging(coords, values, target, distance_range, partial_sill, nugget, max_points=12):
    """Independent ordinary-kriging system, using Euclidean distances explicitly."""
    distance = np.sqrt(np.sum((coords - target) ** 2, axis=1))
    selected = np.argsort(distance[distance <= distance_range])[:max_points]
    eligible = np.flatnonzero(distance <= distance_range)
    selected = eligible[selected]
    points = coords[selected]

    def gamma(h):
        ratio = np.asarray(h) / distance_range
        return nugget + partial_sill * np.where(ratio < 1, 1.5 * ratio - .5 * ratio**3, 1)

    matrix = np.ones((len(points) + 1, len(points) + 1))
    pair_distance = np.sqrt(np.sum((points[:, None, :] - points[None, :, :]) ** 2, axis=2))
    matrix[:-1, :-1] = gamma(pair_distance)
    np.fill_diagonal(matrix, 0)
    rhs = np.r_[gamma(distance[selected]), 1.]
    solution = np.linalg.solve(matrix, rhs)
    return solution[:-1] @ values[selected], rhs[:-1] @ solution[:-1] + solution[-1]


class ScikitGStatExamples(unittest.TestCase):
    def test_entrypoint_predictions_and_variance_match_independent_linear_system(self):
        ns = example(SKILL / "SKILL.md", "Ordinary kriging example")
        parameters = ns["V"].describe(short=True)
        expected = [spherical_kriging(ns["coords"], ns["values"], point,
                    parameters["effective_range"], parameters["sill"], parameters["nugget"])
                    for point in ns["grid_coords"]]
        np.testing.assert_allclose(ns["predictions"], np.array(expected)[:, 0], atol=1e-10)
        np.testing.assert_allclose(ns["variance"], np.array(expected)[:, 1], atol=1e-10)
        self.assertTrue(ns["supported"].all())

    def test_reference_variance_is_copied_before_another_transform(self):
        coords, values = samples()
        ns = example(SKILL / "references/kriging_methods.md", "Predictions and conditional variance",
                     {"coords": coords, "values": values, "grid_coords": np.array([[45., 45.], [55., 55.]])})
        before = ns["variance"].copy()
        ns["ok"].transform(np.array([50.]), np.array([50.]))
        np.testing.assert_array_equal(ns["variance"], before)
        self.assertEqual(ns["ok"].sigma.shape, (1,))

    def test_matern_and_stable_named_parameters_preserve_nonzero_nugget(self):
        coords, values = samples()
        for model, shape_name in [("matern", "smoothness"), ("stable", "shape")]:
            with self.subTest(model=model):
                variogram = skg.Variogram(coords, values, model=model, use_nugget=True,
                                         fit_method="manual", fit_range=70, fit_sill=2.5,
                                         fit_shape=1.5, fit_nugget=.4)
                actual = analysis.model_parameters(variogram)
                self.assertEqual(actual, {"range": 70., "sill": 2.5, "nugget": .4, shape_name: 1.5})
                ns = example(SKILL / "references/variogram_models.md", "Named parameters and evaluation",
                             {"V": variogram, "lags": np.array([0., 10., 1000.])})
                self.assertEqual(ns["nugget"], .4)
                self.assertEqual(ns["total_sill"], 2.9)
                self.assertEqual(ns["shape"], {shape_name: 1.5})
                self.assertAlmostEqual(ns["semivariance"][0], .4)
                self.assertAlmostEqual(ns["semivariance"][-1], 2.9, places=7)

    def test_fit_summary_keeps_matern_smoothness_separate_from_zero_nugget(self):
        result, _ = analysis.analyze_variogram(*samples(), n_lags=10)
        self.assertEqual({m["name"] for m in result["models"]}, {"spherical", "exponential", "gaussian", "matern"})
        self.assertEqual(result["model_failures"], {})
        self.assertTrue(all(m["nugget"] == 0 for m in result["models"]))
        matern = next(m for m in result["models"] if m["name"] == "matern")
        self.assertGreater(matern["smoothness"], 0)
        self.assertEqual(result["best_model"], min(result["models"], key=lambda x: x["rmse"])["name"])

    def test_holdout_values_cannot_change_fit_predictions_variance_or_baseline(self):
        coords, values = samples()
        mask = coords[:, 0] > 70
        path = SKILL / "references/kriging_methods.md"
        before = example(path, "Spatial holdout", {"coords": coords, "values": values, "test_mask": mask})
        altered = values.copy()
        altered[mask] += 1000
        after = example(path, "Spatial holdout", {"coords": coords, "values": altered, "test_mask": mask})
        np.testing.assert_array_equal(before["V_train"].parameters, after["V_train"].parameters)
        for name in ("prediction", "variance"):
            np.testing.assert_array_equal(before[name], after[name])
        self.assertEqual(before["baseline"], after["baseline"])
        self.assertGreater(after["report"]["rmse_on_supported"], 900)
        supported = before["supported"]
        self.assertGreater(supported.sum(), 0)
        expected = np.sqrt(np.mean((values[mask][supported] - values[~mask].mean()) ** 2))
        self.assertAlmostEqual(before["report"]["baseline_rmse_on_same_targets"], expected)

    def test_unsupported_holdout_remains_missing_with_no_score(self):
        coords, values = samples()
        mask = coords[:, 0] > 70
        coords[mask] += 10000
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", KrigingWarning)
            ns = example(SKILL / "references/kriging_methods.md", "Spatial holdout",
                         {"coords": coords, "values": values, "test_mask": mask})
        self.assertTrue(np.isnan(ns["prediction"]).all())
        self.assertTrue(np.isnan(ns["variance"]).all())
        self.assertEqual(ns["report"]["coverage"], 0)
        self.assertEqual(ns["report"]["unsupported"], int(mask.sum()))
        self.assertIsNone(ns["report"]["rmse_on_supported"])
        self.assertIsNone(ns["report"]["baseline_rmse_on_same_targets"])

    def test_empty_holdout_partition_is_rejected(self):
        coords, values = samples()
        for mask in (np.zeros(len(values), dtype=bool), np.ones(len(values), dtype=bool)):
            with self.assertRaisesRegex(ValueError, "both training and test"):
                example(SKILL / "references/kriging_methods.md", "Spatial holdout",
                        {"coords": coords, "values": values, "test_mask": mask})

    def test_csv_missing_rows_are_removed_in_pairs_without_fabricated_zeros(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "measurements.csv"
            path.write_text("x,y,value\n0,0,1\n1,1,2\n2,2,3\n3,3,\n,4,5\n")
            original = path.read_bytes()
            coords, values = analysis.load_data(path, "x", "y", "value")
            np.testing.assert_array_equal(coords, [[0, 0], [1, 1], [2, 2]])
            np.testing.assert_array_equal(values, [1, 2, 3])
            self.assertEqual(path.read_bytes(), original)

    def test_duplicate_nonfinite_empty_and_constant_inputs_are_rejected(self):
        coords, values = samples()
        for bad_coords, bad_values in [
            (np.r_[coords[:2], coords[:1]], values[:3]),
            (coords, np.full(len(values), np.inf)),
            (coords[:0], values[:0]), (coords, np.ones(len(values))),
            (coords[:, 0], values),
        ]:
            with self.subTest(shape=np.shape(bad_coords)), self.assertRaises(ValueError):
                analysis.validate_samples(bad_coords, bad_values)

    def test_matern_plot_retains_fitted_nugget_and_total_sill(self):
        coords, values = samples()
        variogram = skg.Variogram(coords, values, model="matern", use_nugget=True,
                                 fit_method="manual", fit_range=20, fit_sill=2.5,
                                 fit_shape=1.5, fit_nugget=.4)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "matern.png"
            with patch.object(plt, "close"):
                analysis.plot_variogram(variogram, str(output))
                ax = plt.gcf().axes[0]
                curve = ax.lines[0].get_ydata()
                self.assertAlmostEqual(curve[0], .4)
                self.assertAlmostEqual(curve[-1], 2.9, places=5)
                self.assertIn("Nugget: 0.4000", ax.texts[0].get_text())
            plt.close("all")
            self.assertEqual(output.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_cli_numeric_maxlag_and_nugget_export_reopen(self):
        coords, values = samples()
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            source = directory / "samples.csv"
            pd.DataFrame({"x": coords[:, 0], "y": coords[:, 1], "z": values}).to_csv(source, index=False)
            original = source.read_bytes()
            output = directory / "results"
            result = subprocess.run([sys.executable, str(SCRIPT), str(source), "--x", "x", "--y", "y",
                "--z", "z", "--output", str(output), "--n-lags", "10", "--maxlag", "60", "--use-nugget"],
                env=dict(os.environ, MPLBACKEND="Agg"), capture_output=True, text=True, timeout=90)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads((output / "variogram_results.json").read_text(),
                                parse_constant=lambda value: self.fail(f"Nonfinite JSON: {value}"))
            self.assertTrue(report["variogram"]["use_nugget"])
            for model in report["variogram"]["models"]:
                self.assertLessEqual(model["range"], 60.000001)
                self.assertGreaterEqual(model["nugget"], 0)
            for name in ("variogram.png", "model_comparison.png"):
                self.assertEqual((output / name).read_bytes()[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(source.read_bytes(), original)

    def test_all_failed_model_fits_cannot_be_exported_as_success(self):
        with patch.object(analysis, "model_parameters", side_effect=ValueError("nonfinite")):
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(ValueError, "No variogram model"):
                analysis.analyze_variogram(*samples())


if __name__ == "__main__":
    unittest.main()
