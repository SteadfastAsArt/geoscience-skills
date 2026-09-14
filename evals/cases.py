"""Small independent oracles; no scientific libraries or paid agents required.

Only task prompts and input files are staged for agents. This module and the
expected results stay outside the agent's filesystem namespace.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import random
import struct


TASKS = {"las-qc": "lasio", "segy-subset": "segyio",
         "formation-evaluation": "well-log-evaluation"}
TRACE_FIELDS = {
    "CDP": (20, "i"), "SourceGroupScalar": (70, "h"),
    "SourceX": (72, "i"), "SourceY": (76, "i"),
    "CoordinateUnits": (88, "h"), "DelayRecordingTime": (108, "h"),
    "TRACE_SAMPLE_COUNT": (114, "H"), "TRACE_SAMPLE_INTERVAL": (116, "H"),
    "INLINE_3D": (188, "i"), "CROSSLINE_3D": (192, "i"),
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_fixture(task: str, inputs: Path, seed: int = 20260914) -> dict:
    """Write only synthetic inputs, returning an oracle private to the runner."""
    inputs.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    if task == "las-qc":
        depths = [1200.0 + i * 0.5 for i in range(17)]
        depths[9] = depths[8]
        gr = [float(rng.randrange(25, 140)) for _ in depths]
        rho = [round(rng.uniform(2.1, 2.8), 4) for _ in depths]
        for i in (2, 11, 14):
            gr[i] = -999.25
        for i in (5, 11):
            rho[i] = -999.25
        header = """~Version Information
 VERS. 2.0 : CWLS LOG ASCII STANDARD
 WRAP. NO
~Well Information
 STRT.M 1200
 STOP.M 1208
 STEP.M 0.5
 NULL. -999.25
 WELL. SYNTHETIC-EVALUATION
~Curve Information
 DEPT.M : Depth
 GR.API : Gamma ray
 RHOB.G/CC : Bulk density
~ASCII
"""
        path = inputs / "well.las"
        path.write_text(header + "".join(
            f"{d:.2f} {g:.4f} {r:.4f}\n" for d, g, r in zip(depths, gr, rho)
        ), encoding="ascii")
        curves = {}
        for name, values, unit in (("GR", gr, "API"), ("RHOB", rho, "G/CC")):
            valid = [v for v in values if v != -999.25]
            curves[name] = dict(unit=unit, valid_count=len(valid),
                                null_count=len(values) - len(valid),
                                minimum=min(valid), maximum=max(valid),
                                mean=sum(valid) / len(valid))
        expected = dict(row_count=len(depths), depth=dict(
            unit="M", minimum=min(depths), maximum=max(depths),
            strictly_increasing=all(b > a for a, b in zip(depths, depths[1:])),
            duplicate_count=len(depths) - len(set(depths))), curves=curves)
    elif task == "formation-evaluation":
        path = inputs / "formation.las"
        parameters = dict(gr_sand_api=20.0, gr_shale_api=120.0,
                          matrix_density_g_cc=2.65, fluid_density_g_cc=1.0,
                          rw_ohm_m=0.05, archie_a=1.0, archie_m=2.0, archie_n=2.0)
        depths = [1500.0 + i * 0.5 for i in range(13)]
        gr = [25, 35, 40, -999.25, 50, 60, 70, 90, 110, 100, 35, 30, 25]
        rho = [round(rng.uniform(2.25, 2.55), 4) for _ in depths]
        rt = [round(rng.uniform(5.0, 25.0), 3) for _ in depths]
        rho[5], rho[8], rt[10], rt[1] = -999.25, 2.8, 0.0, 0.05
        header = """~Version Information
 VERS. 2.0 : CWLS LOG ASCII STANDARD
 WRAP. NO
~Well Information
 STRT.M 1500
 STOP.M 1506
 STEP.M 0.5
 NULL. -999.25
 WELL. SYNTHETIC-FORMATION
~Curve Information
 DEPT.M : Measured depth
 GR.API : Gamma ray
 RHOB.G/CC : Bulk density
 RT.OHM-M : Deep resistivity
~ASCII
"""
        path.write_text(header + "".join(f"{d:.2f} {g:.4f} {r:.4f} {t:.4f}\n"
                        for d, g, r, t in zip(depths, gr, rho, rt)), encoding="ascii")
        (inputs / "formation-parameters.json").write_text(json.dumps(parameters, indent=2) + "\n")
        rows = []
        for d, g, r, t in zip(depths, gr, rho, rt):
            valid = all(x != -999.25 for x in (g, r, t)) and r > 0 and t > 0
            vsh = max(0.0, min(1.0, (g - 20.0) / 100.0)) if valid else None
            phi = (2.65 - r) / 1.65 if valid else None
            phi = phi if phi is not None and 0 <= phi <= 1 else None
            raw_sw = (0.05 / (phi * phi * t)) ** 0.5 if phi is not None and phi > 0 else None
            rows.append(dict(depth_m=d, qc_valid=valid, vsh=vsh, phi_d=phi,
                             sw=min(1.0, raw_sw) if raw_sw is not None else None,
                             sw_clipped=raw_sw is not None and raw_sw > 1))
        intervals = []
        for upper, lower in zip(rows, rows[1:]):
            if upper["vsh"] is None or lower["vsh"] is None:
                continue
            lith = "sandstone" if upper["vsh"] < 0.3 else "siltstone" if upper["vsh"] < 0.6 else "shale"
            if intervals and intervals[-1]["base_m"] == upper["depth_m"] and intervals[-1]["lithology"] == lith:
                intervals[-1]["base_m"] = lower["depth_m"]
            else:
                intervals.append(dict(top_m=upper["depth_m"], base_m=lower["depth_m"], lithology=lith))
        expected = {"evaluated.json": {"rows": rows}, "lithology.json": {"intervals": intervals}}
    elif task == "segy-subset":
        path = inputs / "survey.sgy"
        text_header = "".join(
            f"C{i:2d} SYNTHETIC AGENT EVALUATION; NO FIELD DATA".ljust(80)
            for i in range(1, 41)
        ).encode("ascii")
        binary = bytearray(400)
        for offset, value in ((16, 2000), (20, 12), (24, 5), (28, 1),
                              (300, 0x0100), (302, 1)):
            struct.pack_into(">H", binary, offset, value)
        inline_ids = [309, 311, 317, 313, 308, 311, 315, 320, 312]
        rng.shuffle(inline_ids)
        records = []
        for i, inline in enumerate(inline_ids):
            hdr = bytearray(240)
            struct.pack_into(">i", hdr, 0, i + 1)
            struct.pack_into(">h", hdr, 28, 1)
            values = dict(CDP=100 + i, SourceGroupScalar=-10,
                          SourceX=4560000 + i * 125, SourceY=61230000 + i * 75,
                          CoordinateUnits=1, DelayRecordingTime=24,
                          TRACE_SAMPLE_COUNT=12, TRACE_SAMPLE_INTERVAL=2000,
                          INLINE_3D=inline, CROSSLINE_3D=700 + i)
            for name, (offset, fmt) in TRACE_FIELDS.items():
                struct.pack_into(">" + fmt, hdr, offset, values[name])
            samples = [rng.randrange(-10000, 10000) / 16.0 for _ in range(12)]
            records.append(bytes(hdr) + struct.pack(">12f", *samples))
        path.write_bytes(text_header + binary + b"".join(records))
        parsed = read_segy(path)
        expected = {**parsed, "traces": [t for t in parsed["traces"]
                    if 310 <= t["headers"]["INLINE_3D"] <= 315]}
    else:
        raise ValueError(f"unknown task: {task}")
    return {"expected": expected, "input_name": path.name, "input_sha256": digest(path),
            "input_files_sha256": {item.name: digest(item) for item in sorted(inputs.iterdir()) if item.is_file()}}


def read_segy(path: Path) -> dict:
    """Read this task's fixed-length, big-endian IEEE SEG-Y subset only."""
    data = path.read_bytes()
    if len(data) < 3600:
        raise ValueError("SEG-Y file is shorter than its headers")
    u16 = lambda offset: struct.unpack_from(">H", data, offset)[0]
    count, interval, fmt = u16(3220), u16(3216), u16(3224)
    if fmt != 5 or count < 1 or u16(3504) != 0:
        raise ValueError("expected IEEE samples and no extended text headers")
    stride = 240 + 4 * count
    if (len(data) - 3600) % stride:
        raise ValueError("truncated or inconsistent trace records")
    traces = []
    for offset in range(3600, len(data), stride):
        headers = {name: struct.unpack_from(">" + code, data, offset + pos)[0]
                   for name, (pos, code) in TRACE_FIELDS.items()}
        samples = list(struct.unpack_from(f">{count}f", data, offset + 240))
        traces.append(dict(headers=headers, samples=samples))
    return dict(text_sha256=hashlib.sha256(data[:3200]).hexdigest(),
                sample_count=count, sample_interval_us=interval,
                format=fmt, traces=traces)


def compare(expected, actual, path="result", tolerance=1e-7) -> list[str]:
    """Compare scientific values with an explicit tolerance and strict types."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path}: expected an object"]
        return [issue for key, value in expected.items() for issue in
                ([f"{path}.{key}: missing"] if key not in actual else
                 compare(value, actual[key], f"{path}.{key}", tolerance))]
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            return [f"{path}: incorrect item count"]
        return [issue for i, (a, b) in enumerate(zip(expected, actual))
                for issue in compare(a, b, f"{path}[{i}]", tolerance)]
    if expected is None:
        return [] if actual is None else [f"{path}: expected null"]
    if isinstance(expected, bool) or isinstance(expected, str):
        return [] if type(expected) is type(actual) and expected == actual else [f"{path}: mismatch"]
    if isinstance(expected, int):
        return [] if type(actual) is int and actual == expected else [f"{path}: integer mismatch"]
    if isinstance(expected, float):
        valid = (type(actual) in (float, int) and math.isfinite(actual)
                 and math.isclose(expected, actual, rel_tol=tolerance, abs_tol=tolerance))
        return [] if valid else [f"{path}: numerical mismatch"]
    raise TypeError(f"unsupported oracle value: {type(expected)}")


def grade(task: str, workspace: Path, oracle: dict) -> dict:
    checks = []
    input_path = workspace / "inputs" / oracle["input_name"]
    if not input_path.is_file() or digest(input_path) != oracle["input_sha256"]:
        checks.append("input: changed or missing")
    for name, sha in oracle.get("input_files_sha256", {}).items():
        candidate = workspace / "inputs" / name
        if not candidate.is_file() or candidate.is_symlink() or digest(candidate) != sha:
            checks.append(f"input {name}: changed or missing")
    if not (workspace / "solution.py").is_file() or (workspace / "solution.py").is_symlink():
        checks.append("solution.py: missing reproducible source")
    if task == "formation-evaluation":
        outputs = {}
        for name, expected in oracle["expected"].items():
            candidate = workspace / name
            try:
                if candidate.is_symlink():
                    raise ValueError("output must be a regular task artifact")
                checks.extend(compare(expected, json.loads(candidate.read_text()), path=name))
                outputs[name] = digest(candidate)
            except (OSError, ValueError, TypeError) as exc:
                checks.append(f"{name}: unreadable or invalid ({type(exc).__name__})")
        return {"passed": not checks, "failures": checks, "output_sha256": outputs}
    output = workspace / ("result.json" if task == "las-qc" else "subset.sgy")
    try:
        if output.is_symlink():
            raise ValueError("output must be a regular task artifact")
        actual = (json.loads(output.read_text()) if task == "las-qc"
                  else read_segy(output))
        checks.extend(compare(oracle["expected"], actual, tolerance=0 if task == "segy-subset" else 1e-7))
    except (OSError, ValueError, TypeError, struct.error) as exc:
        checks.append(f"output: unreadable or invalid ({type(exc).__name__})")
    return {"passed": not checks, "failures": checks,
            "output_sha256": digest(output) if output.is_file() and not output.is_symlink() else None}
