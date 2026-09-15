"""Crescentino observations and an explicitly limited two-layer DC diagnostic.

Uses the modelling stack. The independent image-series response below supplies
the controlled synthetic recovery case, never the real-field observations.
"""

from hashlib import sha256
import json

import numpy as np
import pandas as pd
import pygimli as pg
from pygimli.physics.ves import VESModelling
from scipy.stats import chi2

from field_case_support import verify_case


SPACING = np.array([0, 8, 14, 18, 20, 22, 24, 26, 28, 30, 34, 40, 48], dtype=float)
RHO = "Rho(Ohm*m)"
REPEATABILITY = "St.Dev.(%)"


def load_survey(directory=None):
    directory, provenance = verify_case("ert_survey", directory)
    observations = pd.read_csv(directory / "Resistivity_data.csv.gz")
    positions = pd.read_csv(directory / "Electrodes_Positions.csv.gz")
    if len(observations) != 164724 or len(positions) != 6734:
        raise ValueError("Original survey row counts changed")
    first = observations.iloc[:318].copy()
    electrodes = positions.loc[positions.num_shot == 1].copy()
    if (not np.array_equal(first.meas_num, np.arange(1, 319))
            or not np.array_equal(electrodes.iloc[:, 2], np.arange(1, 14))):
        raise ValueError("First-station acquisition/electrode identity is inconsistent")
    if first.iloc[:, :10].isna().any().any():
        raise ValueError("Do not replace missing original ERT measurements")
    return first, electrodes, provenance


def distances(rows):
    ids = rows[["A", "B", "M", "N"]].to_numpy(dtype=int) - 1
    if np.any((ids < 0) | (ids >= len(SPACING))):
        raise ValueError("Electrode ID outside the selected first station")
    a, b, m, n = SPACING[ids].T
    result = np.stack((abs(a - m), abs(a - n), abs(b - m), abs(b - n)))
    if np.any(result == 0) or np.any(a == b) or np.any(m == n):
        raise ValueError("Current/potential electrode pairs must be distinct")
    return result


def geometric_factors(rows):
    am, an, bm, bn = distances(rows)
    return 2 * np.pi / (1 / am - 1 / an - 1 / bm + 1 / bn)


def observed_container(rows):
    """Keep signed transfer resistance and 0-based IDs in actual pyGIMLi data."""
    container = pg.DataContainerERT()
    for x in SPACING:
        container.createSensor([float(x), 0.0, 0.0])
    for i, (a, b, m, n) in enumerate(rows[["A", "B", "M", "N"]].to_numpy(dtype=int) - 1):
        container.createFourPointData(i, int(a), int(b), int(m), int(n))
    container["rhoa"] = rows[RHO].to_numpy()
    container["r"] = rows.iloc[:, 8].to_numpy() / rows.iloc[:, 9].to_numpy()
    return container


def image_series_response(rows, thickness, rho_top, rho_bottom, terms=80):
    """Independent flat two-layer image-source solution for 3D point electrodes.

    The geometric series converges for positive finite resistivities. The fixed
    validation contrast gives reflection coefficient 0.5; 80/160-term agreement
    is checked separately, so truncation cannot masquerade as solver accuracy.
    """
    if min(thickness, rho_top, rho_bottom) <= 0:
        raise ValueError("Thickness and resistivities must be positive")
    separation = distances(rows)
    reflection = (rho_bottom - rho_top) / (rho_bottom + rho_top)
    order = np.arange(1, terms + 1)
    green = 1 / separation + 2 * np.sum(
        reflection ** order / np.sqrt(separation[..., None] ** 2
                                       + (2 * thickness * order) ** 2), axis=-1)
    signs = np.array([1, -1, -1, 1])
    return rho_top * (signs @ green) / (signs @ (1 / separation))


def make_forward(rows):
    am, an, bm, bn = distances(rows)
    return VESModelling(am=am, an=an, bm=bm, bn=bn, nLayers=2)


def fit_layers(rows, values=None, log_sigma=None, start=(5.0, 150.0, 50.0)):
    values = rows[RHO].to_numpy(dtype=float) if values is None else np.asarray(values)
    if log_sigma is None:
        # Repeated-stack SD is incomplete and sometimes rounds to zero. Declare
        # an additional 3% log-scale term; do not present it as measured accuracy.
        log_sigma = np.hypot(rows[REPEATABILITY].to_numpy(dtype=float) / 100.0, 0.03)
    log_sigma = np.asarray(log_sigma, dtype=float)
    if (len(rows) <= 3 or values.shape != (len(rows),) or log_sigma.shape != values.shape
            or not np.isfinite(values).all() or not np.isfinite(log_sigma).all()
            or np.any(values <= 0) or np.any(log_sigma <= 0)):
        raise ValueError("Log-domain inversion requires positive finite data and uncertainty")
    forward = make_forward(rows)
    inversion = pg.Inversion(fop=forward, verbose=False)
    inversion.dataTrans = pg.trans.TransLog()
    inversion.modelTrans = pg.trans.TransLog()
    model = np.asarray(inversion.run(values, errorVals=log_sigma, startModel=list(start),
                                     lam=0, maxIter=20, verbose=False))
    prediction = np.asarray(inversion.response)
    if not np.isfinite(model).all() or np.any(model <= 0):
        raise ValueError("Invalid recovered two-layer model")
    if (prediction.shape != values.shape or not np.isfinite(prediction).all()
            or np.any(prediction <= 0)):
        raise ValueError("Invalid positive apparent-resistivity prediction")
    statistic = float(np.sum(((np.log(prediction) - np.log(values)) / log_sigma) ** 2))
    return {"model": model, "predicted": prediction, "log_sigma": log_sigma,
            "chi_square": statistic, "degrees_of_freedom": len(rows) - 3,
            "library_chi_square_per_datum": float(inversion.chi2())}


def reciprocal_groups(rows):
    """Same group for pair reversals and reciprocal current/potential pairs."""
    groups = []
    for a, b, m, n in rows[["A", "B", "M", "N"]].to_numpy(dtype=int):
        pairs = sorted((tuple(sorted((int(a), int(b)))), tuple(sorted((int(m), int(n))))))
        groups.append("|".join(str(v) for pair in pairs for v in pair))
    return np.asarray(groups)


def ert_results():
    original, positions, _ = load_survey()
    positive = original[RHO].to_numpy() > 0
    rows = original.loc[positive].copy()
    fit = fit_layers(rows)
    groups = reciprocal_groups(rows)
    test = np.array([sha256(group.encode("ascii")).digest()[0] % 5 == 0 for group in groups])
    train = ~test
    holdout_fit = fit_layers(rows.loc[train])
    predicted = np.asarray(make_forward(rows.loc[test]).response(holdout_fit["model"]))
    y = rows[RHO].to_numpy()
    sigma = fit["log_sigma"]
    baseline = float(np.average(np.log(y[train]), weights=sigma[train] ** -2))
    # Coordinates are retained for provenance. The diagnostic uses instrument
    # nominal distances, not an invented zero-elevation georeferenced surface.
    xy = positions.iloc[:, 3:5].to_numpy(dtype=float)
    surveyed_span = float(np.linalg.norm(xy[-1] - xy[0]))
    report = {
        "station": 1, "original_measurements": len(original),
        "nonpositive_rhoa_excluded_from_log_fit": int((~positive).sum()),
        "negative_voltages_retained": int((rows.iloc[:, 8] < 0).sum()),
        "zero_reported_repeatability_values": int((rows[REPEATABILITY] == 0).sum()),
        "model_h_m_rho_top_ohm_m_rho_bottom_ohm_m": fit["model"].tolist(),
        "chi_square": fit["chi_square"], "degrees_of_freedom": fit["degrees_of_freedom"],
        "critical_99": float(chi2.ppf(0.99, fit["degrees_of_freedom"])),
        "conditional_layered_model_rejected": bool(fit["chi_square"]
            > chi2.ppf(0.99, fit["degrees_of_freedom"])),
        "holdout_measurements": int(test.sum()),
        "holdout_log_rmse": float(np.sqrt(np.mean((np.log(predicted) - np.log(y[test])) ** 2))),
        "training_log_mean_baseline_holdout_rmse": float(np.sqrt(np.mean(
            (baseline - np.log(y[test])) ** 2))),
        "surveyed_endpoint_span_m": surveyed_span, "nominal_endpoint_span_m": 48.0,
        "ground_truth": None,
        "scope": "Two-layer, flat, isotropic diagnostic with a declared log-error budget. "
                 "Quadrupole holdout is not an independent survey or a field recovery test.",
    }
    return report, {"original": original, "rows": rows, "fit": fit, "groups": groups,
                    "train": train, "test": test, "holdout_fit": holdout_fit,
                    "holdout_prediction": predicted}


if __name__ == "__main__":
    print(json.dumps(ert_results()[0], indent=2))
