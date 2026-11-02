#!/usr/bin/env python3
"""Run one declared scientific environment with an existing Python interpreter.

Each suite gets its own process. No dependencies are installed. Missing imports,
zero collected tests, skips, expected failures and timeouts all fail validation.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import traceback
import unittest


ROOT = Path(__file__).resolve().parents[1]


def run_case(path, report_path):
    """Child-process entrypoint; deliberately needs only the standard library."""
    result = {"tests_run": 0, "failures": 0, "errors": 0, "skipped": 0,
              "expected_failures": 0, "unexpected_successes": 0, "passed": False}
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location("scientific_suite", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        outcome = unittest.TextTestRunner(verbosity=2).run(suite)
        result.update(tests_run=outcome.testsRun, failures=len(outcome.failures), errors=len(outcome.errors),
                      skipped=len(outcome.skipped), expected_failures=len(outcome.expectedFailures),
                      unexpected_successes=len(outcome.unexpectedSuccesses))
        result["passed"] = (outcome.wasSuccessful() and outcome.testsRun > 0
                            and not outcome.skipped and not outcome.expectedFailures)
    except Exception as error:
        result.update(errors=1, error_type=type(error).__name__)
        traceback.print_exc()
    report_path.write_text(json.dumps(result, indent=2) + "\n")
    return 0 if result["passed"] else 1


def run_environment(root, name, python, report_path=None, timeout=600):
    # Coverage validation depends on PyYAML in the maintainer environment only.
    if __package__:
        from .check_coverage import load_registry
    else:
        from check_coverage import load_registry
    registry, _ = load_registry(root)
    if name not in registry["environments"]:
        raise ValueError(f"Unknown environment {name!r}; choose from {', '.join(registry['environments'])}")
    if timeout <= 0:
        raise ValueError("Timeout must be positive")
    if report_path and report_path.exists():
        raise ValueError("Report already exists; choose a new output path")
    # Do not resolve a venv's python symlink into the base interpreter.
    python = Path(os.path.abspath(python))
    probe = subprocess.run([str(python), "-I", "-B", "-c",
        "import sys,json,importlib.metadata as m; print(json.dumps({'python':sys.version.split()[0],"
        "'packages':{d.metadata['Name']:d.version for d in m.distributions() if d.metadata['Name']}}))"],
        capture_output=True, text=True, timeout=30)
    if probe.returncode:
        raise ValueError("Cannot inspect the selected scientific interpreter")
    runtime = json.loads(probe.stdout)
    environment = registry["environments"][name]
    if ".".join(runtime["python"].split(".")[:2]) != environment["python"]:
        raise ValueError(f"{name} requires Python {environment['python']}; selected {runtime['python']}")
    suites = [(sid, suite) for sid, suite in registry["suites"].items() if suite["environment"] == name]
    if not suites:
        raise ValueError(f"No suites registered for {name}")
    baseline = root / environment["requirements"]
    report = {"schema_version": 1, "recorded_at": datetime.now(timezone.utc).isoformat(),
              "environment": name, "runtime": runtime, "baseline": environment["requirements"],
              "baseline_sha256": hashlib.sha256(baseline.read_bytes()).hexdigest(),
              "scope": "Executed registered suites; no agent model was invoked.", "results": []}
    with tempfile.TemporaryDirectory(prefix="geoscience-science-run-") as temporary:
        workspace = Path(temporary)
        env = dict(os.environ, MPLBACKEND="Agg", MPLCONFIGDIR=str(workspace / "mpl"),
                   PYVISTA_OFF_SCREEN="true", PYTHONDONTWRITEBYTECODE="1",
                   OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", NUMBA_CACHE_DIR=str(workspace / "numba"))
        if name == "hydro":
            env.setdefault("NUMBA_THREADING_LAYER", "workqueue")
        for sid, suite in suites:
            path = root / suite["path"]
            case_report = workspace / f"{sid}.json"
            started = time.monotonic()
            item = {"suite": sid, "path": suite["path"],
                    "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "passed": False}
            print(f"Running {name}/{sid}", flush=True)
            try:
                outcome = subprocess.run([str(python), "-I", "-B", str(Path(__file__).absolute()),
                    "--case", str(path), "--case-report", str(case_report)], cwd=root, env=env,
                    capture_output=True, text=True, timeout=timeout)
                print(outcome.stdout, end="")
                print(outcome.stderr, end="", file=sys.stderr)
                if case_report.is_file():
                    item.update(json.loads(case_report.read_text()))
                item["exit_code"] = outcome.returncode
                item["passed"] = bool(item["passed"] and outcome.returncode == 0)
            except subprocess.TimeoutExpired:
                item["error_type"] = "TimeoutExpired"
            item["duration_seconds"] = round(time.monotonic() - started, 3)
            report["results"].append(item)
    report["passed"] = all(item["passed"] for item in report["results"])
    report["tests_run"] = sum(item.get("tests_run", 0) for item in report["results"])
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with report_path.open("x") as handle:
            json.dump(report, handle, indent=2, allow_nan=False)
            handle.write("\n")
    print(f"{name}: {report['tests_run']} tests across {len(suites)} suites; "
          f"{'PASSED without skips' if report['passed'] else 'FAILED'}")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--environment", help="Environment name in tests/skill_coverage.json")
    parser.add_argument("--python", type=Path, help="Existing isolated scientific Python")
    parser.add_argument("--report", type=Path, help="New JSON report path")
    parser.add_argument("--timeout", type=float, default=600, help="Seconds per suite")
    parser.add_argument("--case", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--case-report", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.case:
        if not args.case_report:
            parser.error("Internal case execution needs --case-report")
        return run_case(args.case, args.case_report)
    if not args.environment or not args.python:
        parser.error("--environment and --python are required")
    try:
        report = run_environment(args.root.resolve(), args.environment, args.python, args.report, args.timeout)
        return 0 if report["passed"] else 1
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Scientific run failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
