#!/usr/bin/env python3
"""Check portable Agent Skills files and optional local platform registries.

Only PyYAML is required. Import validate_repository for structured results,
or use --root to check another skill repository. Platform checks cover local
skill registration; use the platform's own validator for its complete schema.
"""

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

import yaml


FRONTMATTER_FIELDS = {
    "name", "description", "license", "compatibility", "metadata", "allowed-tools",
}
SKIP_DIRS = {
    "agents", "assets", "build", "dist", "docs", "examples", "node_modules",
    "references", "scripts", "test", "tests", "__pycache__",
}
LIST_METADATA_FIELDS = {"tags", "dependencies", "complements"}
WORKFLOW_ROLES = {"data-loading", "processing", "analysis", "modelling", "visualization"}
SKILL_TYPES = {"domain", "workflow", "meta"}
NAME_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
FENCE_PATTERN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
LINK_PATTERN = re.compile(
    r"!?\[[^\]\n]*\]\(\s*(?:<([^>\n]+)>|([^\s)]+))"
    r"(?:\s+[\"'][^\n]*?[\"'])?\s*\)"
)
REFERENCE_PATTERN = re.compile(r"^ {0,3}\[[^\]]+\]:\s*(?:<([^>]+)>|(\S+))")


@dataclass(frozen=True)
class Issue:
    level: str
    path: Path
    message: str
    line: int | None = None


@dataclass
class ValidationResult:
    skill_dirs: list[Path]
    issues: list[Issue]

    @property
    def errors(self):
        return [issue for issue in self.issues if issue.level == "ERROR"]

    @property
    def warnings(self):
        return [issue for issue in self.issues if issue.level == "WARN"]


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate keys instead of silently retaining the last value."""


def _construct_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise yaml.constructor.ConstructorError(
                None, None, "mapping keys must be scalar values", key_node.start_mark
            ) from exc
        if duplicate:
            raise yaml.constructor.ConstructorError(
                None, None, f"duplicate key: {key!r}", key_node.start_mark
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def _split_frontmatter(text):
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("Missing YAML frontmatter opening delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("Missing YAML frontmatter closing delimiter") from exc
    try:
        data = yaml.load("\n".join(lines[1:end]), Loader=UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise ValueError(f"Invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("YAML frontmatter must be a mapping")
    return data, "\n".join(lines[end + 1:]), end + 2


def parse_frontmatter(text):
    """Return a frontmatter mapping, or raise a descriptive ValueError."""
    return _split_frontmatter(text)[0]


def find_skill_dirs(root):
    """Discover formal skills recursively, including nested workflow skills."""
    root = Path(root).resolve()
    found = []
    for current, directories, files in os.walk(root, followlinks=False):
        directories[:] = sorted(
            name for name in directories
            if not name.startswith(".") and name not in SKIP_DIRS
        )
        if "SKILL.md" in files:
            found.append(Path(current))
    return sorted(found)


def _check_frontmatter(data, skill_dir):
    path = skill_dir / "SKILL.md"
    issues = []
    for key in data:
        if key not in FRONTMATTER_FIELDS:
            issues.append(Issue("ERROR", path, f"Unsupported frontmatter field {key!r}; use metadata"))
    for field, limit in (("name", 64), ("description", 1024), ("compatibility", 500)):
        if field == "compatibility" and field not in data:
            continue
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            issues.append(Issue("ERROR", path, f"{field} must be a non-empty string"))
        elif len(value) > limit:
            issues.append(Issue("ERROR", path, f"{field} exceeds {limit} characters"))
    name = data.get("name")
    if isinstance(name, str):
        if not NAME_PATTERN.fullmatch(name):
            issues.append(Issue("ERROR", path, "name must use lowercase letters, digits, and single hyphens"))
        if name != skill_dir.name:
            issues.append(Issue("ERROR", path, f"name {name!r} must match directory {skill_dir.name!r}"))
    for field in ("license", "allowed-tools"):
        if field in data and (not isinstance(data[field], str) or not data[field].strip()):
            issues.append(Issue("ERROR", path, f"{field} must be a non-empty string"))
    metadata = data.get("metadata", {})
    if not isinstance(metadata, dict):
        issues.append(Issue("ERROR", path, "metadata must be a string-to-string mapping"))
        return issues
    for key, value in metadata.items():
        if not isinstance(key, str) or not isinstance(value, str):
            issues.append(Issue("ERROR", path, f"metadata entry {key!r} must have a string key and value"))
            continue
        if key in LIST_METADATA_FIELDS:
            try:
                items = json.loads(value)
            except json.JSONDecodeError:
                items = None
            if not isinstance(items, list) or any(not isinstance(item, str) or not item.strip() for item in items):
                issues.append(Issue("ERROR", path, f"metadata.{key} must encode a JSON array of non-empty strings"))
        if key == "workflow_role" and value not in WORKFLOW_ROLES:
            issues.append(Issue("ERROR", path, f"Invalid metadata.workflow_role: {value!r}"))
        if key == "skill_type" and value not in SKILL_TYPES:
            issues.append(Issue("ERROR", path, f"Invalid metadata.skill_type: {value!r}"))
    return issues


def markdown_prose(text, path, start_line=1, check_fences=True):
    """Return prose lines and fence issues, ignoring contents of fenced blocks."""
    prose, issues = [], []
    opened = None
    for number, line in enumerate(text.splitlines(), start_line):
        match = FENCE_PATTERN.match(line)
        if opened:
            if match:
                marker, rest = match.groups()
                if marker[0] == opened[0] and len(marker) >= opened[1] and not rest.strip():
                    opened = None
            continue
        if match:
            marker, info = match.groups()
            if marker[0] == "`" and "`" in info:
                prose.append((number, line))
                continue
            opened = (marker[0], len(marker), number)
            if check_fences and not info.strip():
                issues.append(Issue("WARN", path, "Code block opening has no language tag", number))
            continue
        prose.append((number, line))
    if opened and check_fences:
        issues.append(Issue("ERROR", path, "Unclosed fenced code block", opened[2]))
    return prose, issues


def _check_links(prose, path, known_skills=None):
    issues = []
    for number, line in prose:
        line = re.sub(r"(`+).*?\1", "", line)
        matches = list(LINK_PATTERN.finditer(line))
        reference = REFERENCE_PATTERN.match(line)
        if reference:
            matches.append(reference)
        for match in matches:
            destination = match.group(1) or match.group(2)
            try:
                url = urlsplit(destination)
            except ValueError:
                issues.append(Issue("ERROR", path, f"Invalid link: {destination}", number))
                continue
            if url.scheme or url.netloc or not url.path:
                continue
            target = (path.parent / unquote(url.path)).resolve()
            if not target.exists():
                issues.append(Issue("ERROR", path, f"Broken relative link: {destination}", number))
            elif known_skills is not None and target.name == "SKILL.md" and target.parent not in known_skills:
                issues.append(Issue("ERROR", path, f"Link targets a skill outside discovery: {destination}", number))
    return issues


def validate_skill(skill_dir, known_skills=None):
    """Return (frontmatter or None, issues) for one skill and its references."""
    skill_dir = Path(skill_dir).resolve()
    path = skill_dir / "SKILL.md"
    try:
        text = path.read_text(encoding="utf-8-sig")
        data, body, start_line = _split_frontmatter(text)
    except (OSError, UnicodeError, ValueError) as exc:
        return None, [Issue("ERROR", path, str(exc))]
    issues = _check_frontmatter(data, skill_dir)
    if len(body.splitlines()) > 500:
        issues.append(Issue("WARN", path, "Skill body exceeds 500 lines; move details to references"))
    prose, fence_issues = markdown_prose(body, path, start_line)
    issues.extend(fence_issues)
    issues.extend(_check_links(prose, path, known_skills))
    for reference in sorted((skill_dir / "references").rglob("*.md")):
        try:
            prose, _ = markdown_prose(reference.read_text(encoding="utf-8-sig"), reference, check_fences=False)
            issues.extend(_check_links(prose, reference, known_skills))
        except (OSError, UnicodeError) as exc:
            issues.append(Issue("ERROR", reference, str(exc)))
    return data, issues


def _read_manifest(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, [Issue("ERROR", path, f"Cannot read JSON manifest: {exc}")]
    if not isinstance(data, dict):
        return None, [Issue("ERROR", path, "Manifest must be a JSON object")]
    return data, []


def _local_path(value, base, root, manifest, label, issues):
    if not isinstance(value, str) or not value or (value != "." and not value.startswith("./")):
        issues.append(Issue("ERROR", manifest, f"{label} must be a local relative path beginning with ./"))
        return None
    target = (base / value).resolve()
    if not target.is_relative_to(root):
        issues.append(Issue("ERROR", manifest, f"{label} escapes repository: {value}"))
        return None
    if not target.is_dir():
        issues.append(Issue("ERROR", manifest, f"{label} directory does not exist: {value}"))
        return None
    return target


def _register_paths(paths, base, root, manifest, label, known_skills, registered, issues):
    if isinstance(paths, str):
        paths = [paths]
    if not isinstance(paths, list):
        issues.append(Issue("ERROR", manifest, f"{label} must be a path or an array of paths"))
        return
    for value in paths:
        target = _local_path(value, base, root, manifest, label, issues)
        if target is None:
            continue
        targets = [target] if (target / "SKILL.md").is_file() else find_skill_dirs(target)
        if not targets:
            issues.append(Issue("ERROR", manifest, f"{label} contains no skills: {value}"))
        for skill in targets:
            if skill not in known_skills:
                issues.append(Issue("ERROR", manifest, f"{label} references an undiscovered skill: {skill.relative_to(root)}"))
            if skill in registered:
                issues.append(Issue("ERROR", manifest, f"Duplicate skill registration: {skill.relative_to(root)}"))
            registered.add(skill)


def _check_coverage(manifest, root, known_skills, registered, issues):
    for skill in sorted(known_skills - registered):
        issues.append(Issue("ERROR", manifest, f"Missing skill registration: {skill.relative_to(root)}"))


def validate_marketplace(root, skill_dirs):
    """Check an optional Claude marketplace's local registration and coverage."""
    root = Path(root).resolve()
    path = root / ".claude-plugin" / "marketplace.json"
    if not path.exists():
        return []
    data, issues = _read_manifest(path)
    if data is None:
        return issues
    if not isinstance(data.get("name"), str) or not data["name"].strip():
        issues.append(Issue("ERROR", path, "Marketplace name must be a non-empty string"))
    owner = data.get("owner")
    if not isinstance(owner, dict) or not isinstance(owner.get("name"), str) or not owner["name"].strip():
        issues.append(Issue("ERROR", path, "Marketplace owner must be an object with a non-empty name"))
    plugins = data.get("plugins")
    if not isinstance(plugins, list):
        issues.append(Issue("ERROR", path, "Marketplace plugins must be an array"))
        return issues
    known_skills = {Path(skill).resolve() for skill in skill_dirs}
    registered, names = set(), set()
    for index, plugin in enumerate(plugins):
        label = f"plugins[{index}]"
        if not isinstance(plugin, dict):
            issues.append(Issue("ERROR", path, f"{label} must be an object"))
            continue
        name = plugin.get("name")
        if not isinstance(name, str) or not name.strip():
            issues.append(Issue("ERROR", path, f"{label}.name must be a non-empty string"))
        elif name in names:
            issues.append(Issue("ERROR", path, f"Duplicate plugin name: {name}"))
        else:
            names.add(name)
        if "strict" in plugin and not isinstance(plugin["strict"], bool):
            issues.append(Issue("ERROR", path, f"{label}.strict must be boolean"))
        source = _local_path(plugin.get("source"), root, root, path, f"{label}.source", issues)
        if source is None:
            continue
        paths = plugin.get("skills")
        if paths is None:
            issues.append(Issue("ERROR", path, f"{label} must explicitly declare its local skills paths"))
            continue
        _register_paths(paths, source, root, path, f"{label}.skills", known_skills, registered, issues)
    _check_coverage(path, root, known_skills, registered, issues)
    return issues


def validate_openclaw(root, skill_dirs):
    """Check an optional OpenClaw manifest's local registration and coverage."""
    root = Path(root).resolve()
    path = root / "openclaw.plugin.json"
    if not path.exists():
        return []
    data, issues = _read_manifest(path)
    if data is None:
        return issues
    if not isinstance(data.get("id"), str) or not data["id"].strip():
        issues.append(Issue("ERROR", path, "OpenClaw id must be a non-empty string"))
    if not isinstance(data.get("configSchema"), dict):
        issues.append(Issue("ERROR", path, "OpenClaw configSchema must be an object"))
    if not isinstance(data.get("skills"), list):
        issues.append(Issue("ERROR", path, "OpenClaw skills must be an array"))
        return issues
    known_skills = {Path(skill).resolve() for skill in skill_dirs}
    registered = set()
    _register_paths(data["skills"], root, root, path, "skills", known_skills, registered, issues)
    _check_coverage(path, root, known_skills, registered, issues)
    return issues


def validate_repository(root, check_manifests=True):
    """Validate portable skills first, then optionally validate platform files."""
    root = Path(root).resolve()
    skill_dirs = find_skill_dirs(root)
    issues, records = [], []
    known_skills, names = set(skill_dirs), {}
    if not skill_dirs:
        issues.append(Issue("ERROR", root, "No SKILL.md files found"))
    for skill_dir in skill_dirs:
        data, skill_issues = validate_skill(skill_dir, known_skills)
        issues.extend(skill_issues)
        if data is None:
            continue
        records.append((skill_dir, data))
        name = data.get("name")
        if isinstance(name, str):
            if name in names:
                issues.append(Issue("ERROR", skill_dir / "SKILL.md", f"Duplicate skill name {name!r}; also in {names[name].relative_to(root)}"))
            else:
                names[name] = skill_dir
    for skill_dir, data in records:
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict) or not isinstance(metadata.get("complements"), str):
            continue
        try:
            complements = json.loads(metadata["complements"])
        except json.JSONDecodeError:
            continue
        if isinstance(complements, list):
            for name in complements:
                if isinstance(name, str) and name not in names:
                    issues.append(Issue("ERROR", skill_dir / "SKILL.md", f"Unknown complementary skill: {name}"))
    if check_manifests:
        issues.extend(validate_marketplace(root, skill_dirs))
        issues.extend(validate_openclaw(root, skill_dirs))
    return ValidationResult(skill_dirs, issues)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--skills-only", action="store_true", help="Skip optional platform manifest checks")
    args = parser.parse_args(argv)
    result = validate_repository(args.root, check_manifests=not args.skills_only)
    root = args.root.resolve()
    for issue in result.issues:
        location = issue.path.relative_to(root) if issue.path.is_relative_to(root) else issue.path
        if issue.line is not None:
            location = f"{location}:{issue.line}"
        print(f"{issue.level} {location}: {issue.message}")
    print(f"Skills: {len(result.skill_dirs)}  Errors: {len(result.errors)}  Warnings: {len(result.warnings)}")
    print("FAILED" if result.errors else "PASSED")
    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
