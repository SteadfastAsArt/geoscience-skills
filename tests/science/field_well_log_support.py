"""FDB-1 observed logs to LAS: preserve missingness, remarks and the depth axis."""

from io import StringIO
import json

import lasio
import numpy as np
import pandas as pd

from field_case_support import verify_case


DEPTH = "Depth sed [m]"
SONIC = "Sonic vel [km/s]"
REMARK = "Comment (Remark to sonic log)"
CURVES = {
    "CALX": ("CALI [mm] (Caliper X)", "MM"),
    "CALY": ("CALI [mm] (Caliper Y)", "MM"),
    "TEMP": ("t [°C]", "DEGC"),
    "NGR": ("NGR [API units]", "API"),
}


def load_well_table(directory=None):
    directory, metadata = verify_case("well_logs", directory)
    text = (directory / "FDB-1_wireline_original.tab").read_text(encoding="utf-8")
    table = pd.read_csv(StringIO(text.split("*/\n", 1)[1]), sep="\t", keep_default_na=False)
    table.insert(0, "source_row", np.arange(1, len(table) + 1))
    if set(table["H"]) != {"FDB-1"}:
        raise ValueError("Unexpected borehole identifier")
    return table, metadata


def depth_referenced_rows(table):
    # A temperature reading with no published depth cannot be placed by guessing
    # a regular sequence. Keep it in the raw source, but exclude it from LAS.
    result = table.loc[table[DEPTH] != ""].copy()
    result[DEPTH] = pd.to_numeric(result[DEPTH], errors="raise")
    depth = result[DEPTH].to_numpy(dtype=float)
    if not np.isfinite(depth).all() or not (np.diff(depth) > 0).all():
        raise ValueError("Depth must be finite, unique and strictly increasing")
    return result


def numeric_column(table, column):
    return pd.to_numeric(table[column].replace("", np.nan), errors="raise").to_numpy(dtype=float)


def export_observed_las(output, directory=None):
    table, _ = load_well_table(directory)
    selected = depth_referenced_rows(table)
    depth = selected[DEPTH].to_numpy(dtype=float)
    velocity = numeric_column(selected, SONIC) * 1000.0
    if np.any(velocity[np.isfinite(velocity)] <= 0):
        raise ValueError("Sonic velocity must be positive where present")
    slowness = 304800.0 / velocity  # exact 0.3048 m/ft and 1e6 us/s
    las = lasio.LASFile()
    las.well.WELL.value = "FDB-1"
    las.well.NULL.value = -999.25
    las.well.STEP.value = 0.0  # irregular: source depth gaps are retained
    las.well.LOC.value = "32.8062 N, 130.8601 E; source does not name CRS"
    las.other = ("Converted from real PANGAEA.933467 observations, CC BY 4.0.\n"
                 "Shibutani, Susumu; Lin, Weiren (2021). No gap filling.\n"
                 "Depth datum/TVD conversion unspecified; retain original depth axis.\n"
                 "SONIC_REMARK=1 means a source remark is present, not necessarily a bad reading.\n"
                 "SRC_ROW is the original one-based data row, excluding table headers.")
    las.append_curve("DEPT", depth, unit="M", descr="Published borehole depth")
    las.append_curve("SRC_ROW", selected.source_row.to_numpy(), unit="", descr="Original data row")
    for name, (column, unit) in CURVES.items():
        las.append_curve(name, numeric_column(selected, column), unit=unit, descr=column)
    las.append_curve("VP", velocity, unit="M/S", descr="Observed sonic velocity; source km/s converted")
    las.append_curve("DT", slowness, unit="US/FT", descr="Derived 304800 / VP; not an additional measurement")
    las.append_curve("SONIC_REMARK", (selected[REMARK] != "").to_numpy(dtype=int),
                     unit="", descr="Source sonic remark present")
    las.write(str(output), version=2.0, wrap=False, fmt="%.8f", STEP=0.0)
    return selected


def interval_diagnostic(table):
    selected = depth_referenced_rows(table)
    depth = selected[DEPTH].to_numpy(dtype=float)
    velocity = numeric_column(selected, SONIC) * 1000.0
    qualified = np.isfinite(velocity) & (velocity > 0) & (selected[REMARK].to_numpy() == "")
    increments = np.diff(depth)
    adjacent = qualified[:-1] & qualified[1:] & np.isclose(increments, 0.1, atol=1e-9, rtol=0)
    # Trapezoidal slowness integral over accepted pairs only. Never integrate
    # across missing depth/sonic values or bridge a remarked interval.
    left, right, dz = velocity[:-1][adjacent], velocity[1:][adjacent], increments[adjacent]
    travel_time = np.sum(dz * (1 / left + 1 / right) / 2)
    half_increment = 0.005  # 0.00001 km/s reporting increment / 2, in m/s
    lower = np.sum(dz * (1 / (left + half_increment) + 1 / (right + half_increment)) / 2)
    upper = np.sum(dz * (1 / (left - half_increment) + 1 / (right - half_increment)) / 2)

    # Every fifth source row is a candidate holdout, defined without its value.
    # Accept only samples bracketed by contiguous, unremarked observed neighbours.
    middle = np.arange(1, len(depth) - 1)
    holdout = middle[(selected.source_row.to_numpy()[middle] % 5 == 0)
                     & qualified[middle - 1] & qualified[middle] & qualified[middle + 1]
                     & np.isclose(depth[middle] - depth[middle - 1], 0.1, atol=1e-9, rtol=0)
                     & np.isclose(depth[middle + 1] - depth[middle], 0.1, atol=1e-9, rtol=0)]
    training = qualified.copy()
    training[holdout] = False
    prediction = np.interp(depth[holdout], depth[training], velocity[training])
    return {"source_rows": len(table), "las_rows": len(selected),
            "rows_without_depth": int((table[DEPTH] == "").sum()),
            "accepted_adjacent_intervals": int(adjacent.sum()),
            "covered_depth_m": float(dz.sum()), "covered_one_way_time_s": float(travel_time),
            "quantization_only_time_bounds_s": [float(lower), float(upper)],
            "holdout_count": len(holdout), "holdout_rmse_m_s": float(np.sqrt(np.mean(
                (velocity[holdout] - prediction) ** 2))),
            "measurement_uncertainty": None,
            "depth": depth, "velocity": velocity, "qualified": qualified,
            "adjacent": adjacent, "holdout": holdout, "training": training,
            "prediction": prediction}


def well_report():
    report = interval_diagnostic(load_well_table()[0])
    return {key: value for key, value in report.items() if not isinstance(value, np.ndarray)}


if __name__ == "__main__":
    print(json.dumps(well_report(), indent=2))
