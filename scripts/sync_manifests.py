#!/usr/bin/env python3
"""Generate optional platform manifests from the repository's skill frontmatter.

Run without flags to update manifests, or use --check to detect drift without
writing. --root selects another skill repository for isolated validation.
"""

import argparse
import json
import sys
from pathlib import Path

if __package__:
    from .validate_skills import find_skill_dirs, parse_frontmatter
else:
    from validate_skills import find_skill_dirs, parse_frontmatter


RELEASE_VERSION = "2.4.0"
MARKETPLACE_PATH = Path(".claude-plugin/marketplace.json")
OPENCLAW_PATH = Path("openclaw.plugin.json")


def build_manifests(root):
    """Return both manifest documents using the validator's skill discovery."""
    root = Path(root).resolve()
    plugins = []
    names = set()
    for skill_dir in find_skill_dirs(root):
        skill_file = skill_dir / "SKILL.md"
        frontmatter = parse_frontmatter(skill_file.read_text(encoding="utf-8"))
        if not isinstance(frontmatter, dict) or "_error" in frontmatter:
            raise ValueError(f"{skill_file}: invalid or missing frontmatter")
        metadata = frontmatter.get("metadata", {})
        name = frontmatter.get("name")
        description = frontmatter.get("description")
        version = metadata.get("version") if isinstance(metadata, dict) else None
        for key, value in (("name", name), ("description", description),
                           ("metadata.version", version)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{skill_file}: {key} must be a nonempty string")
        if name in names:
            raise ValueError(f"{skill_file}: duplicate skill name {name!r}")
        names.add(name)
        skill_path = "./" + skill_dir.relative_to(root).as_posix()
        plugins.append({
            "name": name,
            "source": "./",
            "strict": False,
            "skills": [skill_path],
            "description": " ".join(description.split()),
            "version": version,
        })
    if not plugins:
        raise ValueError(f"{root}: no skills discovered")
    plugins.sort(key=lambda plugin: plugin["name"])
    description = (
        f"{len(plugins)} geoscience skills for AI coding assistants covering "
        "seismic, well logs, geological modelling, geophysical inversion, "
        "geostatistics, spatial regression, and related workflows."
    )
    return {
        MARKETPLACE_PATH: {
            "name": "geoscience-skills",
            "owner": {"name": "Geoscience Skills"},
            "metadata": {
                "description": description,
                "version": RELEASE_VERSION,
            },
            "plugins": plugins,
        },
        OPENCLAW_PATH: {
            "id": "geoscience-skills",
            "name": "Geoscience Skills",
            "version": RELEASE_VERSION,
            "description": description,
            "skills": [plugin["skills"][0] for plugin in plugins],
            "configSchema": {},
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true",
        help="report missing or outdated manifests without writing files",
    )
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1],
        help="skill repository root (default: this script's repository)",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        manifests = build_manifests(root)
        changed = []
        for relative_path, document in manifests.items():
            path = root / relative_path
            expected = (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
            if path.is_file() and path.read_bytes() == expected:
                continue
            changed.append(relative_path)
            if args.check:
                print(f"Out of date: {relative_path.as_posix()}")
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(expected)
                print(f"Updated: {relative_path.as_posix()}")
        if args.check and changed:
            print("Run scripts/sync_manifests.py with the same --root to regenerate.")
            return 1
        if not changed:
            print("Platform manifests are up to date.")
        return 0
    except (OSError, ValueError) as error:
        print(f"Cannot generate manifests: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
