# Contributing to Geoscience Skills

Thank you for contributing to the Geoscience Skills library! This guide covers everything you need to add or improve skills.

## Quick Start

1. Fork and clone the repository
2. Create a branch: `git checkout -b add-skill-name`
3. Add your skill following the structure below
4. Run validation: `python3 scripts/validate_skills.py`
5. Submit a pull request

## Adding a New Skill

### 1. Create Directory Structure

```
skill-name/
├── SKILL.md              # Main guidance (200-300 lines)
├── references/           # Deep documentation
│   ├── topic1.md         # Specific reference topic
│   └── topic2.md         # Another reference topic
└── scripts/              # Helper scripts (optional)
    └── example.py        # Utility script
```

### 2. Write SKILL.md

Start with the YAML frontmatter (all 7 fields required):

```yaml
---
name: library-name
description: |
  Third-person description of what this skill does and when to use it.
  Include key terms for discovery. Use when Claude needs to: (1) ...,
  (2) ..., (3) ...
version: 1.0.0
author: Geoscience Skills
license: MIT
tags: [Domain, Library Name, Key Concept, Method, Format, Application, Technique]
dependencies: [package>=1.0.0]
---
```

Then structure the body with these sections:

```markdown
# Library Name - Short Description

## Quick Reference
## Key Classes
## Essential Operations
## When to use vs alternatives
## Common workflows
## Common Issues
## References
```

See [docs/SKILL_TEMPLATE.md](docs/SKILL_TEMPLATE.md) for a complete template.

### 3. Register the Skill

Update these files:

- **SKILLS.md** - Add to the appropriate category table and star-count ranking
- **.claude-plugin/marketplace.json** - Add entry to `plugins[]` array and to the appropriate `categories[]` group

### 4. Validate

```bash
python3 scripts/validate_skills.py
```

## Quality Standards

### YAML Frontmatter

All 7 fields are required:

| Field | Format | Example |
|-------|--------|---------|
| `name` | lowercase library name | `lasio` |
| `description` | Multi-line, third person, includes WHAT and WHEN | See template |
| `version` | Semantic versioning | `1.0.0` |
| `author` | `Geoscience Skills` | `Geoscience Skills` |
| `license` | `MIT` | `MIT` |
| `tags` | Array, 7+ items | `[Well Logs, LAS, ...]` |
| `dependencies` | Array with version specs | `[lasio>=0.30]` |

### Content Requirements

| Criterion | Requirement |
|-----------|-------------|
| SKILL.md body length | 150-500 lines (target 200-300) |
| "When to use vs alternatives" section | Required |
| Workflow checklists | Required for multi-step operations |
| Common issues section | Required |
| Code block language tags | All code blocks must have tags (`python`, `bash`) |
| References depth | ONE level deep from SKILL.md |
| Tone | Third person, concise, no over-explaining |

### Checklist Before Submitting

```
- [ ] SKILL.md has valid YAML frontmatter with all 7 fields
- [ ] SKILL.md is 150-500 lines (target 200-300)
- [ ] "When to use vs alternatives" section exists
- [ ] All code blocks have language tags
- [ ] Tags array has 7+ entries
- [ ] Skill registered in SKILLS.md
- [ ] Skill registered in .claude-plugin/marketplace.json (plugins + categories)
- [ ] python3 scripts/validate_skills.py passes
```

## Tag Conventions

- Use **Title Case** for words: `Well Logs`, `Spatial Analysis`
- Use **UPPERCASE** for acronyms: `ERT`, `GPR`, `MT`, `AVO`, `SEG-Y`
- Include at minimum:
  - Domain name (e.g., `Seismology`, `Petrophysics`)
  - Library name (e.g., `ObsPy`, `Lasio`)
  - Key methods/concepts (e.g., `Kriging`, `Fluid Substitution`)
  - Data formats if applicable (e.g., `LAS`, `DLIS`, `SEG-Y`)
  - Application area (e.g., `Well Logs`, `Near-Surface`)
- Target 7+ tags per skill for discoverability

## Code Style

- All code examples use language tags: ` ```python `, ` ```bash `
- Examples should be concise and runnable
- Include imports in examples
- Use realistic geoscience variable names (not `x`, `y`, `foo`)
- Show expected output shapes/types where helpful

## Improving Existing Skills

1. Keep SKILL.md under 500 lines; split into reference files if needed
2. Maintain YAML frontmatter format and all 7 fields
3. Bump the `version` field in YAML frontmatter
4. Ensure "When to use vs alternatives" section exists
5. Run `python3 scripts/validate_skills.py` before submitting

## Reference Files

- Place in `skill-name/references/`
- One level deep only (no nested references)
- Cover advanced topics, detailed API docs, or edge cases
- Link from SKILL.md: `**[Topic](references/topic.md)** - Description`

## Getting Help

- Open an [issue](https://github.com/SteadfastAsArt/geoscience-skills/issues)
- See [SKILLS.md](SKILLS.md) for existing skills and categories
- See [docs/ROADMAP.md](docs/ROADMAP.md) for planned skills
