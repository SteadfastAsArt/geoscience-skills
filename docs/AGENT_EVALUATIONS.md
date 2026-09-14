# Coding agent task evaluations

These evaluations run a coding-agent CLI on synthetic LAS and SEG-Y tasks and
check the files it produces. They supplement installation checks and Python
example tests with a narrow, observable task run. They do not establish broad
scientific correctness or performance on field data.

## Evaluation mode and evidence

The current mode is **explicit-file evaluation**. Every agent receives a
36-skill catalog from the evaluated checkout and a request to select and read
relevant skill documents. Each report records the catalog's content hash. The
prompt does not name the desired skill. This tests selection from the catalog,
but **does not test native automatic skill discovery or activation**.

The report keeps the following evidence separate:

- `numerical_checks`: independent checks against private expected values.
- `claimed_skills`: the agent's own `evidence.json` statement.
- `observed_skill_reads` and `skill_read_evidence`: successful Read tool events,
  or recognizable file-reading shell commands whose returned content contains
  the skill's frontmatter name. Echoing a path or self-reporting usage does not
  count. This establishes a document read, not proof of causal influence.
- `skill_selection_verified`: the expected task skill was both claimed and
  observed. A `passed` task also requires successful CLI completion and numerical
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

Fixtures and graders use the Python standard library. Expected answers remain
in the parent process; the agent namespace contains only task text, synthetic
inputs and public skill content. Fixture readback tests additionally use real
lasio and segyio, independently checking the hand-built input formats.

## Reproduce

Use Linux with working `bwrap`, Python 3.11+, an existing coding-agent CLI, and an
isolated Python environment containing the [core dependencies](../tests/science/requirements-core.txt).
The script does not install dependencies or agent CLIs. Run the free tests first:

```bash
python3 -m unittest discover -s tests -p test_agent_evaluations.py -v
/path/to/core-venv/bin/python evals/tests/test_fixture_readback.py -v
```

Run the two Codex tasks using the configured default model:

```bash
python3 scripts/evaluate_agents.py \
  --agents codex \
  --python /path/to/core-venv/bin/python \
  --timeout 300 \
  --output /tmp/codex-geoscience-evaluation.json
```

Use `--cli codex=/path/to/codex` if it is not on PATH. Use `--tasks las-qc`
or `--tasks segy-subset` for one case. `--seed` changes synthetic measurements
without changing the contract. Keep the recorded seed when reproducing inputs.
Codex is the default target; the preserved Claude adapter is opt-in with
`--agents claude`, and supports `--max-budget-usd` per task. Agent calls may use
the user's paid service; Codex has a wall-clock timeout rather than a dollar cap.

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
success is inferred from Codex results. Other agent CLIs were not run.

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
was checked against the recorded CLI versions. Future CLI output changes may
require evidence-parser updates; a missing read event must not be upgraded to a
successful native skill activation claim.
