"""The scientific runner must not count skipped or absent tests as validated."""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_science


class ScienceRunnerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def run_child(self, source):
        path = self.root / "test_sample.py"
        report = self.root / "case.json"
        path.write_text(source)
        result = subprocess.run([sys.executable, "-I", str(ROOT / "scripts/run_science.py"),
                                 "--case", str(path), "--case-report", str(report)],
                                 capture_output=True, text=True, timeout=30)
        return result, json.loads(report.read_text())

    def test_real_test_execution_succeeds(self):
        result, report = self.run_child("import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertEqual(2+2,4)\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(report["passed"])
        self.assertEqual(report["tests_run"], 1)

    def test_skips_expected_failures_and_zero_tests_are_failures(self):
        sources = ["import unittest\nclass T(unittest.TestCase):\n @unittest.skip('missing library')\n def test_skip(self): pass\n",
                   "import unittest\nclass T(unittest.TestCase):\n @unittest.expectedFailure\n def test_fail(self): self.fail()\n",
                   "# no test cases\n"]
        for source in sources:
            with self.subTest(source=source):
                result, report = self.run_child(source)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(report["passed"])

    def test_missing_dependency_and_assertion_failure_are_not_successes(self):
        for source in ("import definitely_missing_geoscience_dependency\n",
                       "import unittest\nclass T(unittest.TestCase):\n def test_wrong(self): self.assertEqual(2+2,5)\n"):
            with self.subTest(source=source):
                result, report = self.run_child(source)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(report["passed"])
                self.assertGreater(report["errors"] + report["failures"], 0)

    def test_environment_runner_records_runtime_and_protects_existing_report(self):
        for directory in ("sample", "tests/science"):
            (self.root / directory).mkdir(parents=True)
        (self.root / "sample/SKILL.md").write_text("---\nname: sample\ndescription: Sample.\n---\n")
        (self.root / "tests/science/requirements-test.txt").write_text("# standard library\n")
        (self.root / "tests/science/test_sample.py").write_text(
            "import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n")
        registry = {"schema_version": 1,
            "environments": {"test": {"python": f"{sys.version_info.major}.{sys.version_info.minor}",
                "requirements": "tests/science/requirements-test.txt", "setup": "Existing interpreter."}},
            "suites": {"sample": {"path": "tests/science/test_sample.py", "environment": "test"}},
            "skills": {"sample": {"checks": ["sample"], "scope": "Runner fixture.", "scripts": {}}}}
        (self.root / "tests/skill_coverage.json").write_text(json.dumps(registry))
        output = self.root / "report.json"
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            report = run_science.run_environment(self.root, "test", Path(sys.executable), output)
        self.assertTrue(report["passed"])
        self.assertEqual(report["tests_run"], 1)
        self.assertIn("packages", report["runtime"])
        self.assertEqual(json.loads(output.read_text()), report)
        with self.assertRaisesRegex(ValueError, "already exists"):
            run_science.run_environment(self.root, "test", Path(sys.executable), output)
        registry["environments"]["test"]["python"] = "3.99"
        (self.root / "tests/skill_coverage.json").write_text(json.dumps(registry))
        with self.assertRaisesRegex(ValueError, "requires Python"):
            run_science.run_environment(self.root, "test", Path(sys.executable))


if __name__ == "__main__":
    unittest.main()
