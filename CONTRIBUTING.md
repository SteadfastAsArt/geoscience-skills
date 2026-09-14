# Contributing to Geoscience Skills

Build skills that improve geoscience tasks across coding agents. Use the
[Agent Skills specification](https://agentskills.io/specification) as the shared
format; keep platform integrations separate. See [AGENTS.md](AGENTS.md) for
repository guidance and [compatibility](docs/COMPATIBILITY.md) for installation.

## Add or update a skill

1. Create `<name>/SKILL.md`, or `workflows/<name>/SKILL.md` for a workflow. The
   directory name must match the frontmatter `name`.
2. Start from [the template](docs/SKILL_TEMPLATE.md). Add only references and
   scripts that help with real tasks, and link resources from the skill.
3. Include when to use the skill, relevant alternatives, necessary inputs,
   operational constraints, and observable completion criteria.
4. Add the skill to [SKILLS.md](SKILLS.md). Update the router's domain or workflow
   table when it adds a new routing choice.
5. Run `python3 scripts/sync_manifests.py` to regenerate platform adapters from
   the skill files. Do not maintain separate copies of their descriptions.
6. Run the checks below, then submit a pull request describing behavior and
   validation. Bump `metadata.version` when changing an existing skill.

## Frontmatter

```yaml
---
name: example-library
description: Read and validate Example files. Use when inspecting headers or converting Example data to arrays.
license: MIT
metadata:
  version: "1.0.0"
  author: Geoscience Skills
  skill_type: domain
  tags: '["Data I/O", "Example"]'
  dependencies: '["example-library>=1.0"]'
  complements: '[]'
  workflow_role: data-loading
---
```

`name` and `description` are required by the shared format. Supported optional
root fields are `license`, `compatibility`, `metadata`, and `allowed-tools`.
Names use lowercase letters, digits, and single hyphens, up to 64 characters;
descriptions are nonempty and at most 1024 characters. Avoid agent-specific
tool restrictions in shared skills.

All `metadata` values must be strings. Project list fields (`tags`,
`dependencies`, `complements`) use JSON arrays encoded as YAML strings. This
keeps richer project information without requiring agents to understand custom
top-level fields. Dependencies document Python requirements; skill installation
does not install or verify those packages.

Project conventions:

| Metadata field | Meaning |
|---|---|
| `version` | Skill revision, as a quoted semantic version |
| `author` | Maintainer attribution |
| `skill_type` | `domain`, `workflow`, or `meta` |
| `tags` | Relevant concepts; no minimum number |
| `dependencies` | Python requirements for the documented operations |
| `complements` | Related skill names; optional, not automatically installed |
| `workflow_role` | `data-loading`, `processing`, `analysis`, `modelling`, or `visualization` |

## Content and portability

- Use neutral wording such as "the agent" or describe the task directly.
- Keep the entrypoint short enough to load usefully. There is no minimum length;
  keep it under 500 lines and put conditional detail in linked references.
- Give code fences language tags, including `text` for checklists or diagrams.
- Distinguish runnable examples from fragments that require user data.
- Resolve resource paths relative to the skill directory, not the user's cwd.
- Workflows select stages according to the user's task and available inputs;
  file loading, plotting, and delegation are not mandatory for every task.
- Use a companion skill when available. If it is missing, use the available
  tools and authoritative documentation, or explain the specific missing
  capability. Do not claim to invoke unavailable skills or agents.
- Declare units, array/index conventions, CRS and vertical reference where
  relevant. Check outputs using meaningful scientific invariants.

## Checks

```bash
python3 -m pip install pyyaml
python3 scripts/validate_skills.py
python3 scripts/sync_manifests.py --check
python3 -m unittest discover -s tests -v
```

The validator discovers domain, workflow, and routing skills recursively. It
checks portable frontmatter and resources, and validates platform manifests
separately when present. Structural validation does not establish scientific
correctness or that an agent will select a skill for a particular prompt.

For changes to scientific examples or processing scripts, also run the relevant
[scientific checks](docs/SCIENTIFIC_TESTING.md) in an isolated environment. Add
small generated inputs and assert known numerical results, missing-value
semantics, units, or exported coordinates. Prefer executing the documented
example over copying its formula into a test.

For installation or layout changes:

```bash
python3 scripts/check_installation.py
```

This installs through a pinned upstream `skills` CLI in temporary projects and
checks that all skills and resources arrive intact. It requires Node.js and
network access. Agent task evaluations are separate from installation checks.
Use the [evaluation guide](docs/AGENT_EVALUATIONS.md) for free fixture/acceptance
tests and recorded CLI runs. When updating verification claims, link the checked
revision and result, and distinguish explicit skill reading from native activation.

For dependency maintenance, use the [read-only version report](docs/DEPENDENCY_MAINTENANCE.md)
and validate proposed upgrades in an isolated environment before changing pins.

## Platform extensions

Keep optional command aliases, hooks, and agent registrations out of shared
skill instructions. The `.claude/` configuration is specific to Claude Code;
the Markdown role guides in `agents/` can be read explicitly but are not
automatically registered by a generic skills installer.

When adding another platform, verify its current official requirements, link
the source in `docs/COMPATIBILITY.md`, and test the relevant installation path.
Do not describe installer support as proof of end-to-end agent behavior.
