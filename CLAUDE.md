# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Geoscience Skills Library** - A comprehensive open-source library of 29 geoscience skills for AI coding assistants. Each skill provides expert-level guidance for Python geoscience libraries, covering seismic processing, well log analysis, geological modelling, geophysical inversion, geostatistics, and more.

**Mission**: Enable AI coding agents to assist geoscientists with domain-specific Python workflows, from data loading to interpretation and visualization.

## Repository Architecture

### Directory Structure (29 Skills Across 17 Domains)

Skills are organized by Python library name in a flat directory structure:

- **Seismic & Seismology**: `obspy/`, `segyio/`, `disba/`
- **Well Log Analysis**: `lasio/`, `welly/`, `dlisio/`, `striplog/`, `petropy/`
- **3D Geological Modelling**: `gempy/`, `loopstructural/`, `gemgis/`
- **Geophysical Inversion**: `simpeg/`, `devito/`, `pylops/`, `pygimli/`
- **Potential Fields**: `harmonica/`
- **Rock Physics**: `bruges/`
- **Geostatistics & Spatial**: `verde/`, `geostatspy/`, `scikit-gstat/`
- **Hydrology**: `pastas/`
- **Surface Processes**: `landlab/`
- **Structural Geology**: `mplstereonet/`
- **Geochemistry**: `pyrolite/`
- **Near-Surface Geophysics**: `gprpy/`, `mtpy/`
- **Data Formats**: `xarray/`
- **Visualization**: `pyvista/`
- **Utilities**: `pooch/`

### Skill File Structure

Each skill follows a standardized format:
```
skill-name/
├── SKILL.md              # Main guidance (200-300 lines with YAML frontmatter)
├── references/           # Deep documentation (one level deep)
│   ├── topic1.md         # Specific reference topic
│   └── topic2.md         # Another reference topic
└── scripts/              # Helper scripts (optional)
    └── example.py        # Utility script
```

## Skill Quality Standards

### YAML Frontmatter Requirements

All `SKILL.md` files MUST include YAML frontmatter with these fields:

```yaml
---
name: library-name
description: |
  Description of what AND when to use this skill. Include key terms
  and triggers for discovery.
version: 1.0.0
author: Geoscience Skills
license: MIT
tags: [Domain, Library Name, Key Concept]
dependencies: [package>=1.0.0]
---
```

### Content Quality Standards

Based on Anthropic official best practices:
- SKILL.md body: **200-300 lines** (under 500 lines maximum)
- Progressive disclosure: SKILL.md as overview, details in reference files
- "When to use vs alternatives" section required
- Workflow checklists for multi-step operations
- Common issues section with solutions
- Concise content: assume Claude is smart, no over-explaining basics
- Code examples with language tags (`python`, `bash`)
- References ONE level deep from SKILL.md

### Not Acceptable

- SKILL.md over 500 lines
- Over-explaining basics that Claude already knows
- First-person descriptions
- Nested references (SKILL.md -> ref1.md -> ref2.md)
- Missing "when to use vs alternatives" section

## Development Workflow

### Adding a New Skill

1. Create `skill-name/SKILL.md` with YAML frontmatter following standards
2. Add reference files in `skill-name/references/`
3. Add helper scripts in `skill-name/scripts/` (optional)
4. Update `SKILLS.md` with the new skill entry
5. Add entry to `.claude-plugin/marketplace.json`
6. Validate: SKILL.md is 200-300 lines, YAML parses correctly

### Improving Existing Skills

1. Keep SKILL.md under 500 lines - split into reference files if needed
2. Maintain YAML frontmatter format and all fields
3. Update version number in YAML frontmatter
4. Ensure "when to use vs alternatives" section exists

### Quality Validation

```bash
# Check YAML frontmatter
head -20 skill-name/SKILL.md

# Verify line count (target 200-300)
wc -l skill-name/SKILL.md

# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('skill-name/SKILL.md').read().split('---')[1])"

# Check code blocks have language tags
grep -A 1 '```' skill-name/SKILL.md | head -20
```

## Key Files

- **README.md** - Project overview and installation guide
- **SKILLS.md** - Complete skill reference with categories and stars
- **CLAUDE.md** - This file: repo guidance for AI agents
- **docs/SKILL_TEMPLATE.md** - Template for creating new skills
- **.claude-plugin/marketplace.json** - Plugin marketplace registration

## Conventions

- Skill directories use Python library names (lowercase): `lasio/`, `obspy/`
- Tags use Title Case for words, UPPERCASE for acronyms (ERT, GPR, MT, AVO)
- Descriptions are third person and include WHAT it does and WHEN to use it
- All code examples include language tags
- References are one level deep from SKILL.md
