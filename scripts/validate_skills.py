#!/usr/bin/env python3
"""Validate all geoscience skills against quality standards."""

import json
import re
import sys
from pathlib import Path

REQUIRED_FRONTMATTER_FIELDS = [
    "name", "description", "version", "author", "license", "tags", "dependencies"
]
MIN_LINES = 150
MAX_LINES = 500
MIN_TAGS = 7

# Directories that are not skills
SKIP_DIRS = {
    ".claude-plugin", ".git", ".github", "docs", "scripts",
    "node_modules", "__pycache__",
}


def parse_frontmatter(text):
    """Extract YAML frontmatter from markdown text."""
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        import yaml
        return yaml.safe_load(parts[1])
    except Exception as e:
        return {"_error": str(e)}


def find_skill_dirs(root):
    """Find all skill directories (contain SKILL.md)."""
    skill_dirs = []
    for d in sorted(root.iterdir()):
        if d.is_dir() and d.name not in SKIP_DIRS and not d.name.startswith("."):
            skill_md = d / "SKILL.md"
            if skill_md.exists():
                skill_dirs.append(d)
    return skill_dirs


def validate_skill(skill_dir):
    """Validate a single skill. Returns list of (level, message) tuples."""
    issues = []
    skill_md = skill_dir / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    lines = text.splitlines()
    line_count = len(lines)

    # YAML frontmatter
    fm = parse_frontmatter(text)
    if fm is None:
        issues.append(("ERROR", "Missing YAML frontmatter"))
        return issues
    if "_error" in fm:
        issues.append(("ERROR", f"Invalid YAML: {fm['_error']}"))
        return issues

    for field in REQUIRED_FRONTMATTER_FIELDS:
        if field not in fm:
            issues.append(("ERROR", f"Missing frontmatter field: {field}"))

    # Tags count
    tags = fm.get("tags", [])
    if isinstance(tags, list) and len(tags) < MIN_TAGS:
        issues.append(("WARN", f"Only {len(tags)} tags (recommend {MIN_TAGS}+)"))

    # Line count
    if line_count < MIN_LINES:
        issues.append(("WARN", f"Only {line_count} lines (minimum {MIN_LINES})"))
    elif line_count > MAX_LINES:
        issues.append(("ERROR", f"{line_count} lines exceeds maximum {MAX_LINES}"))

    # Code block language tags
    code_block_pattern = re.compile(r"^```(\w*)$", re.MULTILINE)
    for match in code_block_pattern.finditer(text):
        if not match.group(1):
            line_num = text[:match.start()].count("\n") + 1
            issues.append(("WARN", f"Code block without language tag at line {line_num}"))

    # "When to use" section
    if "when to use" not in text.lower():
        issues.append(("WARN", "Missing 'When to use vs alternatives' section"))

    return issues


def validate_marketplace(root, skill_names):
    """Validate marketplace.json references all skills."""
    issues = []
    mp_path = root / ".claude-plugin" / "marketplace.json"
    if not mp_path.exists():
        issues.append(("ERROR", "Missing .claude-plugin/marketplace.json"))
        return issues

    try:
        data = json.loads(mp_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        issues.append(("ERROR", f"Invalid JSON: {e}"))
        return issues

    plugin_names = {p["name"] for p in data.get("plugins", [])}
    for skill in skill_names:
        if skill not in plugin_names:
            issues.append(("ERROR", f"Skill '{skill}' not in marketplace.json plugins"))

    for plugin in plugin_names:
        if plugin not in skill_names:
            issues.append(("WARN", f"Plugin '{plugin}' in marketplace.json but no skill directory found"))

    return issues


def main():
    root = Path(__file__).resolve().parent.parent
    skill_dirs = find_skill_dirs(root)

    if not skill_dirs:
        print("ERROR: No skill directories found")
        sys.exit(1)

    print(f"Found {len(skill_dirs)} skills\n")

    total_errors = 0
    total_warnings = 0

    for skill_dir in skill_dirs:
        issues = validate_skill(skill_dir)
        errors = [i for i in issues if i[0] == "ERROR"]
        warnings = [i for i in issues if i[0] == "WARN"]
        total_errors += len(errors)
        total_warnings += len(warnings)

        if issues:
            status = "FAIL" if errors else "WARN"
            print(f"  {status}  {skill_dir.name}")
            for level, msg in issues:
                print(f"        {level}: {msg}")
        else:
            print(f"  PASS  {skill_dir.name}")

    # Marketplace validation
    skill_names = {d.name for d in skill_dirs}
    mp_issues = validate_marketplace(root, skill_names)
    mp_errors = [i for i in mp_issues if i[0] == "ERROR"]
    mp_warnings = [i for i in mp_issues if i[0] == "WARN"]
    total_errors += len(mp_errors)
    total_warnings += len(mp_warnings)

    print(f"\nMarketplace:")
    if mp_issues:
        for level, msg in mp_issues:
            print(f"  {level}: {msg}")
    else:
        print("  PASS")

    # Summary
    print(f"\n{'='*50}")
    print(f"Skills: {len(skill_dirs)}  Errors: {total_errors}  Warnings: {total_warnings}")

    if total_errors > 0:
        print("FAILED")
        sys.exit(1)
    else:
        print("PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
