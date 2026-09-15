#!/usr/bin/env python3
"""Check upstream skills CLI installation in disposable, project-scoped folders.

This checks packaging and resource preservation, not agent/model execution.
Requires Node.js/npm and network access for the pinned installer package.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import yaml

SKILLS_CLI_VERSION = "1.5.26"
# Test expectations checked against skills@1.5.26's agent registry. This is not an installer:
# upstream performs installation, and this snapshot detects destination drift.
TARGET_SKILL_DIRS = {
    "codex": ".agents/skills",
    "claude-code": ".claude/skills",
    "github-copilot": ".agents/skills",
    "gemini-cli": ".agents/skills",
    "windsurf": ".windsurf/skills",
    "opencode": ".agents/skills",
    "cline": ".agents/skills",
    "roo": ".roo/skills",
    "openclaw": "skills",
}


def source_skills(root):
    """Read the validated source inventory without relying on a platform manifest."""
    from validate_skills import find_skill_dirs

    sources = {}
    for directory in find_skill_dirs(root):
        text = (directory / "SKILL.md").read_text(encoding="utf-8")
        metadata = yaml.safe_load(text.split("---", 2)[1])
        name = metadata["name"]
        if name in sources:
            raise ValueError(f"Duplicate source skill: {name}")
        sources[name] = directory
    if not sources:
        raise ValueError("No source skills found")
    return sources


def check_installed(project, sources, catalogue, agent):
    """Check listed project skills at the expected target location."""
    if not isinstance(catalogue, list):
        raise ValueError("Installer inventory must be a JSON array")
    found = set()
    for entry in catalogue:
        if entry.get("scope") != "project":
            raise ValueError("Skill does not have project scope")
        directory = Path(entry["path"]).resolve()
        if not directory.is_relative_to(project.resolve()):
            raise ValueError("Installed skill is outside the temporary project")
        entrypoint = directory / "SKILL.md"
        name = entry["name"]
        if name not in sources:
            raise ValueError(f"Unexpected installed skill: {name}")
        expected_directory = (project / TARGET_SKILL_DIRS[agent] / name).resolve()
        if directory != expected_directory:
            raise ValueError(f"Skill is not in the expected {agent} directory: {name}")
        # CLI 1.5.25's `agents` field depends on detecting installed applications
        # in the host's user directory; it can be empty in a clean CI environment.
        source = sources[name]
        expected = [source / "SKILL.md"]
        for folder in ("scripts", "references", "assets"):
            expected.extend(
                path for path in (source / folder).rglob("*")
                if path.is_file()
                and "__pycache__" not in path.parts
                and path.suffix not in {".pyc", ".pyo"}
            )
        for original in expected:
            installed = entrypoint.parent / original.relative_to(source)
            if not installed.is_file() or installed.read_bytes() != original.read_bytes():
                raise ValueError(f"Missing or changed resource: {name}/{original.relative_to(source)}")
        found.add(name)
    missing = set(sources) - found
    if missing:
        raise ValueError(f"Skills not installed: {', '.join(sorted(missing))}")
    return len(found)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--agents", nargs="+", choices=TARGET_SKILL_DIRS, default=tuple(TARGET_SKILL_DIRS))
    parser.add_argument("--cli-version", default=SKILLS_CLI_VERSION)
    args = parser.parse_args()
    npx = shutil.which("npx")
    if not npx:
        parser.error("Node.js/npm (npx) is required")
    root = args.root.resolve()
    sources = source_skills(root)
    environment = dict(os.environ, DO_NOT_TRACK="1")
    print(f"skills CLI {args.cli_version}; {len(sources)} source skills", flush=True)
    for agent in args.agents:
        with tempfile.TemporaryDirectory(prefix="geoscience-install-") as temporary:
            project = Path(temporary)
            command = [
                npx, "--yes", f"skills@{args.cli_version}", "add", str(root),
                "--full-depth", "--skill", "*", "--agent", agent, "--copy", "--yes",
            ]
            result = subprocess.run(
                command, cwd=project, env=environment,
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=240,
            )
            if result.returncode:
                raise RuntimeError(f"{agent}: installer failed\n{result.stdout}\n{result.stderr}")
            listing = subprocess.run(
                [npx, "--yes", f"skills@{args.cli_version}", "list", "--agent", agent, "--json"],
                cwd=project, env=environment, capture_output=True,
                text=True, encoding="utf-8", errors="replace", timeout=120,
            )
            if listing.returncode:
                raise RuntimeError(f"{agent}: inventory failed\n{listing.stdout}\n{listing.stderr}")
            count = check_installed(project, sources, json.loads(listing.stdout), agent)
            print(f"PASS {agent}: {count} skills in target inventory and directory; resources preserved", flush=True)
    print("Installation checks passed; no target agent or scientific task was run.")


if __name__ == "__main__":
    main()
