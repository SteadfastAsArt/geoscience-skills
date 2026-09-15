"""Real EDI -> MTpy-v2 -> response/QC/rotation/export and independent oracles."""

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd
from mtpy import MT

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/fixtures/workflows/near_surface/mt"
SCRIPT = ROOT / "mtpy/scripts/mt_analysis.py"
spec = importlib.util.spec_from_file_location("mt_workflow", SCRIPT)
workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workflow)
CONVENTIONS = {"impedance_units": "mt", "sign_convention": "+"}


def numbers(text, block):
    """Independent numeric extraction of the complete field fixture."""
    match = re.search(r"^>" + re.escape(block) + r"\s[^\n]*\n([^>]+)", text, re.M)
    return np.asarray([float(value) for value in match[1].split()])


def synthetic_edi(path, *, missing=False, omit_variance=False):
    """Serialize analytical tensors without the MTpy/mt-metadata writer."""
    frequency = np.array([10., 1., 0.1])
    z = np.empty((3, 2, 2), complex)
    z[:, 0, 1] = np.sqrt(5*frequency*100/2)*(1+1j)
    z[:, 1, 0] = -z[:, 0, 1]
    z[:, 0, 0] = 0.1*z[:, 0, 1]
    z[:, 1, 1] = -0.2*z[:, 0, 1]
    variance = (0.02*np.abs(z))**2
    text = """>HEAD
 DATAID=SYNTHETIC
 LAT=40
 LONG=-110
 ELEV=100
 DATUM=WGS84
 EMPTY=1.0E+32
 UNITS=millivolts_per_kilometer_per_nanotesla
>INFO
 Synthetic numerical benchmark; no field observations.
 transfer_function.sign_convention = +
>=DEFINEMEAS
 MAXCHAN=4
 MAXRUN=1
 MAXMEAS=4
 REFLAT=40
 REFLONG=-110
 REFELEV=100
 REFTYPE=CART
 UNITS=M
>HMEAS ID=1 CHTYPE=HX X=0 Y=0 AZM=0
>HMEAS ID=2 CHTYPE=HY X=0 Y=0 AZM=90
>EMEAS ID=3 CHTYPE=EX X=0 Y=0 X2=100 Y2=0
>EMEAS ID=4 CHTYPE=EY X=0 Y=0 X2=0 Y2=100
>=MTSECT
 SECTID=SYNTHETIC
 NFREQ=3
 HX=1
 HY=2
 EX=3
 EY=4
"""
    blocks = {"FREQ": frequency, "ZROT": np.zeros(3)}
    for index, component in enumerate(("XX", "XY", "YX", "YY")):
        i, j = divmod(index, 2)
        blocks[f"Z{component}R"] = z[:, i, j].real.copy()
        blocks[f"Z{component}I"] = z[:, i, j].imag.copy()
        if not omit_variance:
            blocks[f"Z{component}.VAR"] = variance[:, i, j]
    if missing:
        blocks["ZXYR"][0] = 1e32
    for key, values in blocks.items():
        text += f">{key} // 3\n" + " ".join(f"{v:.17g}" for v in values) + "\n"
    path.write_text(text + ">END\n")
    return frequency, z, variance


class MTWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = FIXTURE / "test.edi"
        cls.mt, cls.table, cls.report = workflow.prepare(cls.path, **CONVENTIONS)
        text = cls.path.read_text()
        cls.frequency = numbers(text, "FREQ")
        cls.z = np.empty((80, 2, 2), complex)
        cls.variance = np.empty((80, 2, 2))
        for index, component in enumerate(("XX", "XY", "YX", "YY")):
            i, j = divmod(index, 2)
            cls.z[:, i, j] = numbers(text, f"Z{component}R") + 1j*numbers(text, f"Z{component}I")
            cls.variance[:, i, j] = numbers(text, f"Z{component}.VAR")

    def test_source_bytes_license_units_station_and_coordinates(self):
        provenance = json.loads((FIXTURE / "provenance.json").read_text())
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), provenance["file_sha256"])
        self.assertEqual(hashlib.sha256((FIXTURE / "UPSTREAM-LICENSE.txt").read_bytes()).hexdigest(),
                         provenance["license_sha256"])
        self.assertEqual(self.report["station"], "14_IEB0537A")
        self.assertEqual(self.report["n_frequencies"], 80)
        self.assertEqual(self.report["impedance_units"], "mV/km/nT")
        self.assertAlmostEqual(self.mt.latitude, -(22 + 49/60 + 25.4/3600))
        self.assertAlmostEqual(self.mt.longitude, 139 + 17/60 + 40.9/3600)
        self.assertEqual(self.mt.elevation, 158)
        np.testing.assert_allclose(self.report["source_rotation_deg"], 5)

    def test_field_impedance_variances_and_derived_quantities_against_source(self):
        # Reader stores periods and reconstructs frequencies, introducing ULP rounding.
        np.testing.assert_allclose(self.mt.frequency, self.frequency, rtol=1e-14)
        np.testing.assert_allclose(self.mt.Z.z, self.z, rtol=1e-12)
        np.testing.assert_allclose(self.mt.Z.z_error**2, self.variance, rtol=1e-12)
        # mV/km/nT -> E/H ohm is mu0*1000; rho=|Z_ohm|²/(mu0*2*pi*f).
        mu0 = 4e-7*np.pi
        expected = np.abs(self.z*mu0*1000)**2/(mu0*2*np.pi*self.frequency[:, None, None])
        np.testing.assert_allclose(self.table.rho_ohm_m, expected.ravel(), rtol=1e-12)
        np.testing.assert_allclose(self.table.phase_deg, np.angle(self.z, deg=True).ravel())
        relative = np.sqrt(self.variance)/abs(self.z)
        np.testing.assert_array_equal(self.table.qc_pass, (relative <= 0.5).ravel())

    def test_clockwise_rotation_is_additive_and_matches_tensor_algebra(self):
        rotated, table, report = workflow.prepare(self.path, rotation_deg=30, **CONVENTIONS)
        theta = np.deg2rad(30)
        r = np.array([[np.cos(theta), np.sin(theta)], [-np.sin(theta), np.cos(theta)]])
        expected = r @ self.z @ r.T
        np.testing.assert_allclose(rotated.Z.z, expected, rtol=1e-11, atol=1e-12)
        np.testing.assert_allclose(np.linalg.det(rotated.Z.z), np.linalg.det(self.z), rtol=1e-10)
        np.testing.assert_allclose(report["output_rotation_deg"], 35)
        np.testing.assert_allclose(self.mt.Z.z, self.z)  # original remains intact

    def test_controlled_halfspace_and_variance_standard_deviation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"synthetic.edi"
            frequency, z, variance = synthetic_edi(path)
            mt, table, report = workflow.prepare(path, **CONVENTIONS)
            off_diagonal = table.component.isin(["xy", "yx"])
            np.testing.assert_allclose(table.loc[off_diagonal, "rho_ohm_m"], 100)
            np.testing.assert_allclose(table.loc[table.component == "xy", "phase_deg"], 45)
            np.testing.assert_allclose(table.loc[table.component == "yx", "phase_deg"], -135)
            np.testing.assert_allclose(mt.Z.z_error, np.sqrt(variance))
            self.assertTrue(table.qc_pass.all())

    def test_empty_impedance_and_absent_variance_do_not_become_valid_zeros(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"missing.edi"
            synthetic_edi(path, missing=True, omit_variance=True)
            mt, table, report = workflow.prepare(path, **CONVENTIONS)
            row = table[(table.frequency_hz == 10) & (table.component == "xy")].iloc[0]
            self.assertTrue(np.isnan(row.z_real_mV_per_km_per_nT))
            self.assertTrue(np.isnan(row.rho_ohm_m))
            self.assertFalse(row.impedance_present)
            self.assertFalse(table.variance_known.any())
            self.assertFalse(table.qc_pass.any())
            self.assertTrue(table.z_sigma_mV_per_km_per_nT.isna().all())
            self.assertTrue(np.isnan(mt.Z.z[0, 0, 1]))  # plot object retains mask too
            with self.assertRaisesRegex(ValueError, "complete tensor"):
                workflow.prepare(path, rotation_deg=30, **CONVENTIONS)
            _, csv, _ = workflow.run_workflow(path, Path(directory)/"export", **CONVENTIONS)
            self.assertEqual(pd.read_csv(csv).rho_ohm_m.isna().sum(), 1)

    def test_export_cli_plots_and_csv_metadata_readback(self):
        with tempfile.TemporaryDirectory() as directory:
            process = subprocess.run([sys.executable, str(SCRIPT), str(self.path),
                "--output-dir", directory, "--impedance-units", "mt",
                "--sign-convention", "+", "--plot"], capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            path = Path(directory)
            exported = pd.read_csv(path/"test_qc.csv", float_precision="round_trip")
            pd.testing.assert_frame_equal(exported, self.table, check_exact=False, rtol=1e-13)
            meta = json.loads((path/"test_metadata.json").read_text())
            self.assertEqual(meta["csv_sha256"], hashlib.sha256((path/"test_qc.csv").read_bytes()).hexdigest())
            self.assertEqual((path/"test_response.png").read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_native_edi_write_read_preserves_complete_sample_and_rotation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"roundtrip.edi"
            self.mt.write(fn=path)
            reread = MT(path)
            reread.read(get_elevation=False)
            np.testing.assert_allclose(reread.Z.z, self.z, rtol=1e-6)
            np.testing.assert_allclose(reread.Z.z_error**2, self.variance, rtol=2e-6)
            np.testing.assert_allclose(reread.rotation_angle, 5)
            self.assertEqual(reread.station, self.mt.station)

    def test_invalid_input_and_existing_output_fail_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"bad.edi"
            synthetic_edi(path)
            path.write_text(path.read_text().replace(">FREQ // 3\n10 1 ", ">FREQ // 3\n10 0 "))
            with self.assertRaisesRegex(ValueError, "positive"):
                workflow.prepare(path, **CONVENTIONS)
            process = subprocess.run([sys.executable, str(SCRIPT), str(path),
                "--output-dir", str(Path(directory)/"bad-out"),
                "--impedance-units", "mt", "--sign-convention", "+"],
                capture_output=True, text=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertFalse((Path(directory)/"bad-out").exists())
            existing = Path(directory)/"test_qc.csv"
            existing.write_text("keep user data\n")
            with self.assertRaises(FileExistsError):
                workflow.run_workflow(self.path, directory, **CONVENTIONS)
            self.assertEqual(existing.read_text(), "keep user data\n")


if __name__ == "__main__":
    unittest.main()
