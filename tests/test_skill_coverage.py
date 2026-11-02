"""Coverage inventory must expose missing tests without claiming execution."""

import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_coverage as coverage


class CoverageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for directory in ("sample/scripts", "tests/science", "docs", "evals/results"):
            (self.root / directory).mkdir(parents=True)
        (self.root / "sample/SKILL.md").write_text("---\nname: sample\ndescription: Sample task.\n---\n")
        (self.root / "sample/scripts/process.py").write_text("print('sample')\n")
        (self.root / "tests/science/requirements-test.txt").write_text("# standard library only\n")
        (self.root / "tests/science/test_sample.py").write_text(
            "import unittest\nclass Sample(unittest.TestCase):\n    def test_result(self):\n        self.assertEqual(2+2,4)\n")
        self.registry = {"schema_version": 1,
            "environments": {"test": {"python": "3.12", "requirements": "tests/science/requirements-test.txt", "setup": "Isolated test environment."}},
            "suites": {"sample": {"environment": "test", "path": "tests/science/test_sample.py"}},
            "skills": {"sample": {"checks": ["sample"], "scope": "Selected numeric example only.",
                "scripts": {"scripts/process.py": {"gap": "CLI output readback has no execution test."}}}}}

    def test_explicit_gap_is_visible_and_not_upgraded_to_a_passing_test(self):
        inventory = coverage.validate(self.root, self.registry)
        rendered = coverage.markdown(self.root, self.registry, inventory)
        self.assertIn("0 scripts with declared execution tests", rendered)
        self.assertIn("1 explicit script coverage gaps", rendered)
        self.assertIn("CLI output readback", rendered)
        self.assertIn("not a passing run", rendered)

    def test_new_script_requires_a_mapping_even_when_the_skill_has_library_tests(self):
        (self.root / "sample/scripts/new.py").write_text("pass\n")
        with self.assertRaisesRegex(ValueError, "script coverage mismatch"):
            coverage.validate(self.root, self.registry)
        self.registry["skills"]["sample"]["scripts"]["scripts/new.py"] = {"checks": ["sample"]}
        coverage.validate(self.root, self.registry)

    def test_new_skill_and_new_scientific_suite_cannot_disappear_from_inventory(self):
        (self.root / "second").mkdir()
        (self.root / "second/SKILL.md").write_text("---\nname: second\ndescription: Another task.\n---\n")
        with self.assertRaisesRegex(ValueError, "Skill coverage mismatch"):
            coverage.validate(self.root, self.registry)
        self.registry["skills"]["second"] = {"checks": [], "scope": "Unverified guidance.", "scripts": {}}
        (self.root / "tests/science/test_new.py").write_text("def test_new(): pass\n")
        with self.assertRaisesRegex(ValueError, "Scientific suites missing"):
            coverage.validate(self.root, self.registry)

    def test_missing_environment_or_non_test_file_cannot_satisfy_coverage(self):
        for field, value in (("environment", "absent"), ("path", "sample/scripts/process.py")):
            changed = copy.deepcopy(self.registry)
            changed["suites"]["sample"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                coverage.validate(self.root, changed)
        (self.root / "tests/science/test_sample.py").write_text("# no tests\n")
        with self.assertRaisesRegex(ValueError, "no test functions"):
            coverage.validate(self.root, self.registry)

    def test_unknown_duplicate_or_empty_script_checks_are_rejected(self):
        for record in ({"checks": ["absent"]}, {"checks": []}, {"checks": ["sample", "sample"]},
                       {"gap": ""}, {"gap": "missing", "checks": ["sample"]}):
            changed = copy.deepcopy(self.registry)
            changed["skills"]["sample"]["scripts"]["scripts/process.py"] = record
            with self.subTest(record=record), self.assertRaises(ValueError):
                coverage.validate(self.root, changed)

    def test_external_paths_cannot_satisfy_requirements_or_suite_links(self):
        for path in ("../outside.py", "/tmp/outside.py", "a\\b.py"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                coverage.project_file(self.root, path)
        for name in ("../outside", "/tmp/outside", "a\\b"):
            changed = copy.deepcopy(self.registry)
            changed["suites"][name] = changed["suites"].pop("sample")
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "Invalid environment or suite ID"):
                coverage.validate(self.root, changed)

    def test_native_evidence_requires_success_and_tracks_complete_bundle_drift(self):
        inventory = coverage.validate(self.root, self.registry)
        record = {"status": "passed", "native_activation_verified": True, "exit_code": 0,
                  "numerical_checks": {"passed": True}, "native_discovery": {"passed": True},
                  "expected_skill": "sample", "observed_skill_reads": ["sample"], "task": "sample-task",
                  "installed_bundle_hashes": {"sample": coverage.bundle_hash(inventory["sample"])}}
        path = self.root / "evals/results/native.json"
        path.write_text(json.dumps({"evaluation_mode": "native", "results": [record]}))
        evidence = coverage.native_evidence(self.root, inventory)["sample"]
        self.assertTrue(evidence[0]["matches_current_bundle"])
        (inventory["sample"] / "scripts/process.py").write_text("print('changed')\n")
        self.assertFalse(coverage.native_evidence(self.root, inventory)["sample"][0]["matches_current_bundle"])
        record["numerical_checks"]["passed"] = False
        path.write_text(json.dumps({"evaluation_mode": "native", "results": [record]}))
        self.assertEqual(coverage.native_evidence(self.root, inventory)["sample"], [])

    def test_matrix_check_is_read_only_and_detects_scope_changes(self):
        registry = self.root / coverage.REGISTRY
        registry.write_text(json.dumps(self.registry))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(coverage.main(["--root", str(self.root), "--check"]), 1)
            self.assertFalse((self.root / coverage.MATRIX).exists())
            self.assertEqual(coverage.main(["--root", str(self.root), "--write"]), 0)
            original = (self.root / coverage.MATRIX).read_bytes()
            self.registry["skills"]["sample"]["scope"] = "Changed scope."
            registry.write_text(json.dumps(self.registry))
            self.assertEqual(coverage.main(["--root", str(self.root), "--check"]), 1)
            self.assertEqual((self.root / coverage.MATRIX).read_bytes(), original)

    def test_current_repository_registry_is_complete(self):
        registry, inventory = coverage.load_registry(ROOT)
        self.assertEqual(set(inventory), set(registry["skills"]))


if __name__ == "__main__":
    unittest.main()
