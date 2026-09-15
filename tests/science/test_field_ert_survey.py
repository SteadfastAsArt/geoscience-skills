"""Observed ERT fit/holdout and independent synthetic recovery (modelling stack)."""

import unittest

import numpy as np
import pygimli as pg

from field_case_support import verify_case
from field_ert_support import (
    REPEATABILITY, RHO, SPACING, ert_results, fit_layers, geometric_factors,
    image_series_response, load_survey, make_forward, observed_container, reciprocal_groups,
)


class FieldERTTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report, cls.results = ert_results()

    def test_fixed_original_sources_license_and_first_acquisition_selection(self):
        directory, metadata = verify_case("ert_survey")
        self.assertEqual(metadata["dataset"]["license"], "CC-BY-4.0")
        self.assertEqual(metadata["dataset"]["doi"], "10.5281/zenodo.18183049")
        self.assertEqual(metadata["files"]["Resistivity_data.csv.gz"]["uncompressed_sha256"],
                         "f8e946266becbe811506f534082abe758c942bd54686970e550596adbcb4cdc6")
        rows, positions, _ = load_survey()
        np.testing.assert_array_equal(rows.meas_num, np.arange(1, 319))
        np.testing.assert_array_equal(positions.iloc[:, 2], np.arange(1, 14))
        self.assertIn("EPSG32632", positions.columns[3])
        self.assertIn("EPSG32632", positions.columns[4])
        self.assertNotEqual(self.report["surveyed_endpoint_span_m"], 48.0)

    def test_instrument_rhoa_matches_signed_voltage_current_with_rounding_bounds(self):
        rows = self.results["original"]
        factor = geometric_factors(rows)
        voltage, current = rows.iloc[:, 8].to_numpy(), rows.iloc[:, 9].to_numpy()
        expected = factor * voltage / current  # mV / mA = ohm, no extra 1000
        # Source rounds rho to 0.01 ohm m and V,I to 0.001 mV,mA.
        # A conservative ratio bound uses the smallest possible positive I.
        rounding = (0.005 + abs(factor) * (0.0005 / (current - 0.0005)
                    + abs(voltage) * 0.0005 / (current * (current - 0.0005))))
        self.assertTrue(np.all(abs(expected - rows[RHO].to_numpy()) <= rounding))
        container = observed_container(rows)
        # Direct core call avoids pyGIMLi's optional disk-cache wrapper.
        np.testing.assert_allclose(np.asarray(pg.core.geometricFactors(container, dim=3)),
                                   factor, rtol=1e-12, atol=1e-12)
        np.testing.assert_array_equal(np.asarray(container["a"]), rows.A.to_numpy() - 1)
        self.assertEqual(container.sensorCount(), len(SPACING))

    def test_nonpositive_resistivity_is_excluded_but_signed_voltages_are_kept(self):
        self.assertEqual(self.report["nonpositive_rhoa_excluded_from_log_fit"], 2)
        self.assertGreater(self.report["negative_voltages_retained"], 100)
        self.assertGreater(self.report["zero_reported_repeatability_values"], 0)
        self.assertTrue(np.all(self.results["fit"]["log_sigma"] >= 0.03))
        with self.assertRaisesRegex(ValueError, "positive finite"):
            fit_layers(self.results["original"])

    def test_two_layer_model_is_rejected_under_declared_error_budget(self):
        self.assertEqual(self.report["degrees_of_freedom"], 316 - 3)
        self.assertTrue(self.report["conditional_layered_model_rejected"])
        self.assertGreater(self.report["chi_square"], self.report["critical_99"])
        self.assertIsNone(self.report["ground_truth"])
        # Independently computed sum versus the inversion's per-datum statistic.
        fit = self.results["fit"]
        self.assertAlmostEqual(fit["chi_square"] / 316,
                               fit["library_chi_square_per_datum"], places=9)
        # A separate optimizer checks local convergence and the three fitted
        # directions, so a prematurely stopped inversion cannot alone create
        # the failed-fit conclusion. This does not prove a global minimum.
        from scipy.optimize import least_squares
        rows = self.results["rows"]
        forward = make_forward(rows)
        target = np.log(rows[RHO].to_numpy())
        def residual(log_model):
            return (np.log(np.asarray(forward.response(np.exp(log_model))))
                    - target) / fit["log_sigma"]
        refined = least_squares(residual, np.log(fit["model"]), max_nfev=100)
        self.assertTrue(refined.success)
        self.assertEqual(np.linalg.matrix_rank(refined.jac), 3)
        refined_statistic = float(refined.fun @ refined.fun)
        self.assertLess(abs(refined_statistic / fit["chi_square"] - 1), 0.001)
        self.assertGreater(refined_statistic, self.report["critical_99"])

    def test_geometry_only_holdout_keeps_reciprocals_and_targets_out_of_training(self):
        result = self.results
        train, test = result["train"], result["test"]
        self.assertTrue(train.any() and test.any())
        self.assertFalse(np.any(train & test))
        self.assertTrue(set(result["groups"][train]).isdisjoint(result["groups"][test]))
        original = result["rows"].iloc[:1].copy()
        reciprocal = original.copy()
        reciprocal[["A", "B", "M", "N"]] = original[["N", "M", "B", "A"]].to_numpy()
        self.assertEqual(reciprocal_groups(original)[0], reciprocal_groups(reciprocal)[0])
        y = np.log(result["rows"][RHO].to_numpy())
        weights = result["fit"]["log_sigma"][train] ** -2
        baseline = np.sum(weights * y[train]) / np.sum(weights)
        expected = np.sqrt(np.mean((y[test] - baseline) ** 2))
        self.assertAlmostEqual(expected, self.report["training_log_mean_baseline_holdout_rmse"])
        self.assertTrue(np.isfinite(result["holdout_prediction"]).all())

    def test_forward_solver_agrees_with_independent_two_layer_image_series(self):
        rows = self.results["rows"]
        expected = image_series_response(rows, 5.0, 100.0, 300.0)
        refined = image_series_response(rows, 5.0, 100.0, 300.0, terms=160)
        np.testing.assert_allclose(expected, refined, rtol=1e-13, atol=1e-10)
        actual = np.asarray(make_forward(rows).response([5.0, 100.0, 300.0]))
        np.testing.assert_allclose(actual, expected, rtol=1e-7, atol=1e-7)
        # A homogeneous halfspace has rho_a=rho for every quadrupole.
        homogeneous = image_series_response(rows, 5.0, 150.0, 150.0)
        np.testing.assert_allclose(homogeneous, 150.0, rtol=1e-13, atol=1e-10)

    def test_controlled_recovery_from_independent_synthetic_data(self):
        rows = self.results["rows"]
        truth = np.array([5.0, 100.0, 300.0])
        clean = image_series_response(rows, *truth)
        rng = np.random.default_rng(20260914)
        sigma = np.full(len(rows), 0.02)
        # Explicit multiplicative synthetic noise. No field readings are replaced
        # or relabelled as known underground truth.
        observed = clean * np.exp(rng.normal(size=len(rows)) * sigma)
        fit = fit_layers(rows, observed, sigma, start=(3.0, 150.0, 200.0))
        # Predeclared 5% parameter-recovery criterion for this small contrast,
        # geometry, sample count and 2% log-noise experiment only.
        np.testing.assert_allclose(fit["model"], truth, rtol=0.05, atol=0)
        from scipy.stats import chi2
        bounds = chi2.ppf([0.005, 0.995], len(rows) - 3)
        self.assertGreater(fit["chi_square"], bounds[0])
        self.assertLess(fit["chi_square"], bounds[1])


if __name__ == "__main__":
    unittest.main()
