"""Regression tests for skill-derived optional platform manifests."""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
import sync_manifests


class ManifestSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.skill_paths = (
            "using-geoscience-skills",
            "example-domain",
            "workflows/example-workflow",
        )
        for relative_path in self.skill_paths:
            path = self.root / relative_path / "SKILL.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                "---\n"
                f"name: {path.parent.name}\n"
                "description: |\n"
                "  Example geoscience guidance.\n"
                "  Use for the selected task.\n"
                "license: MIT\n"
                "metadata:\n"
                "  version: '1.0.1'\n"
                "---\n\n# Example\n",
                encoding="utf-8",
            )

    def run_sync(self, *flags):
        with contextlib.redirect_stdout(io.StringIO()):
            return sync_manifests.main(["--root", str(self.root), *flags])

    def snapshots(self):
        return {
            path: (self.root / path).read_bytes()
            for path in (sync_manifests.MARKETPLACE_PATH,
                         sync_manifests.OPENCLAW_PATH)
        }

    def test_generation_has_complete_skill_paths_and_platform_schema(self):
        self.assertEqual(self.run_sync(), 0)
        marketplace = json.loads((self.root / sync_manifests.MARKETPLACE_PATH).read_text())
        openclaw = json.loads((self.root / sync_manifests.OPENCLAW_PATH).read_text())
        self.assertEqual(set(marketplace), {"name", "owner", "metadata", "plugins"})
        self.assertEqual(marketplace["owner"], {"name": "Geoscience Skills"})
        self.assertEqual(marketplace["metadata"]["version"], "2.5.0")
        expected_paths = {"./" + path for path in self.skill_paths}
        actual_paths = set()
        for plugin in marketplace["plugins"]:
            self.assertEqual(set(plugin), {
                "name", "source", "strict", "skills", "description", "version",
            })
            self.assertEqual(plugin["source"], "./")
            self.assertIs(plugin["strict"], False)
            self.assertEqual(plugin["version"], "1.0.1")
            self.assertEqual(len(plugin["skills"]), 1)
            skill_path = plugin["skills"][0]
            self.assertTrue((self.root / plugin["source"] / skill_path / "SKILL.md").is_file())
            self.assertEqual(plugin["name"], Path(skill_path).name)
            actual_paths.add(skill_path)
        self.assertEqual(actual_paths, expected_paths)
        self.assertEqual(openclaw["skills"], [p["skills"][0] for p in marketplace["plugins"]])
        self.assertEqual(openclaw["version"], "2.5.0")
        self.assertEqual(openclaw["configSchema"], {})

    def test_generation_is_deterministic_and_check_is_read_only(self):
        self.assertEqual(self.run_sync(), 0)
        first = self.snapshots()
        self.assertEqual(self.run_sync(), 0)
        self.assertEqual(self.snapshots(), first)
        mtimes = {path: (self.root / path).stat().st_mtime_ns for path in first}
        self.assertEqual(self.run_sync("--check"), 0)
        self.assertEqual(self.snapshots(), first)
        self.assertEqual(
            {path: (self.root / path).stat().st_mtime_ns for path in first}, mtimes,
        )

    def test_metadata_changes_are_detected_without_writing(self):
        self.assertEqual(self.run_sync(), 0)
        initial = self.snapshots()
        skill_file = self.root / "example-domain/SKILL.md"
        original = skill_file.read_text(encoding="utf-8")
        for before, after in (("1.0.1", "1.0.2"),
                              ("Example geoscience guidance.", "Updated guidance.")):
            with self.subTest(changed_field=before):
                skill_file.write_text(original.replace(before, after), encoding="utf-8")
                self.assertEqual(self.run_sync("--check"), 1)
                self.assertEqual(self.snapshots(), initial)
        skill_file.write_text(original, encoding="utf-8")
        self.assertEqual(self.run_sync("--check"), 0)

    def test_check_reports_missing_manifests_without_creating_files(self):
        self.assertEqual(self.run_sync("--check"), 1)
        self.assertFalse((self.root / sync_manifests.MARKETPLACE_PATH).exists())
        self.assertFalse((self.root / sync_manifests.OPENCLAW_PATH).exists())
        self.assertFalse((self.root / ".claude-plugin").exists())

    def test_cli_accepts_an_isolated_root(self):
        command = [sys.executable, str(REPO_ROOT / "scripts/sync_manifests.py"),
                   "--root", str(self.root)]
        result = subprocess.run(command, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run(command + ["--check"], cwd=self.root,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_repository_manifests_cover_all_skills(self):
        manifests = sync_manifests.build_manifests(REPO_ROOT)
        skill_files = list(REPO_ROOT.glob("*/SKILL.md"))
        skill_files += list((REPO_ROOT / "workflows").glob("*/SKILL.md"))
        expected = {"./" + path.parent.relative_to(REPO_ROOT).as_posix()
                    for path in skill_files}
        self.assertTrue(expected)
        plugins = manifests[sync_manifests.MARKETPLACE_PATH]["plugins"]
        self.assertEqual(len(plugins), len(expected))
        self.assertEqual(len({plugin["name"] for plugin in plugins}), len(expected))
        self.assertEqual({plugin["skills"][0] for plugin in plugins}, expected)
        self.assertEqual(set(manifests[sync_manifests.OPENCLAW_PATH]["skills"]), expected)


if __name__ == "__main__":
    unittest.main()
