#!/usr/bin/env python3
"""Offline GHCN daily-TMAX case: QC, short reference, spatial holdout and export.

This is a fixed, documented 2018–2020 case, not a general climate-normal product.
Input dates label observing days, not known UTC intervals. No download occurs.
"""

import argparse
from hashlib import sha256
import gzip
from importlib.metadata import version
from io import StringIO
import json
from pathlib import Path

import cftime
import numpy as np
import pandas as pd
from pyproj import CRS, Transformer
from scipy.spatial import Delaunay
import verde as vd
import xarray as xr


REFERENCE = (2018, 2019)
EVALUATION_YEAR = 2020
MIN_COVERAGE = 0.9
SPATIAL_BOUNDARIES = (-77.0, -74.0)
EARTH_RADIUS_M = 6371008.8
WORKING_CRS = CRS.from_proj4("+proj=aeqd +lat_0=41.5 +lon_0=-75 +datum=WGS84 +units=m")
PROJECT = Transformer.from_crs("EPSG:4326", WORKING_CRS, always_xy=True)


def read_verified_source(source, provenance):
    source, provenance = Path(source), Path(provenance)
    metadata = json.loads(provenance.read_text(encoding="utf-8"))
    if metadata["query"].get("units") != "metric" or metadata["query"].get("dataTypes") != "TMAX":
        raise ValueError("This case requires an explicitly metric TMAX query")
    item = metadata["files"][source.name]
    content = source.read_bytes()
    if len(content) != item["bytes"] or sha256(content).hexdigest() != item["sha256"]:
        raise ValueError("Compressed source integrity check failed")
    original = gzip.decompress(content)
    if (len(original) != item["uncompressed_bytes"]
            or sha256(original).hexdigest() != item["uncompressed_sha256"]):
        raise ValueError("Original CSV integrity check failed")
    table = pd.read_csv(StringIO(original.decode("utf-8")), keep_default_na=False,
                        dtype={"STATION": str, "TMAX_ATTRIBUTES": str})
    if set(table.STATION) != set(metadata["station_ids"]):
        raise ValueError("Station selection differs from the recorded query")
    return table, metadata


def prepare_daily(table):
    """Retain raw converted values; mask missing/failed-QC values in analysis."""
    table = table.copy()
    required = {"STATION", "NAME", "LATITUDE", "LONGITUDE", "ELEVATION",
                "DATE", "TMAX", "TMAX_ATTRIBUTES"}
    if not required.issubset(table.columns):
        raise ValueError("Required GHCN metric-TMAX columns are missing")
    table["DATE"] = pd.to_datetime(table.DATE, format="%Y-%m-%d", errors="raise")
    if table.duplicated(["STATION", "DATE"]).any():
        raise ValueError("Duplicate station/date observations")
    dates = pd.date_range("2018-01-01", "2020-12-31", freq="D")
    if not table.DATE.isin(dates).all():
        raise ValueError("Date outside the documented observation window")
    stations = sorted(table.STATION.unique())
    for column in ["NAME", "LATITUDE", "LONGITUDE", "ELEVATION"]:
        if (table.groupby("STATION")[column].nunique(dropna=False) != 1).any():
            raise ValueError(f"Changing station metadata requires explicit review: {column}")
    location = table.groupby("STATION").first().loc[stations]
    latitude, longitude = location.LATITUDE.to_numpy(float), location.LONGITUDE.to_numpy(float)
    if (not np.isfinite(latitude).all() or not np.isfinite(longitude).all()
            or np.any(abs(latitude) > 90) or np.any(abs(longitude) > 180)):
        raise ValueError("Invalid geographic station coordinates")
    parsed = table.TMAX_ATTRIBUTES.str.split(",")
    absent = table.TMAX.isna() | (table.TMAX == "")
    absent_attributes = (table.TMAX_ATTRIBUTES == "") & absent
    if not (parsed.map(lambda value: len(value) in (3, 4)) | absent_attributes).all():
        raise ValueError("Malformed GHCN measurement/quality/source attributes")
    table["quality"] = parsed.map(lambda value: value[1] if len(value) > 1 else "")
    # API requested metric units: these are degrees C, not raw .dly tenths of C.
    table["raw_kelvin"] = pd.to_numeric(table.TMAX.replace("", np.nan), errors="raise") + 273.15
    if np.isinf(table.raw_kelvin.to_numpy(float)).any():
        raise ValueError("Infinite temperature is not a missing observation")
    index = pd.MultiIndex.from_product([dates, stations], names=["DATE", "STATION"])
    table = table.set_index(["DATE", "STATION"]).reindex(index)
    shape = (len(dates), len(stations))
    raw = table.raw_kelvin.to_numpy(float).reshape(shape)
    quality = table.quality.fillna("").to_numpy(str).reshape(shape)
    attributes = table.TMAX_ATTRIBUTES.fillna("").to_numpy(str).reshape(shape)
    qc = np.zeros(shape, dtype=np.int8)
    qc[~np.isfinite(raw)] = 1
    qc[(quality != "") & np.isfinite(raw)] = 2
    data = xr.Dataset(
        {"raw_tmax": (("time", "station"), raw),
         "tmax": (("time", "station"), np.where(qc == 0, raw, np.nan)),
         "qc_status": (("time", "station"), qc),
         "source_attributes": (("time", "station"), attributes),
         "station_name": ("station", location.NAME.to_numpy(str)),
         "station_latitude": ("station", latitude),
         "station_longitude": ("station", longitude),
         "station_elevation": ("station", location.ELEVATION.to_numpy(float))},
        coords={"time": xr.date_range("2018-01-01", "2020-12-31", freq="D",
                                       use_cftime=True, calendar="proleptic_gregorian"),
                "station": stations})
    for name in ["tmax", "raw_tmax"]:
        data[name].attrs = {"units": "K", "long_name": "Daily maximum air temperature",
                            "cell_methods": "time: maximum",
                            "comment": "Maximum over the source observing day; UTC bounds unknown"}
    data.qc_status.attrs = {"flag_values": np.array([0, 1, 2], dtype=np.int8),
                           "flag_meanings": "accepted missing failed_source_quality_check"}
    data.time.attrs["comment"] = "Observing-date labels; exact UTC intervals are not supplied"
    data.station_latitude.attrs["units"] = "degrees_north"
    data.station_longitude.attrs["units"] = "degrees_east"
    data.station_elevation.attrs.update(units="m", comment="Source vertical datum unspecified")
    return data


def monthly_summary(daily, min_coverage=MIN_COVERAGE):
    means = daily.tmax.resample(time="MS").mean(skipna=True)
    count = daily.tmax.resample(time="MS").count().astype(np.int32)
    expected = means.time.dt.days_in_month
    coverage = count / expected
    result = xr.Dataset({"monthly_tmax": means.where(coverage >= min_coverage),
                         "valid_days": count, "monthly_coverage": coverage,
                         "expected_days": expected})
    result.monthly_tmax.attrs = {"units": "K", "long_name": "Mean of observed daily maxima",
                                 "cell_methods": "time: mean"}
    result.valid_days.attrs["units"] = "day"
    result.monthly_coverage.attrs["units"] = "1"
    return result


def duration_weighted(values, days, expected_days, dim="time", min_coverage=MIN_COVERAGE):
    """Mean over represented valid calendar days; all-missing stays missing."""
    if (not 0 <= min_coverage <= 1 or not np.isfinite(days).all() or bool((days < 0).any())
            or not np.isfinite(expected_days).all() or bool((expected_days <= 0).any())):
        raise ValueError("Durations must be finite, nonnegative and have positive expected support")
    if bool((days > expected_days).any()):
        raise ValueError("Represented duration exceeds available calendar support")
    effective = days.where(values.notnull(), 0)
    support = effective.sum(dim)
    total = expected_days.sum(dim) if dim in expected_days.dims else expected_days
    coverage = support / total
    mean = (values.fillna(0) * effective).sum(dim) / support.where(support > 0)
    return mean.where(coverage >= min_coverage), coverage


def reference_climatology(monthly, stations):
    """Fit the twelve reference-month values using specified stations only."""
    baseline = monthly.sel(station=stations).where(
        (monthly.time.dt.year >= REFERENCE[0]) & (monthly.time.dt.year <= REFERENCE[1]), drop=True)
    means = []
    for month in range(1, 13):
        selected = baseline.where(baseline.time.dt.month == month, drop=True)
        # Equal station support, weighted by each station's represented days.
        value = selected.monthly_tmax
        weights = selected.valid_days.where(value.notnull(), 0)
        actual = weights.sum()
        expected = selected.expected_days.sum() * len(stations)
        if float(actual / expected) < MIN_COVERAGE:
            raise ValueError("Insufficient reference-period coverage")
        means.append(float((value.fillna(0) * weights).sum() / actual))
    return xr.DataArray(means, dims="climate_month", coords={"climate_month": np.arange(1, 13)},
                        attrs={"units": "K", "reference_period": "2018-01-01/2019-12-31",
                               "comment": "Short station-network reference, not a climate normal"})


def annual_anomaly(monthly, reference):
    target = monthly.where(monthly.time.dt.year == EVALUATION_YEAR, drop=True)
    baseline = reference.sel(climate_month=target.time.dt.month)
    anomaly = target.monthly_tmax - baseline
    annual, coverage = duration_weighted(anomaly, target.valid_days, target.expected_days)
    annual.attrs = {"units": "K", "long_name": "2020 mean daily-TMAX anomaly",
                    "reference_period": "2018-01-01/2019-12-31",
                    "comment": "Duration weighted against monthly station-network reference"}
    return annual, coverage


def station_local_anomalies(monthly):
    """Descriptive changes relative to each station's own past; not CV inputs."""
    reference = xr.concat([reference_climatology(monthly, [station])
                           for station in monthly.station.values], dim=monthly.station)
    anomaly, coverage = annual_anomaly(monthly, reference)
    anomaly.attrs["comment"] = "Each station's own short 2018–2019 reference; never used by spatial holdout"
    return reference, anomaly, coverage


def fit_spatial(coordinates, values):
    x, y = [np.asarray(value, dtype=float) for value in coordinates]
    values = np.asarray(values, dtype=float)
    if len(values) <= 3 or not np.isfinite(values).all():
        raise ValueError("Spatial fit needs at least four finite station values")
    if np.linalg.matrix_rank(np.column_stack([np.ones(len(x)), x, y])) != 3:
        raise ValueError("Station geometry cannot identify a planar trend")
    return vd.Trend(degree=1).fit((x, y), values)


def spatial_fold(monthly, longitude, latitude, test):
    """No value from a held-out station in any year enters fitted quantities."""
    test = np.asarray(test, dtype=bool)
    train = ~test
    if not test.any() or not train.any():
        raise ValueError("A spatial fold requires both training and held-out stations")
    reference = reference_climatology(monthly, monthly.station.values[train])
    values, coverage = annual_anomaly(monthly, reference)
    x, y = PROJECT.transform(longitude, latitude)
    model = fit_spatial((x[train], y[train]), values.values[train])
    prediction = model.predict((x[test], y[test]))
    constant = float(values.values[train].mean())
    return {"train": train, "test": test, "reference": reference.values,
            "coefficients": np.asarray(model.coef_), "prediction": prediction,
            "observed": values.values[test], "constant_prediction": constant,
            "coverage": coverage.values}


def spatial_holdout(monthly, longitude, latitude):
    groups = np.digitize(longitude, SPATIAL_BOUNDARIES)
    folds = [spatial_fold(monthly, longitude, latitude, groups == group)
             for group in sorted(set(groups))]
    residual = np.concatenate([fold["prediction"] - fold["observed"] for fold in folds])
    baseline = np.concatenate([fold["constant_prediction"] - fold["observed"] for fold in folds])
    report = {"longitude_boundaries_degree": list(SPATIAL_BOUNDARIES),
              "held_out_counts": [int(fold["test"].sum()) for fold in folds],
              "rmse_K": float(np.sqrt(np.mean(residual ** 2))),
              "training_mean_baseline_rmse_K": float(np.sqrt(np.mean(baseline ** 2))),
              "scope": "Unseen stations, including edge extrapolation; no buffer or independence claim"}
    return report, folds, groups


def spherical_cell_areas(latitude_bounds, longitude_bounds, radius=EARTH_RADIUS_M):
    """Exact rectangle areas on the declared sphere, not an ellipsoidal geoid."""
    lat, lon = np.asarray(latitude_bounds, float), np.asarray(longitude_bounds, float)
    if (lat.ndim != 2 or lon.ndim != 2 or lat.shape[1] != 2 or lon.shape[1] != 2
            or not np.isfinite(lat).all() or not np.isfinite(lon).all()
            or np.any(abs(lat) > 90) or np.any(lat[:, 1] <= lat[:, 0])
            or np.any(lon[:, 1] <= lon[:, 0]) or np.any(lon[:, 1] - lon[:, 0] > 360)
            or not np.isfinite(radius) or radius <= 0):
        raise ValueError("Invalid latitude/longitude bounds or spherical radius")
    return radius ** 2 * np.diff(np.sin(np.deg2rad(lat)), axis=1) * np.deg2rad(
        lon[:, 1] - lon[:, 0])[None, :]


def area_weighted(values, cell_area, support, min_coverage=MIN_COVERAGE):
    if np.any(~np.isfinite(cell_area)) or np.any(cell_area <= 0):
        raise ValueError("Cell areas must be positive and finite")
    fixed = cell_area.where(support, 0)
    total = fixed.sum()
    if float(total) <= 0:
        raise ValueError("The declared spatial support has no area")
    valid = fixed.where(values.notnull(), 0)
    covered = valid.sum()
    coverage = covered / total
    mean = (values.fillna(0) * valid).sum() / covered.where(covered > 0)
    return mean.where(coverage >= min_coverage), coverage


def prediction_grid(longitude, latitude, station_anomaly):
    x, y = PROJECT.transform(longitude, latitude)
    model = fit_spatial((x, y), station_anomaly)
    latitude_edges = np.arange(38.5, 44.5 + 0.25, 0.25)
    longitude_edges = np.arange(-80.5, -70.0 + 0.25, 0.25)
    lat_bounds = np.column_stack([latitude_edges[:-1], latitude_edges[1:]])
    lon_bounds = np.column_stack([longitude_edges[:-1], longitude_edges[1:]])
    lat, lon = lat_bounds.mean(axis=1), lon_bounds.mean(axis=1)
    xx, yy = np.meshgrid(lon, lat)
    grid_x, grid_y = PROJECT.transform(xx, yy)
    hull = Delaunay(np.column_stack([x, y]))
    supported = np.ones(xx.shape, dtype=bool)
    # Use the stricter all-corners criterion, not just centre membership. This
    # is a discrete support rule; it does not trace curved geographic cell edges.
    for lat_side in (0, 1):
        for lon_side in (0, 1):
            corner_lon, corner_lat = np.meshgrid(lon_bounds[:, lon_side], lat_bounds[:, lat_side])
            cx, cy = PROJECT.transform(corner_lon, corner_lat)
            supported &= hull.find_simplex(np.column_stack([cx.ravel(), cy.ravel()])).reshape(xx.shape) >= 0
    values = np.where(supported, model.predict((grid_x, grid_y)), np.nan)
    dataset = xr.Dataset(
        {"model_anomaly": (("latitude", "longitude"), values),
         "cell_area": (("latitude", "longitude"), spherical_cell_areas(lat_bounds, lon_bounds)),
         "spatial_support": (("latitude", "longitude"), supported.astype(np.int8)),
         "latitude_bounds": (("latitude", "bounds"), lat_bounds),
         "longitude_bounds": (("longitude", "bounds"), lon_bounds)},
        coords={"latitude": lat, "longitude": lon, "bounds": [0, 1]})
    dataset.model_anomaly.attrs = {"units": "K", "long_name": "Planar model estimate of annual daily-TMAX anomaly",
                                    "cell_measures": "area: cell_area", "grid_mapping": "crs",
                                    "comment": "Predictions at cell centres, not observed grid cells"}
    dataset.cell_area.attrs = {"units": "m2", "earth_radius_m": EARTH_RADIUS_M}
    dataset.latitude.attrs = {"units": "degrees_north", "bounds": "latitude_bounds"}
    dataset.longitude.attrs = {"units": "degrees_east", "bounds": "longitude_bounds"}
    dataset["crs"] = xr.DataArray(0, attrs={"grid_mapping_name": "latitude_longitude",
        "semi_major_axis": 6378137.0, "inverse_flattening": 298.257223563,
        "comment": "WGS84 working-datum assumption; source datum unverified"})
    dataset["fitting_crs"] = xr.DataArray(0, attrs=WORKING_CRS.to_cf())
    regional, coverage = area_weighted(dataset.model_anomaly, dataset.cell_area,
                                      dataset.spatial_support.astype(bool))
    dataset["regional_model_anomaly"] = regional
    dataset.regional_model_anomaly.attrs = {"units": "K", "cell_methods": "area: mean",
                                            "comment": "Cell-centre quadrature over supported model cells"}
    dataset["regional_area_coverage"] = coverage
    return dataset


def run_case(source, provenance, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("Use an empty output directory; existing results are preserved")
    table, metadata = read_verified_source(source, provenance)
    daily = prepare_daily(table)
    monthly = monthly_summary(daily)
    reference = reference_climatology(monthly, monthly.station.values)
    anomaly, annual_coverage = annual_anomaly(monthly, reference)
    local_reference, local_anomaly, _ = station_local_anomalies(monthly)
    longitude, latitude = daily.station_longitude.values, daily.station_latitude.values
    holdout, folds, groups = spatial_holdout(monthly, longitude, latitude)
    grid = prediction_grid(longitude, latitude, anomaly.values)
    product = xr.merge([daily.rename(time="observing_date"), monthly,
                       reference.to_dataset(name="reference_tmax"), grid], compat="no_conflicts")
    product["station_annual_anomaly"] = anomaly
    product["station_local_reference_tmax"] = local_reference
    product["station_local_annual_anomaly"] = local_anomaly
    product["annual_day_coverage"] = annual_coverage
    for name in ["tmax", "raw_tmax"]:
        product[name].attrs["cell_methods"] = "observing_date: maximum"
    product["spatial_holdout_group"] = ("station", groups.astype(np.int32))
    edges = xr.date_range("2018-01-01", "2021-01-01", freq="MS", use_cftime=True,
                          calendar="proleptic_gregorian")
    product["time_bounds"] = (("time", "bounds"), np.column_stack([edges[:-1], edges[1:]]))
    product.time.attrs = {"bounds": "time_bounds", "comment": "Nominal calendar-month bounds for observing dates"}
    product.attrs = {"title": "Observed daily-TMAX workflow and clearly labelled spatial diagnostic",
                     "Conventions": "CF-1.10", "source": metadata["dataset"]["doi"],
                     "source_csv_sha256": metadata["files"][Path(source).name]["uncompressed_sha256"],
                     "license": metadata["dataset"]["license"], "reference_period": "2018-01-01/2019-12-31",
                     "evaluation_year": EVALUATION_YEAR, "minimum_coverage": MIN_COVERAGE,
                     "observation_interval": "Nominal observing day; UTC timing not supplied",
                     "uncertainty": "Descriptive holdout errors; no calibrated predictive interval",
                     "working_coordinate_assumption": "WGS84; CSV source datum unspecified"}
    path = output / "climate-workflow.nc"
    encoding = {name: {"calendar": "proleptic_gregorian", "units": "days since 2018-01-01 00:00:00"}
                for name in ["time", "observing_date", "time_bounds"]}
    product.to_netcdf(path, engine="scipy", encoding=encoding)
    with xr.open_dataset(path, engine="scipy", decode_times=xr.coders.CFDatetimeCoder(use_cftime=True)) as reopened:
        xr.testing.assert_allclose(reopened, product)
    fold_records = [{"training_stations": daily.station.values[fold["train"]].tolist(),
                     "held_out_stations": daily.station.values[fold["test"]].tolist(),
                     "training_reference_monthly_K": fold["reference"].tolist(),
                     "predicted_K": fold["prediction"].tolist(),
                     "observed_network_reference_anomaly_K": fold["observed"].tolist(),
                     "training_mean_prediction_K": fold["constant_prediction"]} for fold in folds]
    report = {"source_rows": len(table), "station_count": daily.sizes["station"],
              "protocol_version": "1.0.0", "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
              "missing_station_days": int((daily.qc_status == 1).sum()),
              "quality_rejected_station_days": int((daily.qc_status == 2).sum()),
              "reference_years": list(REFERENCE), "evaluation_year": EVALUATION_YEAR,
              "station_anomaly_K": dict(zip(daily.station.values.tolist(), anomaly.values.tolist())),
              "station_local_reference_anomaly_K": dict(zip(daily.station.values.tolist(), local_anomaly.values.tolist())),
              "spatial_holdout": holdout, "supported_model_cells": int(grid.spatial_support.sum()),
              "spatial_folds": fold_records,
              "supported_area_m2": float(grid.cell_area.where(grid.spatial_support.astype(bool), 0).sum()),
              "regional_model_anomaly_K": float(grid.regional_model_anomaly),
              "regional_area_coverage": float(grid.regional_area_coverage),
              "output_sha256": sha256(path.read_bytes()).hexdigest(),
              "source_csv_sha256": product.attrs["source_csv_sha256"],
              "versions": {name: version(name) for name in ["numpy", "pandas", "scipy", "xarray", "cftime", "verde", "pyproj"]}}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return product, report, folds


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run_case(args.source, args.provenance, args.output)[1], indent=2))
