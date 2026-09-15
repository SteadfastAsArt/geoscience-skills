#!/usr/bin/env python3
"""Solve a synthetic confined aquifer and verify its analytic head and flow."""

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import flopy
import numpy as np


def run(workspace, executable="mf6"):
    """Write a new input deck; require an actual, successful MODFLOW 6 run."""
    exe = shutil.which(str(executable))
    if exe is None:
        raise FileNotFoundError(f"MODFLOW 6 executable is unavailable: {executable}")
    version = subprocess.run([exe, "-v"], capture_output=True, text=True,
                             check=True, timeout=10).stdout.strip()
    workspace = Path(workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    if any(workspace.iterdir()):
        raise ValueError("Use an empty workspace to preserve existing model files")
    sim = flopy.mf6.MFSimulation(sim_name="confined", sim_ws=workspace, exe_name=exe)
    flopy.mf6.ModflowTdis(sim, time_units="DAYS", nper=1, perioddata=[(1, 1, 1)])
    flopy.mf6.ModflowIms(sim, outer_dvclose=1e-10, inner_dvclose=1e-10,
                       rcloserecord=1e-10)
    model = flopy.mf6.ModflowGwf(sim, modelname="confined", save_flows=True)
    flopy.mf6.ModflowGwfdis(model, length_units="METERS", nlay=1, nrow=1,
                          ncol=11, delr=10, delc=10, top=0, botm=-20)
    flopy.mf6.ModflowGwfic(model, strt=9.5)
    flopy.mf6.ModflowGwfnpf(model, icelltype=0, k=1, save_specific_discharge=True)
    flopy.mf6.ModflowGwfchd(model, stress_period_data=[((0, 0, 0), 10),
                                                    ((0, 0, 10), 9)])
    flopy.mf6.ModflowGwfoc(model, head_filerecord="confined.hds",
                         budget_filerecord="confined.cbc",
                         saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")])
    sim.write_simulation(silent=True)
    success, output = sim.run_simulation(silent=True, report=True)
    if not success:
        raise RuntimeError("MODFLOW 6 failed:\n" + "\n".join(output[-30:]))
    with closing(model.output.head()) as reader:
        heads = reader.get_data().reshape(-1)
    expected = np.linspace(10, 9, 11)
    np.testing.assert_allclose(heads, expected, rtol=0, atol=1e-7)
    if np.any(heads <= model.dis.top.array.ravel()):
        raise ValueError("The confined benchmark requires heads above the aquifer top")
    with closing(model.output.budget()) as reader:
        boundary_flow = reader.get_data(text="CHD")[0]["q"]
    np.testing.assert_allclose(np.sort(boundary_flow), [-2, 2], rtol=0, atol=1e-6)
    result = {"synthetic": True, "length_unit": "m", "time_unit": "day",
              "aquifer_top_m": 0.0, "aquifer_bottom_m": -20.0,
              "head_m": heads.tolist(), "boundary_flow_m3_day": boundary_flow.tolist(),
              "budget_net_m3_day": float(boundary_flow.sum()),
              "max_head_error_m": float(np.max(np.abs(heads - expected))),
              "flopy_version": flopy.__version__, "executable": exe,
              "modflow_version": version,
              "executable_sha256": hashlib.sha256(Path(exe).read_bytes()).hexdigest()}
    (workspace / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--exe", default="mf6")
    args = parser.parse_args()
    print(json.dumps(run(args.workspace, args.exe), indent=2))
