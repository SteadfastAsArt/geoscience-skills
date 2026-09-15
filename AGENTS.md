# Repository guidance

Geoscience Skills provides portable Agent Skills for coding assistants: 39 domain
skills, 8 workflows, and the `using-geoscience-skills` router. Shared content
follows https://agentskills.io/specification and must work without a particular
agent's hooks, slash commands, delegation API, or plugin manager.

## Layout

- `<library>/SKILL.md`: domain guidance, with local `references/` and `scripts/`.
- `workflows/<name>/SKILL.md`: multi-library workflows.
- `using-geoscience-skills/SKILL.md`: on-demand discovery and routing.
- `agents/`: optional role guides; not a portable agent registration format.
- `.claude/`: optional Claude Code configuration for this checkout.
- `.claude-plugin/marketplace.json`, `openclaw.plugin.json`: generated platform adapters.
- `docs/COMPATIBILITY.md`: installation targets, sources, and verification scope.

## Editing skills

Use the template and schema in `CONTRIBUTING.md` and `docs/SKILL_TEMPLATE.md`.
Keep standard fields at the frontmatter root. Custom project fields belong in
`metadata`, whose keys and values are strings. Encode list-valued project
metadata as JSON array strings. Preserve dependency information when migrating
formats; these declarations do not install Python packages automatically.

Describe the task and selection criteria without naming a particular assistant.
Keep entrypoints as concise as the task permits; there is no minimum line or tag
count. Load references only when relevant. Do not require unavailable companion
skills, optional commands, or subagents to complete ordinary tasks.

For scientific examples, preserve units, coordinate systems, missing-value
semantics, assumptions, and provenance. Do not silently change calculations as
part of a packaging or documentation task.

## Validation

```bash
python3 scripts/validate_skills.py
python3 scripts/sync_manifests.py --check
python3 -m unittest discover -s tests -v
```

After changing skill names, paths, or descriptions, regenerate adapters with
`python3 scripts/sync_manifests.py` and update the human-readable `SKILLS.md` index.
For installation changes, run `python3 scripts/check_installation.py`; this uses
the upstream skills CLI in temporary projects and requires Node.js and network
access. It does not exercise each coding agent's model or the scientific stack.

Keep platform-specific enhancements optional. Document whether a compatibility
claim is based on the shared specification, upstream installer support, a local
installation check, or an actual agent task run.

For scientific code or example changes, use the separate core/modelling
environments and relevant tests described in `docs/SCIENTIFIC_TESTING.md`.
Preserve user-level packages and skills; install test dependencies only in
isolated environments. Scientific checks must fail on missing dependencies,
not report skipped examples as validated results.
