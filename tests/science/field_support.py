"""Offline provenance checks and a deliberately limited GNSS trend diagnostic.

Run this file with the modelling environment to print the field-data report.
This is a numerical validation example, not a regional deformation solution.
"""

from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import solve
from scipy.stats import chi2, norm
import verde as vd


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/field/alps_gps"
VALUE = "velocity_up_mmyr"
ERROR = "velocity_up_error_mmyr"


def verify_files(directory=FIXTURE):
    """Check every vendored upstream byte against the pinned provenance record."""
    directory = Path(directory)
    manifest = json.loads((directory / "provenance.json").read_text(encoding="utf-8"))
    for name, record in manifest["files"].items():
        content = (directory / name).read_bytes()
        if len(content) != record["bytes"] or sha256(content).hexdigest() != record["sha256"]:
            raise ValueError(f"Field-data integrity check failed: {name}")
    revision = (directory / "upstream-revision.txt").read_text().strip()
    if revision != manifest["curation"]["git_revision"]:
        raise ValueError("Upstream revision does not match provenance.json")
    return manifest


def load_field_data(directory=FIXTURE):
    """Load all 186 published stations; reject missing values instead of filling."""
    manifest = verify_files(directory)
    data = pd.read_csv(Path(directory) / "alps-gps-velocity.csv.xz", keep_default_na=False)
    if list(data.columns) != list(manifest["columns"]):
        raise ValueError("Unexpected field-data columns or column order")
    if len(data) != manifest["station_count"] or not data.station_id.is_unique:
        raise ValueError("Missing or duplicate station IDs")
    values = data.drop(columns="station_id").to_numpy(dtype=float)
    errors = data.filter(like="_error_").to_numpy(dtype=float)
    if not np.isfinite(values).all() or not (errors > 0).all():
        raise ValueError("Field observations must be finite with positive reported errors")
    return data


def _first_solution_records(path):
    """Read the first station solution in the original NEH table, before its notes."""
    records = {}
    in_table = False
    for line in path.read_text(encoding="latin-1").splitlines():
        if line.startswith("STATION NAME"):
            in_table = True
            continue
        if not in_table or not line.strip():
            continue
        if line.startswith("*---"):
            break
        fields = line.split()
        # Some stations have no DOMES identifier (the second text column).
        if len(fields) not in (11, 12):
            raise ValueError(f"Unexpected original station row: {line}")
        start = 2 if len(fields) == 12 else 1
        records.setdefault(fields[0], [float(v) for v in fields[start:start + 6]])
    return records


def _horizontal_records(directory):
    in_table = False
    for line in (directory / "ALPS2017_REP.VEL").read_text(encoding="latin-1").splitlines():
        if line.startswith("Column 7:"):
            in_table = True
            continue
        if not in_table or not line.strip():
            continue
        fields = line.split()
        if len(fields) != 7:
            raise ValueError(f"Unexpected original horizontal row: {line}")
        yield fields


def source_coordinate_disagreements(directory=FIXTURE):
    """Report source differences greater than one REP coordinate reporting unit.

    This is a conservative discrepancy screen, not a derived error tolerance or
    evidence of a coordinate transformation. Neither source is silently changed.
    """
    directory = Path(directory)
    positions = _first_solution_records(directory / "ALPS2017_NEH.CRD")
    discrepancies = {}
    for fields in _horizontal_records(directory):
        station = {"CH1Z": "CHIZ", "IE1G": "IENG"}.get(fields[0], fields[0])
        lat, _, lon, *_ = positions[station]
        lon = lon - 360 if lon > 300 else lon
        delta = max(abs(lon - float(fields[1])), abs(lat - float(fields[2])))
        if delta > 0.0001:
            discrepancies[station] = {"max_coordinate_difference_degree": delta}
    return discrepancies


def reconstruct_published_table(directory=FIXTURE):
    """Independently join original tables using the documented upstream choices.

    Reproduce table values, not compressor-dependent CSV/XZ bytes. Raw source
    files remain unchanged. Horizontal and vertical reference frames are distinct.
    """
    directory = Path(directory)
    positions = _first_solution_records(directory / "ALPS2017_NEH.CRD")
    vertical = _first_solution_records(directory / "ALPS2017_NEH.VEL")
    rows = []
    for fields in _horizontal_records(directory):
        station = {"CH1Z": "CHIZ", "IE1G": "IENG"}.get(fields[0], fields[0])
        lon_rep, lat_rep, east, north, east_error, north_error = map(float, fields[1:])
        lat, lat_error, lon, lon_error, height, height_error = positions[station]
        lon = lon - 360 if lon > 300 else lon
        # Check the two upstream ID corrections using the REP coordinate precision.
        # Other source-coordinate disagreements are reported separately, not hidden.
        if fields[0] in ("CH1Z", "IE1G"):
            if abs(lon - lon_rep) > 0.00005 or abs(lat - lat_rep) > 0.00005:
                raise ValueError(f"Corrected station join failed: {station}")
        up, up_error = vertical[station][4:6]
        rows.append({
            "station_id": station, "longitude": lon, "latitude": lat,
            "height_m": height, "velocity_east_mmyr": east * 1000,
            "velocity_north_mmyr": north * 1000, VALUE: up * 1000,
            "longitude_error_m": lon_error, "latitude_error_m": lat_error,
            "height_error_m": height_error,
            "velocity_east_error_mmyr": east_error * 1000,
            "velocity_north_error_mmyr": north_error * 1000, ERROR: up_error * 1000,
        })
    decimals = {"longitude": 7, "latitude": 7, "height_m": 3,
                "longitude_error_m": 4, "latitude_error_m": 4, "height_error_m": 3}
    for column in rows[0]:
        if column.startswith("velocity_"):
            decimals[column] = 1
    return pd.DataFrame(rows).round(decimals)


def design_matrix(data):
    """Degrees are only polynomial predictors here, never metric distances/strain."""
    return np.column_stack((np.ones(len(data)), data.longitude.to_numpy() - 10,
                            data.latitude.to_numpy() - 46))


def fit_vertical_trend(data):
    """Fit a plane and propagate a conditional, independent reported-sigma model.

    Covariance below excludes model discrepancy, interstation correlations, and
    uncertainty in coordinates. Do not interpret it as total geological accuracy.
    """
    design = design_matrix(data)
    values = data[VALUE].to_numpy(dtype=float)
    sigma = data[ERROR].to_numpy(dtype=float)
    if (len(data) <= 3 or not np.isfinite(design).all()
            or not np.isfinite(values).all() or not np.isfinite(sigma).all()
            or not (sigma > 0).all()):
        raise ValueError("Need more than three finite observations with positive sigma")
    weighted_design = design / sigma[:, None]
    rank = int(np.linalg.matrix_rank(weighted_design))
    if rank != 3:
        raise ValueError("Stations do not constrain a full-rank planar trend")
    coordinates = (design[:, 1], design[:, 2])
    model = vd.Trend(degree=1).fit(coordinates, values, weights=sigma ** -2)
    predicted = model.predict(coordinates)
    # Independent linear-algebra uncertainty calculation: Verde supplies the fit.
    covariance = solve(weighted_design.T @ weighted_design, np.eye(3), assume_a="pos")
    statistic = float(np.sum(((values - predicted) / sigma) ** 2))
    degrees_of_freedom = len(data) - rank  # sigma is supplied, not fit from residuals
    critical = float(chi2.ppf(0.99, degrees_of_freedom))
    return {"model": model, "design": design, "predicted": predicted,
            "covariance": covariance, "chi_square": statistic,
            "degrees_of_freedom": degrees_of_freedom, "critical_99": critical,
            "noise_only_model_rejected": statistic > critical}


def longitude_strip_holdout(data):
    """Five fixed longitude strips; each station is predicted once without its strip.

    This is a spatially separated stress test, including edge extrapolation. It is
    not a guaranteed buffer between stations or a test of spatial independence.
    """
    fold = np.digitize(data.longitude.to_numpy(), [0.0, 5.0, 10.0, 15.0])
    predictions = np.full(len(data), np.nan)
    variances = np.full(len(data), np.nan)
    baseline = np.full(len(data), np.nan)
    fitted = []
    for group in np.unique(fold):
        train, test = fold != group, fold == group
        fit = fit_vertical_trend(data.loc[train])
        design = design_matrix(data.loc[test])
        predictions[test] = fit["model"].predict((design[:, 1], design[:, 2]))
        variances[test] = np.einsum("ij,jk,ik->i", design, fit["covariance"], design)
        baseline[test] = np.average(data.loc[train, VALUE],
                                    weights=data.loc[train, ERROR].to_numpy() ** -2)
        fitted.append({"group": int(group), "train": train, "test": test, "fit": fit})
    return {"fold": fold, "predicted": predictions, "mean_baseline": baseline,
            "conditional_prediction_variance": variances, "fits": fitted}


def field_report(directory=FIXTURE):
    data = load_field_data(directory)
    fit = fit_vertical_trend(data)
    holdout = longitude_strip_holdout(data)
    residual = data[VALUE].to_numpy() - holdout["predicted"]
    noise_sigma = np.sqrt(data[ERROR].to_numpy() ** 2
                          + holdout["conditional_prediction_variance"])
    return {
        "stations": len(data), "component": VALUE,
        "source_coordinate_disagreements": source_coordinate_disagreements(directory),
        "chi_square": fit["chi_square"], "degrees_of_freedom": fit["degrees_of_freedom"],
        "critical_99": fit["critical_99"],
        "noise_only_model_rejected": fit["noise_only_model_rejected"],
        "holdout_rmse_mmyr": float(np.sqrt(np.mean(residual ** 2))),
        "holdout_mean_baseline_rmse_mmyr": float(np.sqrt(np.mean(
            (data[VALUE].to_numpy() - holdout["mean_baseline"]) ** 2))),
        "conditional_95_interval_coverage": float(np.mean(abs(residual)
            <= norm.ppf(0.975) * noise_sigma)),
        "interpretation": "Plane plus independent reported noise is inadequate; "
                          "conditional intervals exclude model discrepancy.",
    }


if __name__ == "__main__":
    print(json.dumps(field_report(), indent=2))
