# Roadmap

## Planned Skills

| Library | Domain | Stars | Priority |
|---------|--------|-------|----------|
| flopy | Groundwater Modelling (MODFLOW) | 600+ | High |
| pygmt | Generic Mapping Tools | 800+ | High |
| discretize | Mesh generation for SimPEG | 200+ | Medium |
| segysak | SEG-Y with xarray integration | 100+ | Medium |
| geolime | Mining geology & block models | 50+ | Medium |
| pyleoclim | Paleoclimate time series | 200+ | Medium |
| rockhound | Sample geoscience datasets | 50+ | Low |
| boule | Reference ellipsoids & gravity | 100+ | Low |
| ensaio | Geoscience sample datasets | 50+ | Low |

## Infrastructure

### In Progress
- GitHub Actions CI for skill validation

### Planned
- npm CLI installer (`npx geoscience-skills install <skill>`)
- Automated skill quality scoring
- Integration testing with sample data files

### Future Workflows & Agents
- Hydrogeological workflow (pastas + well logs)
- Near-surface geophysics workflow (GPR + ERT + MT)
- Climate data analysis workflow (xarray + verde)
- Cross-validation agent for model quality assessment

### Completed
- v2.2.0: Added workflow skills, agents, slash commands, and SessionStart hook
- v2.2.0: Enriched all 29 skill frontmatter with complements and workflow_role fields
- v2.0.0: Standardized all 29 skills to Anthropic skill format
- v2.0.0: Added YAML frontmatter with 7 required fields
- v2.0.0: Added workflow checklists and "when to use vs alternatives" sections
- v1.0.0: Initial release with 29 geoscience skills

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to add a new skill.
