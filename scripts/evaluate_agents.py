#!/usr/bin/env python3
"""Run small skill-assisted tasks in isolated Linux coding-agent processes.

No packages, agents or global skills are installed or updated by this script.
Raw transcripts and agent artifacts remain in private temporary directories.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import shlex
import signal
import subprocess
import sys
import tempfile
import time
import tomllib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evals.cases import TASKS, digest, grade, make_fixture  # noqa: E402
from scripts.validate_skills import find_skill_dirs, parse_frontmatter  # noqa: E402

AGENTS = ("codex", "claude", "gemini", "github-copilot")
CLI_NAMES = {"codex": "codex", "claude": "claude",
             "gemini": "gemini", "github-copilot": "copilot"}
SUPPORTED = {"codex", "claude"}
PROTOCOL_VERSION = "2"
NATIVE_PROTOCOL_VERSION = "native-1"


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def bundle_digest(directory: Path) -> str:
    checksum = hashlib.sha256()
    for path in sorted(directory.rglob("*")):
        if path.is_file() and not path.is_symlink():
            checksum.update(path.relative_to(directory).as_posix().encode() + b"\0")
            checksum.update(bytes.fromhex(digest(path)))
    return checksum.hexdigest()


def toml_value(value) -> str:
    if isinstance(value, dict):
        return "{" + ", ".join(f"{json.dumps(k)} = {toml_value(v)}"
                                for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(map(toml_value, value)) + "]"
    if type(value) in (bool, int, float, str):
        return json.dumps(value)
    raise ValueError("unsupported model configuration type")


def stage_credentials(agent: str, home: Path, state: Path) -> tuple[str | None, list[Path]]:
    """Copy authentication privately; omit hooks, plugins, MCP and user rules."""
    copied = []
    model = None
    if agent == "codex":
        source = Path(os.environ.get("CODEX_HOME", str(home / ".codex")))
        destination = state / "codex"
        destination.mkdir()
        config = {}
        try:
            config = tomllib.loads((source / "config.toml").read_text())
        except FileNotFoundError:
            pass
        # Preserve model/provider selection; intentionally omit unrelated user setup.
        kept = {key: config[key] for key in (
            "model", "model_provider", "model_reasoning_effort",
            "model_reasoning_summary", "model_verbosity") if key in config}
        provider = config.get("model_provider", "openai")
        definition = config.get("model_providers", {}).get(provider)
        if definition:
            kept["model_providers"] = {provider: definition}
        model = config.get("model")
        (destination / "config.toml").write_text("\n".join(
            f"{key} = {toml_value(value)}" for key, value in kept.items()) + "\n")
        credentials = [(source / "auth.json", destination / "auth.json")]
    else:
        source = home / ".claude"
        destination = state / "home" / ".claude"
        destination.mkdir(parents=True, exist_ok=True)
        config = read_json(source / "settings.json")
        model = config.get("model")
        kept = {key: config[key] for key in ("model", "effortLevel") if key in config}
        kept.update(disableAllHooks=True)
        write_json(destination / "settings.json", kept)
        write_json(state / "home" / ".claude.json", {"hasCompletedOnboarding": True})
        credentials = [(source / ".credentials.json", destination / ".credentials.json")]
    for source, destination in credentials:
        if source.is_file():
            shutil.copyfile(source, destination)
            destination.chmod(0o600)
            copied.append(destination)
    return model, copied


def stage_workspace(task: str, destination: Path, seed: int, root: Path = ROOT,
                    mode: str = "explicit-file", skill_root: Path | None = None) -> dict:
    destination.mkdir(parents=True)
    oracle = make_fixture(task, destination / "inputs", seed)
    catalog = []
    for directory in find_skill_dirs(skill_root or root):
        frontmatter = parse_frontmatter((directory / "SKILL.md").read_text())
        skill_base = Path(".agents/skills") if mode == "native" else Path("skills")
        target = destination / skill_base / frontmatter["name"]
        # No symlinks: a repository link must never expose external host paths.
        for path in directory.rglob("*"):
            if path.is_file() and not path.is_symlink() and not any(
                part.startswith(".") or part == "__pycache__"
                for part in path.relative_to(directory).parts
            ):
                output = target / path.relative_to(directory)
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, output)
        catalog.append({"name": frontmatter["name"], "description": frontmatter["description"],
                        "path": (skill_base / frontmatter["name"] / "SKILL.md").as_posix(),
                        "sha256": digest(target / "SKILL.md"), "bundle_sha256": bundle_digest(target)})
    if mode == "explicit-file":
        write_json(destination / "skill-catalog.json", catalog)
    else:
        # Git marks the discovery root; it does not expose the main checkout.
        subprocess.run(["git", "init", "--quiet", str(destination)], check=True, capture_output=True)
    task_text = (root / "evals" / "tasks" / f"{task}.md").read_text()
    protocol_file = "native-v1.md" if mode == "native" else f"v{PROTOCOL_VERSION}.md"
    protocol = (root / "evals" / "protocols" / protocol_file).read_text().rstrip()
    prompt = protocol + "\n\n" + task_text
    (destination / "TASK.md").write_text(prompt)
    oracle["prompt_sha256"] = hashlib.sha256(prompt.encode()).hexdigest()
    oracle["catalog"] = catalog
    oracle["catalog_sha256"] = (digest(destination / "skill-catalog.json") if mode == "explicit-file"
                                else hashlib.sha256(json.dumps(catalog, sort_keys=True).encode()).hexdigest())
    oracle["protocol_version"] = NATIVE_PROTOCOL_VERSION if mode == "native" else PROTOCOL_VERSION
    return oracle


def python_runtime(python: Path) -> dict:
    code = """import sys,json,importlib.metadata as m
versions={p:m.version(p) for p in ('lasio','segyio','numpy')}
for package in ('pandas','welly','striplog'):
    try: versions[package]=m.version(package)
    except m.PackageNotFoundError: pass
print(json.dumps({'prefix':sys.prefix,'base_prefix':sys.base_prefix,
                  'python':sys.version.split()[0],'libraries':versions}))
"""
    result = subprocess.run([str(python), "-c", code], capture_output=True, text=True, timeout=20)
    if result.returncode:
        raise ValueError("evaluation Python must provide lasio, segyio and numpy")
    return json.loads(result.stdout)


def sandbox_command(agent: str, cli: Path, python: Path, runtime: dict,
                    run_dir: Path, budget: float, mode: str = "explicit-file") -> tuple[list[str], dict, list[str]]:
    """Mount an allowlist, never the host root, main repository, or global skills."""
    home = Path(os.environ["HOME"])
    state, workspace = run_dir / "state", run_dir / "workspace"
    (state / "home").mkdir(parents=True, exist_ok=True)
    command = [shutil.which("bwrap"), "--die-with-parent", "--unshare-pid", "--new-session",
               "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp"]
    for path in ("/usr", "/bin", "/lib", "/lib64", "/etc/ssl", "/etc/resolv.conf",
                 "/etc/hosts", "/etc/nsswitch.conf", "/etc/passwd", "/etc/group"):
        if Path(path).exists():
            command += ["--ro-bind", path, path]
    command += ["--bind", str(state / "home"), str(home)]
    mounts = {str(Path(runtime["prefix"])), str(Path(runtime["base_prefix"]))}
    if agent == "codex":
        node = Path(shutil.which("node") or "/nonexistent").resolve()
        # The npm launcher uses relative package resources under its Node prefix.
        mounts.add(str(node.parent.parent))
        resolved_cli = cli.resolve()
        if resolved_cli.name == "codex.js" and resolved_cli.parent.name == "bin":
            mounts.add(str(resolved_cli.parent.parent))
        codex_home = os.environ.get("CODEX_HOME", str(home / ".codex"))
        command += ["--bind", str(state / "codex"), codex_home]
        inner_cli = str(cli)
        if not any(cli.is_relative_to(Path(m)) for m in mounts):
            command += ["--ro-bind", str(cli.resolve()), "/opt/codex-cli"]
            inner_cli = "/opt/codex-cli"
        invocation = [inner_cli, "exec", "--json", "--ephemeral", "--skip-git-repo-check",
                      "--sandbox", "workspace-write", "-c", 'approval_policy="never"',
                      "-c", "features.multi_agent=false", "-"]
    else:
        command += ["--ro-bind", str(cli.resolve()), "/opt/claude-cli"]
        invocation = ["/opt/claude-cli", "-p", "--output-format", "stream-json", "--verbose",
                      "--no-session-persistence", "--max-budget-usd", str(budget),
                      "--setting-sources", "user", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                      "--permission-mode", "dontAsk", "--permission-prompts", "none",
                      "--tools", "Read,Write,Edit,Bash,Glob,Grep",
                      "--allowedTools", "Read,Write,Edit,Bash,Glob,Grep"]
    for mount in sorted(mounts):
        if Path(mount) in (Path("/"), Path("/home"), Path("/tmp"), home) or ROOT.is_relative_to(Path(mount)):
            raise ValueError("refusing a runtime mount that exposes unrelated host files")
        command += ["--ro-bind", mount, mount]
    command += ["--bind", str(workspace), "/workspace"]
    protected = ("inputs", ".agents/skills", "TASK.md") if mode == "native" else (
        "inputs", "skills", "skill-catalog.json", "TASK.md")
    for name in protected:
        command += ["--ro-bind", str(workspace / name), f"/workspace/{name}"]
    command += ["--chdir", "/workspace", "--"] + invocation
    # Keep HOME/CODEX_HOME values unchanged: their filesystem targets are private mounts.
    names = ("HOME", "USER", "LANG", "TERM", "CODEX_HOME", "OPENAI_API_KEY",
             "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
             "ANTHROPIC_MODEL", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY")
    env = {name: os.environ[name] for name in names if name in os.environ}
    node_bin = str(Path(shutil.which("node") or "/usr/bin/node").parent)
    env.update(PATH=f"{python.parent}:{node_bin}:/usr/local/bin:/usr/bin:/bin",
               MPLBACKEND="Agg", DISABLE_AUTOUPDATER="1",
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1",
               CLAUDE_CODE_DISABLE_AUTO_MEMORY="1")
    return command, env, invocation


def native_discovery(command: list[str], env: dict, run_dir: Path, catalog: list[dict]) -> dict:
    """Ask the installed Codex scanner for skills, without starting a model turn."""
    separator = command.index("--")
    discovery_command = command[:separator + 2] + ["app-server", "--stdio"]
    events, buffered = [], b""
    stderr_path = run_dir / "discovery-stderr.log"
    with stderr_path.open("w") as stderr:
        process = subprocess.Popen(discovery_command, env=env, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=stderr, start_new_session=True)
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        deadline = time.monotonic() + 25

        def request(message, response_id):
            nonlocal buffered
            process.stdin.write((json.dumps(message) + "\n").encode())
            process.stdin.flush()
            while time.monotonic() < deadline:
                while b"\n" in buffered:
                    line, buffered = buffered.split(b"\n", 1)
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    if not isinstance(event, dict):
                        continue
                    events.append(event)
                    if event.get("id") == response_id:
                        return event
                if selector.select(max(0, deadline - time.monotonic())):
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        raise ValueError("native discovery process ended without response")
                    buffered += chunk
            raise TimeoutError("native discovery exceeded 25 seconds")

        try:
            initialized = request({"id": 1, "method": "initialize", "params": {
                "clientInfo": {"name": "geoscience-evaluation", "version": "1"}}}, 1)
            if "error" in initialized:
                raise ValueError("native discovery initialization failed")
            process.stdin.write(b'{"method":"initialized"}\n')
            process.stdin.flush()
            response = request({"id": 2, "method": "skills/list", "params": {
                "cwds": ["/workspace"], "forceReload": True}}, 2)
        finally:
            selector.close()
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate()
            (run_dir / "discovery.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    return summarize_discovery(response, catalog)


def summarize_discovery(response: dict, catalog: list[dict]) -> dict:
    expected = {entry["name"]: "/workspace/" + entry["path"] for entry in catalog}
    discovered, errors = {}, 0
    data = response.get("result", {})
    data = data.get("data", []) if isinstance(data, dict) else []
    for entry in data:
        if entry.get("cwd") != "/workspace":
            continue
        errors += len(entry.get("errors", []))
        for skill in entry.get("skills", []):
            name = skill.get("name")
            if (name in expected and skill.get("path") == expected[name]
                    and skill.get("scope") == "repo" and skill.get("enabled") is True):
                discovered[name] = {"name": name, "path": expected[name], "scope": "repo", "enabled": True}
    missing = sorted(set(expected) - set(discovered))
    return {"method": "codex app-server skills/list", "passed": bool(expected) and not missing and errors == 0 and "error" not in response,
            "expected_count": len(expected), "discovered_count": len(discovered),
            "missing": missing, "parse_error_count": errors,
            "skills": [discovered[name] for name in sorted(discovered)]}


def shell_read_paths(command: str) -> list[tuple[str, str]]:
    """Recognize direct readers after shell unwrapping; quoted echo text is not a command."""
    try:
        wrapped = shlex.split(command)
        if (len(wrapped) == 3 and Path(wrapped[0]).name in {"bash", "sh", "dash", "zsh"}
                and wrapped[1] in {"-c", "-lc"}):
            command = wrapped[2]
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        segments, current = [], []
        for token in lexer:
            if token and all(char in ";&|" for char in token):
                segments.append(current)
                current = []
            else:
                current.append(token)
        segments.append(current)
        return [match for segment in segments
                if segment and Path(segment[0]).name in {"cat", "head", "tail", "sed"}
                for argument in segment[1:]
                for match in re.findall(r"(?<![\w.-])((?:/workspace/)?(?:\.agents/)?skills/([a-z0-9-]+)/SKILL\.md)\b", argument)]
    except ValueError:
        return []


def extract_evidence(agent: str, transcript: str) -> dict:
    """Require successful observed tool reads, not the agent's self-report alone."""
    commands, reads, models, pending, read_evidence = [], set(), set(), {}, []

    def observe(tool: str, arguments: dict, output):
        value = arguments.get("command", "") if tool in ("Bash", "command_execution") else arguments.get("file_path", "")
        if not isinstance(value, str):
            return
        # Publish only hashes for arbitrary shell commands; raw logs stay private.
        record = {"tool": tool, "sha256": hashlib.sha256(value.encode()).hexdigest()}
        try:
            tokens = shlex.split(value)
            if len(tokens) == 3 and tokens[1] in ("-lc", "-c"):
                tokens = shlex.split(tokens[2])
            if tokens and tokens[0] in ("python", "python3", "cat", "head", "sed", "ls", "rg") and all(
                    re.fullmatch(r"[a-zA-Z0-9_./,*: -]+", token) and
                    not token.startswith(("/home/", "/tmp/", "/etc/")) and
                    not any(secret in token.lower() for secret in ("auth", "credential", "token", ".env"))
                    for token in tokens) and len(value) < 300:
                record["command"] = shlex.join(tokens)
        except ValueError:
            pass
        commands.append(record)
        paths = (re.findall(r"(?<![\w.-])((?:/workspace/)?(?:\.agents/)?skills/([a-z0-9-]+)/SKILL\.md)\b", value)
                 if tool == "Read" else shell_read_paths(value))
        rendered = output if isinstance(output, str) else json.dumps(output)
        for skill_path, skill in paths:
            # A successful command merely mentioning the path is not a file read.
            if re.search(r"\bname:\s*[\"']?" + re.escape(skill) + r"\b", rendered):
                reads.add(skill)
                read_evidence.append({"skill": skill, "tool": tool,
                                      "path": skill_path,
                                      "output_sha256": hashlib.sha256(rendered.encode()).hexdigest()})

    for line in transcript.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        model = event.get("model")
        if isinstance(model, str) and re.fullmatch(r"[a-zA-Z0-9._:/-]{1,100}", model):
            models.add(model)
        message = event.get("message", {})
        if not isinstance(message, dict):
            message = {}
        if isinstance(message.get("model"), str):
            models.add(message["model"])
        if isinstance(event.get("modelUsage"), dict):
            models.update(event["modelUsage"])
        if agent == "codex":
            item = event.get("item", {})
            if (event.get("type") == "item.completed" and isinstance(item, dict)
                    and item.get("type") == "command_execution" and item.get("exit_code") == 0):
                observe("command_execution", item, item.get("aggregated_output", ""))
        else:
            for content in message.get("content", []) if isinstance(message.get("content"), list) else []:
                if not isinstance(content, dict):
                    continue
                if content.get("type") == "tool_use":
                    pending[content.get("id")] = (content.get("name"), content.get("input", {}))
                elif content.get("type") == "tool_result" and not content.get("is_error"):
                    tool, arguments = pending.pop(content.get("tool_use_id"), (None, {}))
                    if tool in ("Read", "Bash"):
                        observe(tool, arguments, content.get("content", ""))
    return {"observed_skill_reads": sorted(reads), "tool_commands": commands,
            "skill_read_evidence": read_evidence,
            "observed_models": sorted(model for model in models if
                                      re.fullmatch(r"[a-zA-Z0-9._:/-]{1,100}", model))}


def classify_failure(text: str, timed_out: bool, returncode: int) -> str:
    if timed_out:
        return "timeout"
    lowered = text.lower()
    if any(word in lowered for word in ("not logged in", "please log in", "authentication",
                                         "invalid api key", "401 unauthorized", "login required")):
        return "authentication_unavailable"
    if any(word in lowered for word in ("usage limit", "rate limit", "insufficient_quota", "credit balance")):
        return "quota_or_rate_limit"
    if "bwrap:" in lowered or "sandbox setup failed" in lowered:
        return "isolation_unavailable"
    return "cli_error" if returncode else "task_incomplete"


def run_one(agent: str, task: str, cli: Path, args, runtime: dict) -> dict:
    run_dir = Path(tempfile.mkdtemp(prefix=f"geoscience-eval-{agent}-{task}-"))
    run_dir.chmod(0o700)
    state = run_dir / "state"
    state.mkdir()
    (state / "home").mkdir()
    oracle = stage_workspace(task, run_dir / "workspace", args.seed, mode=args.mode,
                             skill_root=args.skill_source)
    try:
        model, credentials = stage_credentials(agent, Path(os.environ["HOME"]), state)
        command, env, invocation = sandbox_command(agent, cli, args.python, runtime, run_dir, args.max_budget_usd, args.mode)
    except BaseException:
        shutil.rmtree(state)
        raise
    result = dict(agent=agent, task=task, configured_model=model, seed=args.seed,
                  protocol_version=oracle["protocol_version"], evaluation_mode=args.mode,
                  prompt_sha256=oracle["prompt_sha256"], input_sha256=oracle["input_sha256"],
                  skill_catalog_sha256=oracle["catalog_sha256"],
                  installed_skill_count=len(oracle["catalog"]),
                  installed_skill_hashes={entry["name"]: entry["sha256"] for entry in oracle["catalog"]},
                  installed_bundle_hashes={entry["name"]: entry["bundle_sha256"] for entry in oracle["catalog"]},
                  input_files_sha256=oracle["input_files_sha256"],
                  command=[agent, *invocation[1:]], isolation="bubblewrap-allowlist",
                  limits={"timeout_seconds": args.timeout,
                          "budget_usd": args.max_budget_usd if agent == "claude" else None},
                  expected_skill=TASKS[task], status="blocked", reason=None)
    start = time.monotonic()
    timed_out = False
    stdout_path, stderr_path = run_dir / "stdout.jsonl", run_dir / "stderr.log"
    try:
        if args.mode == "native":
            try:
                result["native_discovery"] = native_discovery(command, env, run_dir, oracle["catalog"])
            except (OSError, ValueError, TimeoutError) as exc:
                result["native_discovery"] = {"passed": False, "error_type": type(exc).__name__}
            if not result["native_discovery"]["passed"]:
                result.update(status="blocked", reason="native_discovery_failed",
                              duration_seconds=round(time.monotonic() - start, 3))
                return result
        with stdout_path.open("w") as stdout, stderr_path.open("w") as stderr:
            process = subprocess.Popen(command, env=env, stdin=subprocess.PIPE,
                                       stdout=stdout, stderr=stderr, text=True, start_new_session=True)
            try:
                process.communicate((run_dir / "workspace" / "TASK.md").read_text(), timeout=args.timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(process.pid, signal.SIGKILL)
                process.communicate()
        text = stdout_path.read_text(errors="replace")
        errors = stderr_path.read_text(errors="replace")
        result.update(extract_evidence(agent, text))
        result["exit_code"] = process.returncode
        result["numerical_checks"] = grade(task, run_dir / "workspace", oracle)
        evidence_path = run_dir / "workspace" / "evidence.json"
        claimed = [] if evidence_path.is_symlink() else read_json(evidence_path).get("selected_skills", [])
        known_skills = {item["name"] for item in oracle["catalog"]}
        claimed = [s for s in claimed if isinstance(s, str) and s in known_skills] if isinstance(claimed, list) else []
        result["claimed_skills"] = claimed
        observed = TASKS[task] in result["observed_skill_reads"]
        native_reads = [entry["skill"] for entry in result["skill_read_evidence"]
                        if entry["path"].startswith((".agents/skills/", "/workspace/.agents/skills/"))]
        result["native_activation_verified"] = (args.mode == "native" and
                                                  result["native_discovery"]["passed"] and TASKS[task] in native_reads)
        result["skill_selection_verified"] = (result["native_activation_verified"] if args.mode == "native"
                                               else TASKS[task] in claimed and observed)
        result["skill_content_sha256"] = {entry["name"]: entry["sha256"] for entry in oracle["catalog"]
                                           if entry["name"] in result["observed_skill_reads"]}
        if not timed_out and process.returncode == 0 and result["numerical_checks"]["passed"] and result["skill_selection_verified"]:
            result.update(status="passed", reason=None)
        else:
            reason = classify_failure(text + "\n" + errors, timed_out, process.returncode)
            blocked = reason in {"authentication_unavailable", "quota_or_rate_limit", "isolation_unavailable"}
            result.update(status="blocked" if blocked else "failed", reason=reason)
            if "OAuth session expired and could not be refreshed" in text:
                result["blocker_detail"] = "OAuth session expired and could not be refreshed; no model task completed."
        result["transcript_sha256"] = digest(stdout_path)
        result["artifacts"] = {p.name: digest(p) for p in (run_dir / "workspace").iterdir()
                               if p.is_file() and not p.is_symlink() and p.name not in {"TASK.md", "skill-catalog.json"}}
        result["source_retained"] = "solution.py" in result["artifacts"]
        result["source_replay_verified"] = False
    finally:
        # CLI refreshes can rewrite copied credentials; remove entire private state.
        shutil.rmtree(state)
    result["duration_seconds"] = round(time.monotonic() - start, 3)
    print(f"{agent}/{task}: {result['status']} ({result['reason'] or 'accepted'}); private artifacts: {run_dir}", file=sys.stderr)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agents", nargs="+", choices=AGENTS, default=["codex"])
    parser.add_argument("--mode", choices=("explicit-file", "native"), default="explicit-file")
    parser.add_argument("--skill-source", type=Path, default=ROOT,
                        help="Public skill checkout/snapshot; task protocols still come from this evaluator")
    parser.add_argument("--tasks", nargs="+", choices=TASKS, default=list(TASKS))
    parser.add_argument("--python", type=Path, required=True, help="Existing isolated scientific Python")
    parser.add_argument("--cli", action="append", default=[], metavar="AGENT=PATH")
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--max-budget-usd", type=float, default=1.5, help="Per Claude task; Codex uses timeout only")
    parser.add_argument("--seed", type=int, default=20260914)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.timeout <= 0 or args.max_budget_usd <= 0:
        parser.error("timeout and budget must be positive")
    args.python = args.python.absolute()
    try:
        runtime = python_runtime(args.python)
        overrides = dict(value.split("=", 1) for value in args.cli)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        parser.error(str(exc))
    report = {"schema_version": 2,
              "protocol_version": NATIVE_PROTOCOL_VERSION if args.mode == "native" else PROTOCOL_VERSION,
              "recorded_at": datetime.now(timezone.utc).isoformat(),
              "evaluation_mode": args.mode, "selection_tested": True,
              "native_activation_tested": args.mode == "native",
              "scope": ("native Codex discovery and implicit selection from task-only prompts"
                        if args.mode == "native" else "explicit skill-library selection; not native discovery"),
              "runtime": {key: runtime[key] for key in ("python", "libraries")},
              "results": []}
    for agent in args.agents:
        cli = overrides.get(agent) or shutil.which(CLI_NAMES[agent])
        reason = ("cli_missing" if not cli or not Path(cli).is_file() else
                  "adapter_not_implemented" if agent not in SUPPORTED else
                  "native_adapter_not_implemented" if args.mode == "native" and agent != "codex" else
                  "isolation_unavailable" if not shutil.which("bwrap") else None)
        version = None
        if not reason:
            version_result = subprocess.run([cli, "--version"], capture_output=True, text=True, timeout=15)
            match = re.search(r"\b\d+\.\d+\.\d+(?:[-.][\w.-]+)?", version_result.stdout)
            version = match.group(0) if match else "unknown"
        preceding_blocker = None
        for task in args.tasks:
            result = ({"agent": agent, "task": task, "status": "not-run", "reason": reason}
                      if reason else
                      {"agent": agent, "task": task, "status": "not-run",
                       "reason": preceding_blocker["reason"], "blocked_by_task": preceding_blocker["task"]}
                      if preceding_blocker else run_one(agent, task, Path(cli).absolute(), args, runtime))
            if result["status"] == "blocked":
                preceding_blocker = result
            result["cli_version"] = version
            report["results"].append(result)
            write_json(args.output, report)
    return 0 if all(r["status"] == "passed" for r in report["results"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
