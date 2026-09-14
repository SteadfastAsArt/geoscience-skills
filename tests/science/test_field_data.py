"""Offline real-GNSS fixture, weighted-fit and conditional-uncertainty checks.

Use requirements-models.txt, then unittest discover -s tests/science
-p test_field_data.py -v. Missing scientific libraries intentionally fail imports.
"""

from pathlib import Path
import shutil
import tempfile
import unittest

import numpy as np
import pandas as pd
from scipy.stats import chi2, norm
import verde as vd

from field_support import (
    ERROR, FIXTURE, VALUE, design_matrix, field_report, fit_vertical_trend,
    load_field_data, longitude_strip_holdout, reconstruct_published_table, verify_files,
    source_coordinate_disagreements,
)


class FieldDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_field_data()
        cls.fit = fit_vertical_trend(cls.data)
        cls.holdout = longitude_strip_holdout(cls.data)

    def test_pinned_sources_license_and_coordinate_metadata(self):
        manifest = verify_files()
        self.assertEqual(manifest["curation"]["git_revision"],
                         "123af5d44f4e872300c6eda5455f1fed8f9d5acf")
        self.assertEqual(manifest["files"]["alps-gps-velocity.csv.xz"]["sha256"],
                         "77f2907c2a019366e5f85de5aafcab2d0e90cc2c378171468a7705cab9938584")
        self.assertEqual(manifest["original"]["license"], "CC-BY-3.0")
        self.assertEqual(manifest["curation"]["license"], "CC-BY-4.0")
        header = (FIXTURE / "ALPS2017_NEH.CRD").read_text(encoding="latin-1")
        for value in ("IGb08/ITRF2008", "GRS80", "2010-01-01 00:00:00"):
            self.assertIn(value, header)
        self.assertEqual(manifest["coordinates"]["reference_frame"], "IGb08/ITRF2008")
        self.assertEqual(manifest["columns"]["longitude_error_m"], "m")
        self.assertEqual(manifest["columns"]["longitude"], "degree")

    def test_corrupted_fixture_is_rejected_before_analysis(self):
        with tempfile.TemporaryDirectory(prefix="geoscience-field-integrity-") as directory:
            copy = Path(directory) / "alps_gps"
            shutil.copytree(FIXTURE, copy)
            data_file = copy / "ALPS2017_NEH.VEL"
            contents = bytearray(data_file.read_bytes())
            contents[-1] ^= 1
            data_file.write_bytes(contents)
            with self.assertRaisesRegex(ValueError, "ALPS2017_NEH.VEL"):
                load_field_data(copy)

    def test_every_published_value_reconstructs_from_original_observations(self):
        actual = reconstruct_published_table()
        pd.testing.assert_frame_equal(actual, self.data, check_exact=True)
        self.assertEqual(len(actual), 186)
        self.assertTrue(actual.station_id.is_unique)
        self.assertTrue({"CHIZ", "IENG"}.issubset(set(actual.station_id)))
        self.assertTrue(np.isfinite(actual.drop(columns="station_id")).all().all())
        # No placeholder or gap filling: every reported uncertainty is present.
        self.assertTrue((actual.filter(like="_error_") > 0).all().all())

    def test_real_verde_fit_satisfies_weighted_least_squares_conditions(self):
        fit = self.fit
        sigma = self.data[ERROR].to_numpy()
        residual = self.data[VALUE].to_numpy() - fit["predicted"]
        # A weighted LS optimum has zero residual moment for each basis vector.
        moments = (fit["design"] / sigma[:, None]).T @ (residual / sigma)
        np.testing.assert_allclose(moments, 0, atol=1e-9)
        np.testing.assert_allclose(fit["design"] @ fit["model"].coef_, fit["predicted"],
                                   rtol=1e-12, atol=1e-12)
        self.assertIsInstance(fit["model"], vd.Trend)
        self.assertEqual(fit["degrees_of_freedom"], 186 - 3)
        self.assertTrue((np.linalg.eigvalsh(fit["covariance"]) > 0).all())

    def test_report_rejects_inadequate_plane_without_inflating_observation_errors(self):
        report = field_report()
        # Formal errors are fixed inputs: no residual-based sigma inflation or
        # tuned RMSE tolerance may turn this scientifically inadequate model green.
        self.assertTrue(report["noise_only_model_rejected"])
        self.assertGreater(report["chi_square"], chi2.ppf(0.99, 183))
        self.assertEqual(report["degrees_of_freedom"], 183)
        self.assertGreater(report["holdout_rmse_mmyr"],
                           report["holdout_mean_baseline_rmse_mmyr"])
        # Coverage is descriptive: correlated holdouts do not justify a binomial
        # significance test or a claim of calibrated 95% field prediction accuracy.
        self.assertLess(report["conditional_95_interval_coverage"], 0.95)

    def test_original_coordinate_disagreements_are_reported_not_silently_corrected(self):
        discrepancies = source_coordinate_disagreements()
        self.assertEqual(set(discrepancies), {"WTZR", "ZIMM"})
        self.assertAlmostEqual(discrepancies["WTZR"]["max_coordinate_difference_degree"],
                               0.0024111, places=10)
        self.assertAlmostEqual(discrepancies["ZIMM"]["max_coordinate_difference_degree"],
                               0.0002781, places=10)
        self.assertEqual(field_report()["source_coordinate_disagreements"], discrepancies)

    def test_error_rescaling_preserves_fit_and_scales_variance(self):
        scaled = self.data.copy()
        scaled[ERROR] *= 2
        fit = fit_vertical_trend(scaled)
        np.testing.assert_allclose(fit["predicted"], self.fit["predicted"], atol=1e-12)
        np.testing.assert_allclose(fit["covariance"], 4 * self.fit["covariance"], rtol=1e-12)
        self.assertAlmostEqual(fit["chi_square"], self.fit["chi_square"] / 4, places=9)

    def test_spatial_holdouts_have_no_station_leakage_and_match_independent_baseline(self):
        holdout = self.holdout
        visits = np.zeros(len(self.data), dtype=int)
        for split in holdout["fits"]:
            train, test = split["train"], split["test"]
            self.assertFalse(np.any(train & test))
            self.assertTrue(np.all(train | test))
            self.assertTrue(set(holdout["fold"][train]).isdisjoint(holdout["fold"][test]))
            self.assertEqual(split["fit"]["degrees_of_freedom"], train.sum() - 3)
            visits[test] += 1
            sigma = self.data.loc[train, ERROR].to_numpy()
            values = self.data.loc[train, VALUE].to_numpy()
            # Independent inverse-variance mean, not the full-data mean.
            mean = np.sum(values / sigma ** 2) / np.sum(1 / sigma ** 2)
            np.testing.assert_allclose(holdout["mean_baseline"][test], mean, atol=1e-12)
        np.testing.assert_array_equal(visits, np.ones(len(self.data)))
        self.assertTrue(np.isfinite(holdout["predicted"]).all())
        self.assertTrue((holdout["conditional_prediction_variance"] > 0).all())

    def test_conditional_uncertainty_matches_repeated_real_library_fits(self):
        # The fixture is observed data. These labelled synthetic perturbations
        # test only how the linear estimator propagates an assumed noise model.
        rng = np.random.default_rng(20260914)
        repetitions = 512
        coefficients = []
        perturbed = self.data.copy()
        observed, sigma = self.data[VALUE].to_numpy(), self.data[ERROR].to_numpy()
        design = design_matrix(self.data)
        for _ in range(repetitions):
            perturbed[VALUE] = observed + rng.normal(size=len(observed)) * sigma
            model = vd.Trend(degree=1).fit((design[:, 1], design[:, 2]),
                                          perturbed[VALUE].to_numpy(), weights=sigma ** -2)
            coefficients.append(model.coef_)
        coefficients = np.asarray(coefficients)
        expected_variance = np.diag(self.fit["covariance"])
        # Six simultaneous checks (three means and three variances). Bonferroni
        # allocates an overall nominal false failure probability <= 0.001.
        tail = 0.001 / (2 * 6)
        variance_ratio = coefficients.var(axis=0, ddof=1) / expected_variance
        bounds = chi2.ppf([tail, 1 - tail], repetitions - 1) / (repetitions - 1)
        self.assertTrue(np.all((variance_ratio > bounds[0]) & (variance_ratio < bounds[1])))
        mean_z = (coefficients.mean(axis=0) - self.fit["model"].coef_) / np.sqrt(
            expected_variance / repetitions)
        self.assertTrue(np.all(abs(mean_z) < norm.ppf(1 - tail)))

    def test_missing_errors_and_rank_deficiency_are_explicit_failures(self):
        for value in (0.0, -0.1, np.nan):
            bad = self.data.copy()
            bad.loc[0, ERROR] = value
            with self.assertRaisesRegex(ValueError, "positive sigma"):
                fit_vertical_trend(bad)
        bad = self.data.copy()
        bad["longitude"] = 10.0
        with self.assertRaisesRegex(ValueError, "full-rank"):
            fit_vertical_trend(bad)


if __name__ == "__main__":
    unittest.main()
