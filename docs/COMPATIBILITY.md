# Coding Agent Compatibility

Vendor documentation reviewed: **2026-09-11**.
Project verification recorded: **2026-09-14**.

Geoscience Skills uses the open Agent Skills format so the same scientific
instructions can be installed in multiple coding agents. The portable collection
contains **48 skills**: 39 domain skills, eight workflow skills, and the
`using-geoscience-skills` discovery skill. Agent-specific integrations are optional.

## Install with the upstream skills CLI

Use the [Vercel Labs skills CLI](https://github.com/vercel-labs/skills) from the
project where you want to use these skills. Node.js/npm and Git must be available.

```bash
# Inspect the available skills without installing them.
npx skills add SteadfastAsArt/geoscience-skills --full-depth --list

# Choose skills and agents interactively.
npx skills add SteadfastAsArt/geoscience-skills --full-depth

# Install a small starting set for Codex and Claude Code.
npx skills add SteadfastAsArt/geoscience-skills --full-depth \
  --skill using-geoscience-skills lasio segyio --agent codex claude-code

# Install the complete collection for one agent.
npx skills add SteadfastAsArt/geoscience-skills --full-depth \
  --skill '*' --agent codex

# Inspect installed skills.
npx skills list
```

Keep `--full-depth`: this repository retains domain directories at its root and
eight workflow directories under `workflows/`. A source checkout can also be
installed by replacing `SteadfastAsArt/geoscience-skills` with its local path.

Installation is project-scoped by default. Add `--global` for user scope or
`--copy` for independent copies. The installer manages each agent's destination;
use its current [supported-agent list](https://github.com/vercel-labs/skills#supported-agents)
instead of maintaining a separate path mapping. Install the domain skills named
by a workflow as well: selecting a workflow does not install its related skills
or Python packages automatically.

## Agent matrix

The `--agent` identifiers below are listed by the upstream installer. A native
skills feature documented by an agent establishes format support; it does not
establish that this project's scientific workflows have been run in that agent.

| Agent | `--agent` identifier | Native skill support and usage notes |
| --- | --- | --- |
| Codex | `codex` | Reads skill names/descriptions and loads instructions when selected; scripts and references are supported. See [OpenAI's Build skills guide](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills). |
| Claude Code | `claude-code` | Supports standard skills and its own additional skill/plugin features. See [Claude Code skills](https://code.claude.com/docs/en/skills). |
| GitHub Copilot | `github-copilot` | Agent Skills are documented for several Copilot clients, including CLI and IDE agent modes. Check the relevant client and repository settings. See [GitHub Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills). |
| Gemini CLI | `gemini-cli` | Supports skill discovery and activation. Use `/skills list` and `/skills reload` to inspect or refresh the session; activation follows Gemini's consent flow. See [Gemini CLI skills](https://geminicli.com/docs/cli/skills/). |
| Windsurf / Cascade | `windsurf` | Supports `SKILL.md` plus supporting files and explicit `@skill-name` invocation. The [official Cascade skills page](https://docs.windsurf.com/windsurf/cascade/skills) currently redirects to Devin Desktop documentation. |
| OpenCode | `opencode` | Loads skills through its native `skill` tool; permissions can hide or restrict a skill. See [OpenCode Agent Skills](https://opencode.ai/docs/skills/). |
| Cline | `cline` | Supports skill discovery and individual enable/disable controls. See [Cline skills](https://docs.cline.bot/customization/skills). |
| Roo Code | `roo` | Supports progressive loading and bundled resources; skill names must match their containing directory. See [Roo Code skills](https://roocodeinc.github.io/Roo-Code/features/skills/). |
| OpenClaw | `openclaw` | Documents the Agent Skills format and workspace/user skills. Runtime execution depends on the configured agent environment. See [OpenClaw skills](https://docs.openclaw.ai/tools/skills). |
| Other upstream targets | See the upstream list | Additional installer targets are available. This project does not individually certify their discovery, permissions, or task execution. |
| NanoClaw | Not assessed | No native installation or runtime compatibility claim is made in this release. Use the manual reading fallback if the agent can access repository files. |

For Codex, the older `developers.openai.com/codex/skills/` documentation entry
currently redirects to the linked OpenAI guide. That guide still explicitly
documents Codex's local skill loading. For platform-specific installation or
cloud deployment, follow the current vendor documentation linked above.

## What is portable

Each installable skill is a directory containing `SKILL.md` and, where needed,
its own `references/` and `scripts/` resources. The shared frontmatter uses
`name`, `description`, `license`, and `metadata`. Project-specific fields such as
version, dependencies, tags, and related skills live under `metadata` as strings,
following the [Agent Skills specification](https://agentskills.io/specification).
Dependency and relationship metadata is descriptive; it is not an executable
package manager or workflow scheduler.

The source layout is:

```text
lasio/SKILL.md                             # Example domain skill
segyio/SKILL.md                            # Example domain skill
...                                       # 39 domain skills in total
workflows/well-log-evaluation/SKILL.md      # One of eight workflow skills
using-geoscience-skills/SKILL.md            # Discovery and routing skill
```

The router is separate from `workflows/` so it can be installed independently of
the eight workflows. Workflow instructions refer to related skills by name;
agents should resolve those names from their installed skill inventory. A
workflow can also be followed in a single agent session when delegation is
unavailable.

Python execution remains an environment concern. Install only the scientific
libraries required by the selected task, check their versions, and make the
input data available in the environment where the agent executes code. Installing
a skill does not provide a Python interpreter, geoscience libraries, external
service credentials, or input datasets.

## Optional Claude Code integrations

| Repository component | Portable skills installation | Claude Code integration |
| --- | --- | --- |
| The 48 skill directories | Installed when selected | Also usable through supported Claude installation routes |
| `.claude/commands/` | Not installed as commands | Optional command shortcuts |
| `.claude/settings.json` SessionStart hook | Not installed or activated | Optional repository configuration |
| `agents/` role definitions | Not registered as subagents | Optional Claude-specific agent definitions |
| `.claude-plugin/` manifests | Not a cross-agent plugin installation | Optional Claude marketplace integration |

These repository integrations use Claude conventions. Other agents may offer
their own commands, hooks, or subagents, but this project does not install or
configure equivalents through the generic skills installer. Reading marketplace
metadata to discover skill directories is separate from installing a plugin's
commands, hooks, or agents. The scientific workflows do not require the optional
integrations.

## Verification scope

Compatibility evidence has three distinct levels:

| Level | What it establishes | What it does not establish |
| --- | --- | --- |
| Format validation | Skill frontmatter, names, inventory, and bundled references satisfy repository checks. | That an agent loads or follows the skill. |
| Installer smoke test | A specified version of the upstream CLI discovers and installs the expected files for selected targets. | That the target application starts, activates the skill, or executes scientific code. |
| Agent task evaluation | A named agent/version runs a recorded task and produces checked results. | Equivalent behavior in other agents, versions, models, or execution environments. |

On **2026-09-14**, local installation checks passed with **skills CLI 1.5.26**
for all nine named installer targets. Each target received all **48 skills**,
with the expected project directory, upstream inventory and byte-for-byte
preservation of bundled resources. This uses disposable projects and does not
require the target application to be installed. The upstream CLI remains
responsible for installation; this repository checks the result.

The 48-skill collection passes portable validation. The lightweight regression
suite covers manifests, installation integrity, dependency reporting and the
native/explicit evaluation protocols. The
[validation workflow](../.github/workflows/validate-skills.yml) repeats all nine
installation targets on Linux and Windows; its
[run history](https://github.com/SteadfastAsArt/geoscience-skills/actions/workflows/validate-skills.yml)
identifies the tested revision. The earlier 36-skill/CLI 1.5.25 Windows result
remains in [PR #3's verification run](https://github.com/SteadfastAsArt/geoscience-skills/actions/runs/34810508410);
it is not reused as evidence for the added skills.

Recorded [native Codex evaluations](AGENT_EVALUATIONS.md) passed **LAS QC, SEG-Y
subsetting and formation evaluation** using Codex 0.154.0 and configured model
`gpt-5.5`. Each run scanned all 48 skills with enabled repository scope, received
no catalog or skill-path hints in its task, successfully read the appropriate
native skill file, completed normally and passed independent numerical checks.
The three runs use one recorded skill snapshot; its hashes identify the tested
content even when later documentation changes.

Earlier explicit-catalog runs remain available, including the initial SEG-Y
timeout and successful controlled retry. A corrected evidence parser replayed
native logs after its first assessment missed double-quoted shell reads; those
initial assessments are retained. No extra model run was needed to recover the
already-recorded successful read evidence.

Claude runtime testing is excluded from this round by user request. OpenClaw's
CLI is present but lacks the inspected provider/runtime configuration; the
other assessed client CLIs were unavailable. The
[dated availability record and adapter assessment](PLATFORM_ADAPTER_ASSESSMENT.md)
state the checks and limits. No additional adapter was justified beyond the
existing optional manifests: shared native installation already preserves the
full skill bundles. Installation or Codex results do not establish another
agent's runtime behavior.

Separate [scientific regression suites](SCIENTIFIC_TESTING.md) execute audited
Python examples and check numerical results and exported coordinates. Their
isolated scientific environments are distinct from these installer checks;
passing them does not establish skill activation or task execution inside any
particular coding agent.

## Manual reading fallback

An agent without native skills support can still use the repository as reference
material if it can read local files. Clone the repository and give it a focused
instruction such as:

> Read `SKILLS.md` in this checkout to choose the skill for my task. Then read
> that skill's `SKILL.md` and only the referenced resources needed for the task.
> If it names a complementary skill, locate that skill in this checkout before
> continuing.

This supplies instructions explicitly; it does not add native skill discovery.
Do not concatenate the whole library into `AGENTS.md` or another always-loaded
rules file. Keep the catalogue as an entry point and load individual skills as
needed.
