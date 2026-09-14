# Coding agent task evaluations

**Recorded result, 2026-09-14:** Codex passed native LAS QC, SEG-Y subsetting and
formation-evaluation tasks. Its scanner discovered all 48 staged skills and the
model selected/read the relevant domain or workflow skill without a skill hint
in the task prompt. The [recorded runs](#recorded-local-run) also retain earlier
explicit-file results, including the original timeout.

These evaluations run a coding-agent CLI on synthetic LAS, SEG-Y and formation-evaluation tasks and
check the files it produces. They supplement installation checks and Python
example tests with a narrow, observable task run. They do not establish broad
scientific correctness or performance on field data.

## Evaluation mode and evidence

Two modes are available. **Explicit-file evaluation** provides the checkout's
skill catalog and asks the agent to select and read relevant documents. Its
historical runs used 36 skills. This mode does not establish native discovery.

**Native evaluation** installs the discovered checkout inventory under the
temporary project's `.agents/skills` directory. Its task prompt contains no
catalog, skill names, skill paths, or instruction to select/read skills. The
installed Codex CLI first answers `skills/list` through its local app-server
protocol, without starting a model turn. The evaluator requires every staged
skill to appear enabled at its exact repository path. A separate `codex exec`
then receives only the scientific task and environment constraints.

Native activation evidence means that the CLI scanner found the skill and the
task-running model subsequently read its content from the native directory.
It is an observable discovery-and-read criterion, not hidden model telemetry
or proof that the document caused the numerical result. Reports record inventory
counts and per-skill content hashes; tests derive counts from the discoverer,
so adding skills does not require editing the evaluation inventory.

The report keeps the following evidence separate:

- `numerical_checks`: independent checks against private expected values.
- `claimed_skills`: the agent's own `evidence.json` statement.
- `observed_skill_reads` and `skill_read_evidence`: successful Read tool events,
  or recognizable file-reading shell commands whose returned content contains
  the skill's frontmatter name. Echoing a path or self-reporting usage does not
  count. This establishes a document read, not proof of causal influence.
- `skill_selection_verified`: in explicit mode the expected task skill was both
  claimed and observed; native mode instead requires verified native discovery
  and a successful content read, without asking for self-reported skills.
  `native_discovery` and `native_activation_verified` retain those separate
  checks. A `passed` task also requires successful CLI completion and numerical
  acceptance; CLI exit status alone is insufficient.
- CLI version, configured/observed model identifiers, Python/library versions,
  exact normalized CLI invocation, task/skill/output hashes, and successful
  tool-command hashes. Short task-scoped commands are also retained as text;
  complex or private-path commands remain hashes only.

`solution.py` is retained with the temporary task artifacts. The harness checks
that it exists and grades produced files; it does not independently replay the
agent's source. A retained script is not a verified reproducibility claim.

## Cases and acceptance

| Case | Input | Acceptance |
| --- | --- | --- |
| `las-qc` | 17 LAS rows, a duplicate depth, NULLs in two curves, explicit units | Exact counts, units and depth-order checks; finite null-excluding min/max/mean with `1e-7` absolute/relative tolerance |
| `segy-subset` | 9 interleaved SEG-Y traces, 12 IEEE float samples each, coordinate scalar and delay | Exactly the five requested traces in original order; exact sample amplitudes, text header, binary sample metadata and ten specified trace-header fields |
| `formation-evaluation` | LAS with GR, density and resistivity, calibration parameters, missing rows and invalid physical values | Every row retained; null-aware QC, shale fraction, density porosity, Archie saturation/clipping; merged lithology intervals never cross invalid samples |

Fixtures and graders use the Python standard library. Expected answers remain
in the parent process; the agent namespace contains only task text, synthetic
inputs and public skill content. Fixture readback tests additionally use real
lasio and segyio, independently checking the hand-built input formats.

## Reproduce

Use Linux with working `bwrap`, an existing coding-agent CLI, and an isolated
Python 3.12 environment containing the current [core dependencies](../tests/science/requirements-core.txt).
The script does not install dependencies or agent CLIs. Run the free tests first:

```bash
python3 -m unittest discover -s tests -p test_agent_evaluations.py -v
/path/to/core-venv/bin/python evals/tests/test_fixture_readback.py -v
```

Run all available Codex tasks using native discovery and the configured default model:

```bash
python3 scripts/evaluate_agents.py \
  --agents codex \
  --mode native \
  --python /path/to/core-venv/bin/python \
  --timeout 300 \
  --output /tmp/codex-geoscience-evaluation.json
```

Use `--cli codex=/path/to/codex` if it is not on PATH. Use `--tasks las-qc`
or `--tasks segy-subset` / `--tasks formation-evaluation` for one case. The default
mode remains `explicit-file` for backwards compatibility; select `--mode native`
to test implicit invocation. `--seed` changes synthetic measurements
without changing the contract. Keep the recorded seed when reproducing inputs.
Codex is the default target; the preserved Claude adapter is opt-in with
`--agents claude`, and supports `--max-budget-usd` per task. Agent calls may use
the user's paid service; Codex has a wall-clock timeout rather than a dollar cap.
For a stable comparison while the checkout changes, copy public skill directories
to a separate snapshot and pass `--skill-source /path/to/snapshot` to each run.
Reports include both entrypoint and complete bundled-resource hashes. Native
inventory hashes cover the private canonical inventory rather than a catalog
file exposed to the agent. The task protocol still comes from this evaluator.

The runner uses an allowlist of read-only runtime mounts, a temporary writable
workspace, read-only inputs/skills, and private copies of authentication and
minimal model configuration. The main checkout and user skills are not mounted.
It preserves the configured model and omits unrelated hooks, plugins and MCP
configuration. Private authentication state is removed after each run; temporary
artifacts and raw transcripts remain under the printed `/tmp/geoscience-eval-*`
directory. Do not publish those raw directories without reviewing them. The
machine-readable report excludes credentials and private configuration paths.

Missing CLIs are `not-run`; authentication/isolation failures are `blocked`;
timeouts, incomplete tasks and rejected results are `failed`. A blocking first
task prevents repeated attempts for the same agent in that invocation. The
runner exits nonzero when any requested task is not passed. Gemini and GitHub
Copilot currently have no execution adapters, so their absence or unsupported
adapter status is recorded honestly rather than inferred from installation.

## Recorded local run

The native runs used one [48-skill snapshot](../evals/results/2026-09-14-native-snapshot.json),
Codex 0.154.0, the configured `gpt-5.5` model, and the existing isolated
Python 3.11.14 environment with NumPy 1.26.4, lasio 0.32 and segyio 1.9.14.
These historical results predate the current Python 3.12 test baseline.
Every run independently obtained 48 enabled repository
skills with zero parse errors from the installed CLI's `skills/list` scanner.
The snapshot predates any later edits in the working tree; the reports do not
claim runtime verification of subsequently changed skill content.

| Native task | Actual selected/read skill | Numerical and execution result |
| --- | --- | --- |
| [LAS QC](../evals/results/2026-09-14-native-las-qc.json) | `lasio` | Passed in 94 seconds; 300-second limit |
| [SEG-Y subset](../evals/results/2026-09-14-native-segy-subset.json) | `segyio` | Passed in 120 seconds; 300-second limit |
| [Formation evaluation](../evals/results/2026-09-14-native-formation-evaluation.json) | `well-log-evaluation` | Passed in 159 seconds; 420-second limit |

These tasks used the [native protocol](../evals/protocols/native-v1.md), and their
complete prompts are retained with matching hashes in `evals/results/prompts/`.
Formation evaluation checked null propagation, invalid resistivity, invalid
porosity, saturated/clipped Archie results, and lithology intervals separated
by missing samples. It establishes this small workflow execution, not all
hydrological, climate or near-surface workflow branches.

The first evidence-parser assessment missed successful `sed` reads inside
double-quoted shell commands. Its [original assessments](../evals/results/assessments/)
are retained. The corrected parser unwraps shell commands and distinguishes a
reader from echoing a command string; a regression test covers the actual
command form. The same original transcripts were reassessed without another
model call or any relaxation of numerical, path or returned-content checks.
Each corrected report links to its prior assessment and checksum.

Earlier explicit-file runs remain unchanged:

The checked-in [initial report](../evals/results/2026-09-14.json) and
[protocol 2 retry](../evals/results/2026-09-14-segy-protocol-v2.json), both dated
2026-09-14, record the actual runs and their limitations. Codex 0.154.0 used the
existing `gpt-5.5` configuration. The runtime
was Python 3.11.14, NumPy 1.26.4, lasio 0.32 and segyio 1.9.14.

| Agent / case | Numerical acceptance | Observed skill read | Overall execution |
| --- | --- | --- | --- |
| Codex / LAS QC, protocol 1 | Passed | `lasio` verified | Passed in 108 seconds |
| Codex / SEG-Y subset, protocol 1 | Passed, including exact samples and headers | `segyio` verified | Failed: 180-second timeout during final evidence housekeeping |
| Codex / SEG-Y subset, protocol 2 | Passed, including exact samples and headers | `segyio` verified | Passed in 154 seconds |
| Claude / LAS QC | No task output | None | Historical authentication block |
| Claude / SEG-Y subset | Not run | None | Excluded from this round |
| Gemini / GitHub Copilot | Not run | None | CLI unavailable |

The SEG-Y timeout remains a failure in the report even though its files passed
all numerical checks. At the timeout the agent had validated `evidence.json`
and announced that it would add that validation command to the evidence. No
successful final CLI completion was recorded. This illustrates why file
correctness and complete agent execution are separate measures.

Claude runtime evaluation is excluded from this verification round; its
compatibility remains based on format and installation evidence. Its execution
adapter is retained. The earlier authentication-blocked attempt is retained as
historical evidence: Claude 2.1.270 reported `OAuth session expired and could not
be refreshed`. The SEG-Y task was not launched for Claude. No Claude runtime
success is inferred from Codex results. Other agent model tasks were not run.
The [platform availability record](../evals/results/2026-09-14-platform-availability.json)
and [adapter assessment](PLATFORM_ADAPTER_ASSESSMENT.md) distinguish absent CLIs
from OpenClaw's present but unconfigured runtime.

Protocol 1 requested an agent-authored command list. [Protocol 2](../evals/protocols/v2.md)
reduces that file to skill names and output names and requests that it be written
once; the runner continues to record actual tool commands. The original full
prompts are preserved under [results/prompts](../evals/results/prompts/), with
hashes in the first report. A single controlled SEG-Y retry uses protocol 2 and
a 300-second limit, with the same seed, model configuration and numerical/read
acceptance. It completed in 154 seconds and produced the same SEG-Y output hash
as the first attempt. Its report remains separate from the original failure.
Since both prompt and time limit changed, this retry cannot isolate their
individual effects.

The free regression suite covers malformed outputs, scientific perturbations,
input preservation, seed reproducibility, hidden answers and tool-read evidence.
The paid agent runs are manual; ordinary CI should run the free tests and must
not claim that those tests exercised an agent model.

## Upstream interfaces

The adapters use [Codex non-interactive mode](https://developers.openai.com/codex/noninteractive/)
and its [CLI reference](https://developers.openai.com/codex/cli/reference/), plus
the [Claude CLI reference](https://code.claude.com/docs/en/cli-usage) and documented
[environment controls](https://code.claude.com/docs/en/env-vars). Local `--help`
was checked against the recorded CLI versions. Native discovery follows the
[OpenAI skill locations](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)
and [app-server protocol](https://developers.openai.com/codex/app-server/); the
installed CLI generated the JSON schemas used to verify request/response fields.
Future CLI output changes may
require evidence-parser updates; a missing read event must not be upgraded to a
successful native skill activation claim.
