# Platform adapter assessment

Reviewed on **2026-09-14**. The decision is to keep the portable skill content
and existing generated platform manifests, and add native Codex verification
to the evaluation harness. No additional hooks, agent registrations, or UI
configuration are justified by the observed requirements.

## Evidence and decisions

| Integration | Observed requirement or gap | Decision |
| --- | --- | --- |
| Codex native skills | Repository skills are discovered under `.agents/skills`; the previous evaluation used an explicitly supplied catalog and did not exercise that scanner. | Add a native evaluation mode, direct `skills/list` verification, and task-only prompts. No content adapter is required to expose standard `SKILL.md` files. |
| Codex optional metadata | `agents/openai.yaml` can supply UI metadata and invocation policy. Implicit invocation is enabled by default. | Do not generate redundant policy or UI files without a task requiring them. |
| Claude Code | The project already generates its marketplace manifest, and standard directory skills have a documented project installation route. Runtime evaluation is excluded from this round. | Retain the existing adapter and optional checkout configuration. Do not infer runtime success or clone its hooks into other agents. |
| OpenClaw | The project already generates `openclaw.plugin.json`. CLI 2026.1.30 exists, but the standard configuration files, agent authentication profiles and provider-auth environment variables were absent. | Retain the generated adapter and record runtime as unconfigured. No gateway/model was started, and existing Codex credentials were not repurposed to configure another agent. |
| Gemini CLI, GitHub Copilot, OpenCode, Cline, Roo and Windsurf | Executables were not found on the evaluated PATH. Some products also have IDE modes; an absent CLI does not prove the product is absent. | Record unavailable execution environments. Do not install clients, assume authentication, or invent platform settings. |

The dated [availability record](../evals/results/2026-09-14-platform-availability.json)
contains executable availability and locally observed versions without private
paths. It does not claim authentication for unavailable clients. Existing
[compatibility evidence](COMPATIBILITY.md) distinguishes documented format
support, upstream installer checks, and real agent execution.

## Native verification method

The installed Codex 0.154.0 generated the `InitializeParams`, `SkillsListParams`
and `SkillsListResponse` JSON schemas used to check the local API. The evaluator
starts a temporary app-server, initializes it, asks for `skills/list` with
`cwds: ["/workspace"]` and `forceReload: true`, then stops that process before
starting the task. No model turn or external tool call is needed to enumerate
skills. Only enabled repository skills at the exact staged paths count.

The three recorded native tasks each discovered all **48** skills with no parse
errors, then successfully read the task's relevant skill and produced accepted
outputs. All three used one immutable public-content snapshot. The LAS and
SEG-Y tasks exercised domain selection; formation evaluation exercised workflow
selection. This evidence does not require new Codex-specific metadata or hooks.

OpenClaw's version and `agent --help` were inspected with networking disabled
inside a private filesystem namespace. The installed command documents local
execution separately from gateway delivery; its available CLI alone does not
establish a configured local model. No clients or credentials were installed.

This closes the previous measurement gap between copying files and observing
the agent's own scanner. A later successful content read supplies separate
implicit-selection evidence; independent numerical checks assess the output.
See [the evaluation protocol and recorded results](AGENT_EVALUATIONS.md).

The sandbox mounts the staged skill directories read-only and does not mount
the source checkout or user skill directories. Optional repository hooks and
global plugin configuration are not imported into the evaluation. The user's
configured model is retained in private temporary configuration.

## When to add an adapter

Add platform-specific files only for a reproduced failure or an explicit
platform feature requirement. Record the target/version, failing discovery or
task evidence, the minimal change, and a rerun proving that change addresses
the problem. UI presentation, slash-command aliases, hooks and subagent
registration have separate semantics and must remain optional. A missing CLI
or credential is an environment limitation, not evidence that the portable
skill format needs a new adapter.

## Primary references

The [OpenAI skills guide](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)
documents local discovery and optional metadata. The [Codex app-server guide](https://developers.openai.com/codex/app-server/)
describes the protocol used by the installed CLI. The [Claude Code skills guide](https://code.claude.com/docs/en/skills)
documents standard project skills and its additional platform-specific behavior.
These references describe platform interfaces; the local result records remain
the evidence for this repository's actual execution.
