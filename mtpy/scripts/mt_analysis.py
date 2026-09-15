#!/usr/bin/env python3
"""Direct-impedance EDI -> checked MTpy-v2 response -> CSV and provenance.

Requires caller-confirmed mV/km/nT, exp(+i omega t) and north/east/down.
HEAD UNITS may describe distances; it does not prove impedance units.
Spectra-only and rho/phase-only files require another reader route.
"""

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd

COMPONENTS = ("xx", "xy", "yx", "yy")


def source_blocks(filepath):
    """Preserve EMPTY/absent errors before mt-metadata substitutes zeros."""
    contents = Path(filepath).read_text(encoding="utf-8-sig")
    match = re.search(r"\bEMPTY\s*=\s*([\d.eE+\-]+)", contents, re.I)
    empty = float(match[1]) if match else 1e32
    wanted = {"FREQ", "ZROT"} | {
        "Z" + c.upper() + suffix for c in COMPONENTS
        for suffix in ("R", "I", ".VAR")}
    blocks, key = {}, None
    for line in contents.splitlines():
        line = line.strip()
        if not line or line.startswith(">!"):
            continue
        if line.startswith(">"):
            candidate = line[1:].strip().split()[0].upper()
            key = candidate if candidate in wanted else None
            if key:
                if key in blocks:
                    raise ValueError(f"Duplicate EDI block: {key}")
                blocks[key] = []
        elif key:
            for token in line.split("!", 1)[0].split():
                try:
                    value = float(token.replace("D", "E").replace("d", "e"))
                except ValueError:
                    value = np.nan
                blocks[key].append(np.nan if value == empty else value)
    if "FREQ" not in blocks or not any(k.endswith("R") for k in blocks):
        raise ValueError("Expected direct-impedance EDI with FREQ and Z blocks")
    frequency = np.asarray(blocks["FREQ"])
    if (not frequency.size or not np.all(np.isfinite(frequency) & (frequency > 0))
            or np.unique(frequency).size != frequency.size):
        raise ValueError("Frequencies must be positive, finite and unique")
    order = np.argsort(frequency)[::-1]
    for key, values in blocks.items():
        if len(values) != len(frequency):
            raise ValueError(f"EDI block {key} has a different sample count")
        blocks[key] = np.asarray(values)[order]
    return blocks


def prepare(filepath, *, impedance_units, sign_convention, rotation_deg=0.0,
            relative_error_limit=0.5):
    """Read real MTpy-v2 data and flag every tensor value without deleting rows."""
    from mtpy import MT
    if impedance_units != "mt" or sign_convention != "+":
        raise ValueError("This route requires confirmed mV/km/nT, exp(+i wt), NED")
    if not np.isfinite(rotation_deg):
        raise ValueError("Rotation must be finite")
    if not np.isfinite(relative_error_limit) or relative_error_limit <= 0:
        raise ValueError("Relative-error limit must be positive and finite")
    blocks = source_blocks(filepath)
    mt = MT(filepath, impedance_units="mt")
    mt.read(get_elevation=False)
    if mt.coordinate_reference_frame != "NED" or not mt.has_impedance():
        raise ValueError("Expected impedance with the declared NED convention")
    np.testing.assert_allclose(mt.frequency, blocks["FREQ"], rtol=1e-12)
    source_rotation = np.asarray(mt.rotation_angle).copy()
    size = len(mt.frequency)
    real = np.full((size, 2, 2), np.nan)
    imag, variance = real.copy(), real.copy()
    for index, component in enumerate(COMPONENTS):
        i, j = divmod(index, 2)
        for suffix, destination in (("R", real), ("I", imag), (".VAR", variance)):
            key = "Z" + component.upper() + suffix
            if key in blocks:
                destination[:, i, j] = blocks[key]
    present = np.isfinite(real) & np.isfinite(imag)
    known_error = np.isfinite(variance) & (variance >= 0)
    sigma = np.sqrt(np.where(known_error, variance, np.nan))
    z_object = mt.Z
    np.testing.assert_allclose(z_object.z[present], (real + 1j*imag)[present],
                               rtol=1e-12, atol=1e-12)
    if known_error.any():
        reader_sigma = (np.zeros_like(variance) if z_object.z_error is None
                        else z_object.z_error)
        np.testing.assert_allclose(reader_sigma[known_error], sigma[known_error],
                                   rtol=1e-12, atol=1e-12)
    if rotation_deg:
        if not np.all(present & known_error):
            raise ValueError("Rotation requires a complete tensor with known variances")
        mt.rotate(rotation_deg, inplace=True)
        z_object = mt.Z
        real, imag = z_object.z.real, z_object.z.imag
        sigma = (np.zeros_like(variance) if z_object.z_error is None else z_object.z_error)
    elif not np.all(present & known_error):
        # Restore masks in the object used for plotting as well as the CSV.
        # A missing real or imaginary part invalidates that complex component.
        mt.impedance = np.where(present, real + 1j*imag, np.nan + 1j*np.nan)
        mt.impedance_error = sigma
        z_object = mt.Z
    magnitude = np.hypot(real, imag)
    with np.errstate(divide="ignore", invalid="ignore"):
        relative = sigma / magnitude
    valid = present & (magnitude > 0)
    good = valid & known_error & (relative <= relative_error_limit)
    rho, phase = z_object.resistivity, z_object.phase
    table = pd.DataFrame({
        "frequency_hz": np.repeat(mt.frequency, 4),
        "period_s": np.repeat(1/mt.frequency, 4),
        "component": np.tile(COMPONENTS, size),
        "z_real_mV_per_km_per_nT": real.ravel(),
        "z_imag_mV_per_km_per_nT": imag.ravel(),
        "z_sigma_mV_per_km_per_nT": sigma.ravel(),
        "impedance_present": present.ravel(),
        "variance_known": known_error.ravel(),
        "relative_error": relative.ravel(),
        "qc_pass": good.ravel(),
        "rho_ohm_m": np.where(valid, rho, np.nan).ravel(),
        "phase_deg": np.where(valid, phase, np.nan).ravel(),
    })
    report = {
        "source_sha256": hashlib.sha256(Path(filepath).read_bytes()).hexdigest(),
        "source_filename": Path(filepath).name, "station": mt.station,
        "latitude_deg": mt.latitude, "longitude_deg": mt.longitude,
        "elevation_m": mt.elevation,
        "horizontal_crs_reader_value": mt.datum_crs.to_string(),
        "vertical_datum": "not established by this helper",
        "impedance_units": "mV/km/nT", "apparent_resistivity_units": "ohm m",
        "sign_convention": "exp(+i omega t)", "coordinate_frame": "NED",
        "convention_evidence": "caller-confirmed; original EDI retained",
        "source_rotation_deg": source_rotation.tolist(),
        "additional_clockwise_rotation_deg": float(rotation_deg),
        "output_rotation_deg": np.asarray(mt.rotation_angle).tolist(),
        "rotation_error_model": "library marginal errors, without full covariance",
        "n_frequencies": size, "n_tensor_values": len(table),
        "qc_pass_count": int(good.sum()),
        "missing_impedance_count": int((~present).sum()),
        "unknown_variance_count": int((~known_error).sum()),
        "relative_error_limit": relative_error_limit,
        "filter_action": "flags only; retain every frequency and tensor component",
        "interpretation": "QC only; no inversion or dimensionality certification",
        "versions": {n: importlib.metadata.version(n) for n in
                     ("mtpy-v2", "mt-metadata", "numpy", "pandas")},
    }
    return mt, table, report


def run_workflow(filepath, output_dir, *, impedance_units, sign_convention,
                 rotation_deg=0.0, relative_error_limit=0.5, plot=False):
    """Export and reopen CSV plus metadata; existing outputs are never replaced."""
    mt, table, report = prepare(
        filepath, impedance_units=impedance_units, sign_convention=sign_convention,
        rotation_deg=rotation_deg, relative_error_limit=relative_error_limit)
    directory = Path(output_dir)
    stem = Path(filepath).stem
    csv_path = directory / f"{stem}_qc.csv"
    json_path = directory / f"{stem}_metadata.json"
    figure_path = directory / f"{stem}_response.png"
    paths = [csv_path, json_path] + ([figure_path] if plot else [])
    if any(path.exists() for path in paths):
        raise FileExistsError("Output exists; choose a fresh directory")
    directory.mkdir(parents=True, exist_ok=True)
    table.to_csv(csv_path, index=False, float_format="%.17g")
    reopened = pd.read_csv(csv_path, float_precision="round_trip")
    pd.testing.assert_frame_equal(reopened, table, check_exact=False, rtol=1e-13)
    report["csv_sha256"] = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    if plot:
        import matplotlib.pyplot as plt
        response = mt.plot_mt_response(show_plot=False)
        response.plot()
        response.fig.savefig(figure_path, dpi=150)
        plt.close(response.fig)
    json_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    if json.loads(json_path.read_text())["source_sha256"] != report["source_sha256"]:
        raise RuntimeError("Metadata readback failed")
    return report, csv_path, json_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="Direct-impedance EDI file")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--impedance-units", choices=["mt"], required=True)
    parser.add_argument("--sign-convention", choices=["+"], required=True)
    parser.add_argument("--rotation-deg", type=float, default=0.0,
                        help="Additional clockwise angle, not absolute strike")
    parser.add_argument("--relative-error-limit", type=float, default=0.5)
    parser.add_argument("--plot", action="store_true")
    args = parser.parse_args()
    try:
        report, csv_path, json_path = run_workflow(
            args.path, args.output_dir, impedance_units=args.impedance_units,
            sign_convention=args.sign_convention, rotation_deg=args.rotation_deg,
            relative_error_limit=args.relative_error_limit, plot=args.plot)
    except (ValueError, OSError, AssertionError) as error:
        parser.exit(1, f"MT workflow failed: {error}\n")
    print(f"{report['station']}: {report['n_frequencies']} frequencies; "
          f"{report['qc_pass_count']}/{report['n_tensor_values']} values pass QC")
    print(csv_path)
    print(json_path)


if __name__ == "__main__":
    main()
