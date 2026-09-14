---
name: library-name
description: Describe the capability and the specific user tasks that should select it.
license: MIT
metadata:
  version: "1.0.0"
  author: Geoscience Skills
  skill_type: domain
  tags: '["Domain", "Library Name"]'
  dependencies: '["package>=1.0.0"]'
  complements: '[]'
  workflow_role: analysis
---

# Library Name

State the intended result and the non-obvious constraints needed to obtain it.
Replace the scaffold text with concrete guidance before registering the skill.

## When to use

Explain the task boundary and relevant alternatives. Do not depend on a named
coding agent, a slash command, a session hook, or a delegation tool.

## Inputs and conventions

Specify the required data, units, coordinate/index conventions, and any
environment requirements. Explain how missing inputs affect the task.

## Workflow

Describe the useful decision points and steps. Include a minimal runnable
example when it clarifies the operation, or explicitly label a data-dependent
fragment. Skip stages that the user's existing inputs already satisfy.

## Validation and outputs

Specify observable output types and correctness checks, including scientific
assumptions and failure conditions. Record meaningful provenance.

## References and scripts

Link only resources that exist, using paths relative to this directory, and
explain when to read or run each one. Remove this section if none are needed.
