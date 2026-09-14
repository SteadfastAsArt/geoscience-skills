"""Regression tests for portability, discovery, and platform registration."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml


VALIDATOR_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate_skills.py"
SPEC = importlib.util.spec_from_file_location("validate_skills", VALIDATOR_PATH)
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="geoscience-validator-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def skill(self, relative="sample", metadata=None, body="Useful instructions.\n", **fields):
        directory = self.root / relative
        directory.mkdir(parents=True, exist_ok=True)
        data = {"name": directory.name, "description": "Use when analysing sample data."}
        if metadata is not None:
            data["metadata"] = metadata
        data.update(fields)
        (directory / "SKILL.md").write_text(
            "---\n" + yaml.safe_dump(data, sort_keys=False) + "---\n" + body,
            encoding="utf-8",
        )
        return directory

    def manifest(self, data, filename=".claude-plugin/marketplace.json"):
        path = self.root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")

    def marketplace(self, paths=None):
        paths = paths if paths is not None else ["sample"]
        return {
            "name": "test-marketplace", "owner": {"name": "Test Maintainer"},
            "plugins": [
                {"name": Path(path).name, "source": "./", "strict": False, "skills": [f"./{path}"]}
                for path in paths
            ],
        }

    def check(self, **kwargs):
        return validator.validate_repository(self.root, **kwargs)

    def messages(self, result):
        return "\n".join(issue.message for issue in result.issues)

    def test_portable_skill_needs_no_platform_files_or_minimum_length(self):
        self.skill()
        self.assertEqual([], self.check().issues)

    def test_nested_workflows_discovered_and_non_skill_areas_ignored(self):
        self.skill("workflows/one", metadata={"skill_type": "workflow"})
        self.skill("domain/group/two")
        self.skill("using-geoscience-skills", metadata={"skill_type": "meta"})
        for ignored in ("docs/template", "tests/fixture", ".hidden/secret", "domain/references/example"):
            self.skill(ignored, name="invalid name")
        result = self.check()
        self.assertEqual({"one", "two", "using-geoscience-skills"}, {path.name for path in result.skill_dirs})
        self.assertEqual([], result.issues)

    def test_non_mapping_and_malformed_frontmatter_report_errors(self):
        directory = self.skill()
        for text in ("[]", "42", "plain scalar", "null", "name: [broken", "name: sample\nname: duplicate"):
            with self.subTest(text=text):
                (directory / "SKILL.md").write_text(f"---\n{text}\n---\nInstructions.")
                result = self.check()
                self.assertTrue(result.errors)
                self.assertRegex(self.messages(result), "mapping|Invalid YAML")

    def test_required_fields_types_names_and_lengths(self):
        for fields, expected in (
            ({"description": 42}, "description must be a non-empty string"),
            ({"name": "Wrong_Name"}, "name must use lowercase"),
            ({"name": "other"}, "must match directory"),
            ({"name": "x" * 65}, "name exceeds 64"),
            ({"description": "x" * 1025}, "description exceeds 1024"),
            ({"compatibility": "x" * 501}, "compatibility exceeds 500"),
            ({"allowed-tools": ["Read"]}, "allowed-tools must be a non-empty string"),
            ({"version": "1.0.0"}, "Unsupported frontmatter field"),
        ):
            with self.subTest(fields=fields):
                self.skill(**fields)
                self.assertIn(expected, self.messages(self.check()))

    def test_metadata_requires_strings_and_valid_json_arrays(self):
        for metadata, expected in (
            ([], "metadata must be a string-to-string mapping"),
            ({"version": 1}, "must have a string key and value"),
            ({"tags": ["one"]}, "must have a string key and value"),
            ({"tags": "[one]"}, "must encode a JSON array"),
            ({"dependencies": '{"numpy": "1"}'}, "must encode a JSON array"),
            ({"complements": '["sample", 1]'}, "must encode a JSON array"),
            ({"workflow_role": "unknown"}, "Invalid metadata.workflow_role"),
            ({"skill_type": "unknown"}, "Invalid metadata.skill_type"),
        ):
            with self.subTest(metadata=metadata):
                self.skill(metadata=metadata)
                self.assertIn(expected, self.messages(self.check()))

    def test_valid_metadata_and_known_complements(self):
        self.skill(metadata={
            "version": "1.0.0", "author": "Test", "tags": '["One"]',
            "dependencies": '["numpy>=1.0"]', "complements": '["other"]',
            "workflow_role": "analysis", "skill_type": "domain",
        })
        self.skill("other")
        self.assertEqual([], self.check().issues)

    def test_unknown_complement_and_duplicate_skill_name(self):
        self.skill(metadata={"complements": '["missing"]'})
        self.skill("group/sample")
        messages = self.messages(self.check())
        self.assertIn("Unknown complementary skill: missing", messages)
        self.assertIn("Duplicate skill name", messages)

    def test_tagged_fences_do_not_warn_on_closing_or_code_links(self):
        self.skill(body=(
            "```python\nprint('hello')\n[not a link](missing.md)\n```\n"
            "~~~~text\n```\n~~~\n~~~~\n"
            "````markdown\n```python\nexample\n```\n````\n"
        ))
        self.assertEqual([], self.check().issues)

    def test_untagged_fence_reports_only_opening(self):
        self.skill(body="```\nexample\n```\n")
        result = self.check()
        self.assertEqual(1, len(result.warnings))
        self.assertIn("opening has no language tag", result.warnings[0].message)
        self.assertEqual([], result.errors)

    def test_unclosed_fence_is_an_error(self):
        self.skill(body="```python\nprint('unterminated')\n")
        self.assertIn("Unclosed fenced code block", self.messages(self.check()))

    def test_relative_links_references_and_cross_skill_paths(self):
        directory = self.skill(body=(
            "[Guide](references/guide.md)\n[Other](../other/SKILL.md)\n"
            "[Web](https://example.org/docs)\n[Anchor](#local)\n"
            "`[literal](missing.md)`\n[Reference][guide]\n[guide]: references/guide.md\n"
        ))
        self.skill("other")
        reference = directory / "references" / "guide.md"
        reference.parent.mkdir()
        reference.write_text("[Example](example.txt)\n")
        (reference.parent / "example.txt").write_text("data")
        self.assertEqual([], self.check().issues)
        (reference.parent / "example.txt").unlink()
        result = self.check()
        self.assertEqual(1, len(result.errors))
        self.assertEqual(reference, result.errors[0].path)
        self.assertIn("Broken relative link", result.errors[0].message)

    def test_broken_link_and_link_to_excluded_skill(self):
        self.skill(body="[Missing](references/absent.md)\n[Template](../docs/template/SKILL.md)\n")
        self.skill("docs/template")
        messages = self.messages(self.check())
        self.assertIn("Broken relative link", messages)
        self.assertIn("outside discovery", messages)

    def test_both_manifests_register_nested_skills(self):
        self.skill()
        self.skill("workflows/analysis")
        paths = ["sample", "workflows/analysis"]
        self.manifest(self.marketplace(paths))
        self.manifest({"id": "test", "configSchema": {}, "skills": [f"./{path}" for path in paths]}, "openclaw.plugin.json")
        self.assertEqual([], self.check().issues)

    def test_marketplace_requires_owner(self):
        self.skill()
        data = self.marketplace()
        del data["owner"]
        self.manifest(data)
        self.assertIn("Marketplace owner", self.messages(self.check()))
        self.assertEqual([], self.check(check_manifests=False).issues)

    def test_marketplace_bad_source_unknown_path_duplicate_and_omission(self):
        self.skill()
        self.skill("omitted")
        data = self.marketplace()
        data["plugins"].append(dict(data["plugins"][0]))
        data["plugins"].append({"name": "bad-path", "source": "./", "skills": ["./missing"]})
        data["plugins"].append({"name": "bad-source", "source": "./absent", "skills": ["./sample"]})
        self.manifest(data)
        messages = self.messages(self.check())
        for expected in ("Duplicate plugin name", "Duplicate skill registration", "directory does not exist", "Missing skill registration: omitted"):
            self.assertIn(expected, messages)

    def test_platform_paths_cannot_escape_root(self):
        self.skill()
        data = self.marketplace()
        data["plugins"][0]["skills"] = ["./../"]
        self.manifest(data)
        self.assertIn("escapes repository", self.messages(self.check()))

    def test_openclaw_unknown_duplicate_and_missing_paths(self):
        self.skill()
        self.skill("omitted")
        self.manifest({"id": "test", "configSchema": {}, "skills": ["./sample", "./sample", "./absent"]}, "openclaw.plugin.json")
        messages = self.messages(self.check())
        for expected in ("Duplicate skill registration", "directory does not exist", "Missing skill registration: omitted"):
            self.assertIn(expected, messages)

    def test_malformed_platform_shapes_do_not_crash(self):
        self.skill()
        for data in ([], {"plugins": [None, 42, {"name": []}]}, {"plugins": {}}):
            with self.subTest(data=data):
                self.manifest(data)
                self.assertTrue(self.check().errors)
        self.manifest({"id": [], "configSchema": [], "skills": {"bad": "shape"}}, "openclaw.plugin.json")
        self.assertIn("OpenClaw skills must be an array", self.messages(self.check()))

    def test_cli_root_and_exit_status(self):
        self.skill()
        command = [sys.executable, str(VALIDATOR_PATH), "--root", str(self.root)]
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("Skills: 1  Errors: 0  Warnings: 0", result.stdout)
        self.skill(description=None)
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(1, result.returncode)
        self.assertIn("FAILED", result.stdout)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
