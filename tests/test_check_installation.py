"""Ensure installation checks require target discovery and preserve resources."""

from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_installation import check_installed


class InstallationCheckTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="geoscience test ")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "source" / "example"
        self.project = self.root / "target project"
        self.source.mkdir(parents=True)
        (self.source / "SKILL.md").write_text(
            "---\nname: example\ndescription: Example task\n---\n# Example\n",
            encoding="utf-8",
        )
        (self.source / "references").mkdir()
        (self.source / "references" / "units.md").write_text("Units: metres\n", encoding="utf-8")
        self.destination = self.project / ".agents" / "skills" / "example"
        shutil.copytree(self.source, self.destination)
        self.sources = {"example": self.source}
        self.catalogue = [{
            "name": "example", "path": str(self.destination),
            "scope": "project", "agents": ["Codex"],
        }]

    def test_target_skill_and_resources_pass(self):
        self.assertEqual(check_installed(self.project, self.sources, self.catalogue, "codex"), 1)

    def test_host_application_detection_is_not_required(self):
        self.catalogue[0]["agents"] = []
        self.assertEqual(check_installed(self.project, self.sources, self.catalogue, "codex"), 1)

    def test_copy_in_another_agents_directory_fails(self):
        with self.assertRaisesRegex(ValueError, "expected claude-code directory"):
            check_installed(self.project, self.sources, self.catalogue, "claude-code")

    def test_unlisted_copy_cannot_satisfy_installation(self):
        with self.assertRaisesRegex(ValueError, "Skills not installed"):
            check_installed(self.project, self.sources, [], "codex")

    def test_missing_or_changed_resource_fails(self):
        (self.destination / "references" / "units.md").write_text("Units: feet\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Missing or changed resource"):
            check_installed(self.project, self.sources, self.catalogue, "codex")

    def test_outside_project_copy_fails(self):
        self.catalogue[0]["path"] = str(self.source)
        with self.assertRaisesRegex(ValueError, "outside the temporary project"):
            check_installed(self.project, self.sources, self.catalogue, "codex")


if __name__ == "__main__":
    unittest.main()
