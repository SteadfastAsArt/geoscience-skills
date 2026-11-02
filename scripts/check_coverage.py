#!/usr/bin/env python3
"""Validate declared scientific coverage and render its user-facing matrix.

This checks inventory and evidence links; it never runs scientific tests or
upgrades a declared test mapping into a successful runtime verification claim.
"""

import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

if __package__:
    from .validate_skills import find_skill_dirs, parse_frontmatter
else:
    from validate_skills import find_skill_dirs, parse_frontmatter


REGISTRY = Path("tests/skill_coverage.json")
MATRIX = Path("docs/VALIDATION_MATRIX.md")


def project_file(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError(f"Invalid project path: {relative!r}")
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Path must stay inside the project: {relative}")
    result = root / path
    if not result.resolve().is_relative_to(root.resolve()) or not result.is_file():
        raise ValueError(f"Missing or external project file: {relative}")
    return result


def skill_files(directory):
    """Match the public-file filter used when staging native evaluations."""
    return [p for p in sorted(directory.rglob("*")) if p.is_file() and not p.is_symlink()
            and not any(part.startswith(".") or part == "__pycache__"
                        for part in p.relative_to(directory).parts)]


def bundle_hash(directory):
    checksum = hashlib.sha256()
    for path in skill_files(directory):
        checksum.update(path.relative_to(directory).as_posix().encode() + b"\0")
        checksum.update(hashlib.sha256(path.read_bytes()).digest())
    return checksum.hexdigest()


def check_ids(value, suites, label):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"{label}: checks must be a list of suite IDs")
    if len(value) != len(set(value)) or set(value) - suites.keys():
        raise ValueError(f"{label}: duplicate or unknown suite IDs")


def validate(root, registry):
    root = Path(root).resolve()
    if not isinstance(registry, dict) or registry.get("schema_version") != 1:
        raise ValueError("Unsupported coverage schema_version")
    environments, suites, entries = (registry.get(k) for k in ("environments", "suites", "skills"))
    if not all(isinstance(value, dict) and value for value in (environments, suites, entries)):
        raise ValueError("Coverage needs nonempty environments, suites and skills mappings")
    for name in (*environments, *suites):
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", name):
            raise ValueError(f"Invalid environment or suite ID: {name!r}")
    for name, environment in environments.items():
        if not isinstance(environment, dict) or not re.fullmatch(r"3\.\d+", environment.get("python", "")):
            raise ValueError(f"{name}: declare a Python major.minor")
        project_file(root, environment.get("requirements"))
        if not isinstance(environment.get("setup"), str) or not environment["setup"].strip():
            raise ValueError(f"{name}: describe environment/external-executable setup")
    paths = []
    for name, suite in suites.items():
        if not isinstance(suite, dict) or suite.get("environment") not in environments:
            raise ValueError(f"{name}: unknown environment")
        path = project_file(root, suite.get("path"))
        if path.suffix != ".py" or not path.name.startswith("test_"):
            raise ValueError(f"{name}: expected a Python test suite")
        tree = ast.parse(path.read_text())
        if not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
                   for node in ast.walk(tree)):
            raise ValueError(f"{name}: suite has no test functions")
        paths.append(suite["path"])
    if len(paths) != len(set(paths)):
        raise ValueError("A suite path is registered more than once")
    discovered_suites = {p.relative_to(root).as_posix() for p in (root / "tests/science").glob("test_*.py")}
    if discovered_suites - set(paths):
        raise ValueError(f"Scientific suites missing from coverage: {sorted(discovered_suites - set(paths))}")
    inventory = {parse_frontmatter((p / "SKILL.md").read_text())["name"]: p for p in find_skill_dirs(root)}
    if set(entries) != set(inventory):
        raise ValueError(f"Skill coverage mismatch; missing={sorted(set(inventory) - set(entries))}; "
                         f"unknown={sorted(set(entries) - set(inventory))}")
    for name, directory in inventory.items():
        entry = entries[name]
        if not isinstance(entry, dict) or not isinstance(entry.get("scope"), str) or not entry["scope"].strip():
            raise ValueError(f"{name}: explain the tested scope or missing coverage")
        check_ids(entry.get("checks"), suites, name)
        scripts = entry.get("scripts")
        if not isinstance(scripts, dict):
            raise ValueError(f"{name}: scripts must be a mapping")
        shipped = {p.relative_to(directory).as_posix() for p in skill_files(directory)
                   if p.relative_to(directory).parts[0] == "scripts" and p.suffix in (".py", ".sh", ".js", ".mjs")}
        if set(scripts) != shipped:
            raise ValueError(f"{name}: script coverage mismatch; missing={sorted(shipped - set(scripts))}; "
                             f"unknown={sorted(set(scripts) - shipped)}")
        for relative, record in scripts.items():
            if not isinstance(record, dict) or set(record) not in ({"checks"}, {"gap"}):
                raise ValueError(f"{name}/{relative}: declare either checks or a specific gap")
            if "checks" in record:
                check_ids(record["checks"], suites, f"{name}/{relative}")
                if not record["checks"] or set(record["checks"]) - set(entry["checks"]):
                    raise ValueError(f"{name}/{relative}: script checks must be nonempty and listed for the skill")
            elif not isinstance(record["gap"], str) or not record["gap"].strip():
                raise ValueError(f"{name}/{relative}: empty coverage gap")
    return inventory


def native_evidence(root, inventory):
    evidence = {name: [] for name in inventory}
    hashes = {name: bundle_hash(directory) for name, directory in inventory.items()}
    for path in sorted((root / "evals/results").glob("*.json")):
        report = json.loads(path.read_text())
        if not isinstance(report, dict) or report.get("evaluation_mode") != "native":
            continue
        for result in report.get("results", []):
            if result.get("status") != "passed" or result.get("native_activation_verified") is not True:
                continue
            if (result.get("exit_code") != 0 or result.get("numerical_checks", {}).get("passed") is not True
                    or result.get("native_discovery", {}).get("passed") is not True):
                continue
            expected = result.get("expected_skill")
            if expected not in inventory or expected not in result.get("observed_skill_reads", []):
                continue
            matches = result.get("installed_bundle_hashes", {}).get(expected) == hashes[expected]
            evidence[expected].append({"report": path.relative_to(root).as_posix(),
                                       "matches_current_bundle": matches,
                                       "task": result.get("task", "recorded task")})
    return evidence


def markdown(root, registry, inventory):
    evidence = native_evidence(root, inventory)
    mapped = sum("checks" in record for entry in registry["skills"].values() for record in entry["scripts"].values())
    total = sum(len(entry["scripts"]) for entry in registry["skills"].values())
    lines = ["# Skill validation matrix", "", "Generated by `python3 scripts/check_coverage.py --write` from",
             "[the coverage registry](../tests/skill_coverage.json). Do not edit this table manually.", "",
             f"Inventory: **{len(inventory)} skills**, **{total} bundled scripts**, **{mapped} scripts with declared execution tests**,",
             f"**{total - mapped} explicit script coverage gaps**.", "",
             "A test mapping identifies intended coverage, not a passing run or whole-library certification.",
             "A registered suite may execute selected skill examples, a workflow branch or related field-data checks;",
             "read the scope column. Scripts are mapped separately so a library test cannot conceal an untested CLI.",
             "See [scientific testing](SCIENTIFIC_TESTING.md) and CI for executed revisions and environments.", "",
             "Native evidence is limited to the recorded task, agent/model and environment. Bundle matching checks",
             "the selected skill's current public files; it does not rerun the task or establish skill benefit.",
             "Unlisted tasks and changed bundles retain no current native-task claim.", "",
             "| Skill | Scientific checks | Script mappings | Native task evidence | Scope / limitations |",
             "| --- | --- | --- | --- | --- |"]
    def clean(value):
        return " ".join(value.split()).replace("|", "\\|")
    for name, directory in sorted(inventory.items()):
        entry = registry["skills"][name]
        checks = ", ".join(f"[{sid}](../{registry['suites'][sid]['path']})" for sid in entry["checks"]) or "Not mapped"
        scripts = entry["scripts"]
        count = sum("checks" in item for item in scripts.values())
        script_status = f"{count}/{len(scripts)}" if scripts else "No scripts"
        native = "; ".join(f"[{item['task']}](../{item['report']}) ({'matching bundle' if item['matches_current_bundle'] else 'historical; bundle changed'})"
                           for item in evidence[name]) or "Not recorded"
        link = directory.relative_to(root).as_posix() + "/SKILL.md"
        lines.append(f"| [{name}](../{link}) | {checks} | {script_status} | {native} | {clean(entry['scope'])} |")
    lines += ["", "## Script coverage gaps", "", "These explicit gaps keep untested helpers visible. Adding a script without a test mapping",
              "or a specific gap fails the inventory check. Recording a gap does not validate the script.", "",
              "| Script | Missing execution evidence |", "| --- | --- |"]
    for name, directory in sorted(inventory.items()):
        for relative, record in sorted(registry["skills"][name]["scripts"].items()):
            if "gap" in record:
                path = directory.relative_to(root).as_posix() + "/" + relative
                lines.append(f"| [{name}/{relative}](../{path}) | {clean(record['gap'])} |")
    lines += ["", "## Isolated environments", "", "Use an existing environment; the runner does not install packages or external programs.", "",
              "```bash", "python3 scripts/run_science.py --environment geostatistics \\",
              "  --python /path/to/isolated-venv/bin/python --report /tmp/geostatistics-run.json", "```", "",
              "| Environment | Python | Requirements | Setup |", "| --- | --- | --- | --- |"]
    for name, environment in sorted(registry["environments"].items()):
        lines.append(f"| {name} | {environment['python']} | [baseline](../{environment['requirements']}) | {clean(environment['setup'])} |")
    return "\n".join(lines) + "\n"


def load_registry(root):
    registry = json.loads((root / REGISTRY).read_text())
    return registry, validate(root, registry)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Regenerate the matrix after validating mappings")
    mode.add_argument("--check", action="store_true", help="Check registry and generated matrix (default)")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        registry, inventory = load_registry(root)
        expected = markdown(root, registry, inventory)
        target = root / MATRIX
        if args.write:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(expected)
        elif not target.is_file() or target.read_text() != expected:
            raise ValueError("Validation matrix is stale; run scripts/check_coverage.py --write")
        scripts = [r for entry in registry["skills"].values() for r in entry["scripts"].values()]
        print(f"Coverage inventory: {len(inventory)} skills; {sum('checks' in r for r in scripts)}/{len(scripts)} "
              f"scripts mapped to tests; {sum('gap' in r for r in scripts)} explicit gaps. No scientific tests executed.")
        return 0
    except (OSError, ValueError, TypeError, KeyError, SyntaxError) as error:
        print(f"Coverage check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
