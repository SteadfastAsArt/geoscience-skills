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
- Enriched tag metadata for better discoverability

### Planned
- npm CLI installer (`npx geoscience-skills install <skill>`)
- Automated skill quality scoring
- Integration testing with sample data files

### Completed
- v2.0.0: Standardized all 29 skills to Anthropic skill format
- v2.0.0: Added YAML frontmatter with 7 required fields
- v2.0.0: Added workflow checklists and "when to use vs alternatives" sections
- v1.0.0: Initial release with 29 geoscience skills

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to add a new skill.
