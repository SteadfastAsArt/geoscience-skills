"""Free, standard-library tests of fixtures, graders and evidence handling."""

import copy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evals.cases import grade, make_fixture, read_segy
from scripts.evaluate_agents import classify_failure, extract_evidence, stage_workspace, sandbox_command, main, summarize_discovery
from scripts.validate_skills import find_skill_dirs


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        (self.work / "solution.py").write_text("# Test artifact, never run an agent.\n")

    def las(self):
        oracle = make_fixture("las-qc", self.work / "inputs")
        (self.work / "result.json").write_text(json.dumps(oracle["expected"]))
        return oracle

    def segy(self):
        oracle = make_fixture("segy-subset", self.work / "inputs")
        source = (self.work / "inputs/survey.sgy").read_bytes()
        stride = 240 + 4 * 12
        records = [source[i:i + stride] for i in range(3600, len(source), stride)]
        selected = [record for record in records if 310 <= struct.unpack_from(">i", record, 188)[0] <= 315]
        (self.work / "subset.sgy").write_bytes(source[:3600] + b"".join(selected))
        return oracle

    def test_las_accepts_null_excluding_statistics(self):
        oracle = self.las()
        self.assertTrue(grade("las-qc", self.work, oracle)["passed"])
        self.assertEqual(oracle["expected"]["curves"]["GR"]["null_count"], 3)
        self.assertEqual(oracle["expected"]["depth"]["duplicate_count"], 1)

    def test_las_rejects_units_nulls_order_and_nonfinite_statistics(self):
        oracle = self.las()
        for section, key, value in (("depth", "unit", "FT"),
                                    ("depth", "strictly_increasing", True),
                                    ("GR", "null_count", 0), ("RHOB", "mean", float("nan"))):
            actual = copy.deepcopy(oracle["expected"])
            (actual["depth"] if section == "depth" else actual["curves"][section])[key] = value
            (self.work / "result.json").write_text(json.dumps(actual))
            self.assertFalse(grade("las-qc", self.work, oracle)["passed"], (section, key))

    def test_segy_accepts_exact_noncontiguous_subset(self):
        oracle = self.segy()
        self.assertTrue(grade("segy-subset", self.work, oracle)["passed"])
        self.assertEqual(len(read_segy(self.work / "subset.sgy")["traces"]), 5)

    def test_segy_rejects_samples_headers_text_and_trace_order(self):
        oracle = self.segy()
        path = self.work / "subset.sgy"
        correct = path.read_bytes()
        for offset in (0, 3216, 3600 + 70, 3600 + 188, 3600 + 240, 3600 + 243):
            damaged = bytearray(correct)
            damaged[offset] ^= 1
            path.write_bytes(damaged)
            self.assertFalse(grade("segy-subset", self.work, oracle)["passed"], offset)
        stride = 288
        path.write_bytes(correct[:3600] + correct[3600 + stride:3600 + stride * 2]
                         + correct[3600:3600 + stride] + correct[3600 + stride * 2:])
        self.assertFalse(grade("segy-subset", self.work, oracle)["passed"])

    def test_missing_malformed_output_and_modified_input_fail(self):
        oracle = self.las()
        (self.work / "inputs/well.las").write_text("changed")
        self.assertIn("input: changed or missing", grade("las-qc", self.work, oracle)["failures"])
        (self.work / "result.json").write_text("not-json")
        self.assertFalse(grade("las-qc", self.work, oracle)["passed"])
        (self.work / "result.json").unlink()
        self.assertFalse(grade("las-qc", self.work, oracle)["passed"])

    def test_output_symlink_is_not_read_or_hashed_by_parent(self):
        oracle = self.las()
        target = self.work / "parent-only.json"
        target.write_text(json.dumps(oracle["expected"]))
        (self.work / "result.json").unlink()
        (self.work / "result.json").symlink_to(target)
        result = grade("las-qc", self.work, oracle)
        self.assertFalse(result["passed"])
        self.assertIsNone(result["output_sha256"])

    def test_fixture_seed_is_reproducible_but_changes_data(self):
        a = make_fixture("las-qc", self.work / "a", 1)
        b = make_fixture("las-qc", self.work / "b", 1)
        c = make_fixture("las-qc", self.work / "c", 2)
        self.assertEqual(a, b)
        self.assertNotEqual(a["input_sha256"], c["input_sha256"])

    def test_staged_prompt_has_no_oracle_or_expected_skill(self):
        workspace = self.work / "workspace"
        oracle = stage_workspace("segy-subset", workspace, 1)
        prompt = (workspace / "TASK.md").read_text()
        self.assertNotIn('"expected"', prompt)
        self.assertNotIn("skills/segyio", prompt)
        self.assertFalse((workspace / "cases.py").exists())
        self.assertEqual(len(json.loads((workspace / "skill-catalog.json").read_text())), len(find_skill_dirs(ROOT)))
        self.assertIn("expected", oracle)

    def test_native_staging_has_no_catalog_or_skill_instruction_in_prompt(self):
        workspace = self.work / "native"
        oracle = stage_workspace("segy-subset", workspace, 1, mode="native")
        prompt = (workspace / "TASK.md").read_text()
        for forbidden in ("skill-catalog", "SKILL.md", "selected_skills", "segyio", ".agents"):
            self.assertNotIn(forbidden, prompt)
        self.assertFalse((workspace / "skill-catalog.json").exists())
        self.assertFalse((workspace / "skills").exists())
        self.assertEqual(len(list((workspace / ".agents/skills").glob("*/SKILL.md"))), len(find_skill_dirs(ROOT)))
        self.assertEqual(oracle["protocol_version"], "native-1")

    def test_workflow_accepts_nulls_clipping_and_gap_preservation(self):
        oracle = make_fixture("formation-evaluation", self.work / "inputs")
        for name, expected in oracle["expected"].items():
            (self.work / name).write_text(json.dumps(expected))
        self.assertTrue(grade("formation-evaluation", self.work, oracle)["passed"])
        rows = oracle["expected"]["evaluated.json"]["rows"]
        self.assertTrue(rows[1]["sw_clipped"])
        self.assertIsNone(rows[3]["vsh"])
        self.assertIsNone(rows[8]["phi_d"])
        self.assertFalse(rows[10]["qc_valid"])

    def test_workflow_rejects_bridged_gaps_and_zero_filled_missing_values(self):
        oracle = make_fixture("formation-evaluation", self.work / "inputs")
        for name, expected in oracle["expected"].items():
            (self.work / name).write_text(json.dumps(expected))
        actual = copy.deepcopy(oracle["expected"]["evaluated.json"])
        actual["rows"][3]["vsh"] = 0
        (self.work / "evaluated.json").write_text(json.dumps(actual))
        self.assertFalse(grade("formation-evaluation", self.work, oracle)["passed"])
        (self.work / "evaluated.json").write_text(json.dumps(oracle["expected"]["evaluated.json"]))
        actual = copy.deepcopy(oracle["expected"]["lithology.json"])
        actual["intervals"][0]["base_m"] = 1503.0
        (self.work / "lithology.json").write_text(json.dumps(actual))
        self.assertFalse(grade("formation-evaluation", self.work, oracle)["passed"])

    def test_workflow_checks_parameter_file_preservation(self):
        oracle = make_fixture("formation-evaluation", self.work / "inputs")
        (self.work / "inputs/formation-parameters.json").write_text("{}")
        self.assertIn("input formation-parameters.json: changed or missing",
                      grade("formation-evaluation", self.work, oracle)["failures"])


class EvidenceTests(unittest.TestCase):
    def test_native_scanner_requires_enabled_exact_repository_path(self):
        catalog = [{"name": "lasio", "path": ".agents/skills/lasio/SKILL.md"}]
        skill = {"name": "lasio", "path": "/workspace/.agents/skills/lasio/SKILL.md", "scope": "repo", "enabled": True}
        def response(item):
            return {"result": {"data": [{"cwd": "/workspace", "skills": [item], "errors": []}]}}
        self.assertTrue(summarize_discovery(response(skill), catalog)["passed"])
        for key, value in (("enabled", False), ("scope", "user"), ("path", "/workspace/wrong/SKILL.md")):
            self.assertFalse(summarize_discovery(response({**skill, key: value}), catalog)["passed"])

    def test_native_tool_read_retains_native_path_evidence(self):
        event = json.dumps({"type": "item.completed", "item": {"type": "command_execution",
            "command": "cat /workspace/.agents/skills/lasio/SKILL.md", "exit_code": 0,
            "aggregated_output": "---\nname: lasio\ndescription: Read LAS files\n---"}})
        evidence = extract_evidence("codex", event)
        self.assertEqual(evidence["observed_skill_reads"], ["lasio"])
        self.assertEqual(evidence["skill_read_evidence"][0]["path"], "/workspace/.agents/skills/lasio/SKILL.md")

    def test_double_quoted_shell_sed_native_read_is_observed(self):
        event = json.dumps({"type": "item.completed", "item": {"type": "command_execution",
            "command": '/bin/bash -lc "sed -n \'1,240p\' /workspace/.agents/skills/lasio/SKILL.md"',
            "exit_code": 0, "aggregated_output": "---\nname: lasio\ndescription: LAS I/O\n---"}})
        evidence = extract_evidence("codex", event)
        self.assertEqual(evidence["observed_skill_reads"], ["lasio"])

    def test_echoing_a_reader_command_and_frontmatter_is_not_read_evidence(self):
        event = json.dumps({"type": "item.completed", "item": {"type": "command_execution",
            "command": "echo 'cat skills/lasio/SKILL.md name: lasio'", "exit_code": 0,
            "aggregated_output": "cat skills/lasio/SKILL.md name: lasio"}})
        self.assertEqual(extract_evidence("codex", event)["observed_skill_reads"], [])

    def test_blocked_first_task_prevents_duplicate_agent_attempt(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            runtime = {"python": "3.11", "libraries": {}}
            with patch("scripts.evaluate_agents.python_runtime", return_value=runtime), \
                 patch("scripts.evaluate_agents.shutil.which", return_value="/usr/bin/true"), \
                 patch("scripts.evaluate_agents.subprocess.run", return_value=SimpleNamespace(stdout="2.1.270")), \
                 patch("scripts.evaluate_agents.run_one", return_value={
                     "agent": "claude", "task": "las-qc", "status": "blocked",
                     "reason": "authentication_unavailable"}) as runner:
                code = main(["--agents", "claude", "--python", sys.executable,
                             "--output", str(output)])
            self.assertEqual(code, 1)
            self.assertEqual(runner.call_count, 1)
            results = json.loads(output.read_text())["results"]
            self.assertEqual(results[1]["status"], "not-run")
            self.assertEqual(results[1]["blocked_by_task"], "las-qc")

    def test_sandbox_mounts_private_home_and_readonly_inputs_not_host_root(self):
        with tempfile.TemporaryDirectory() as directory:
            run = Path(directory)
            command, env, _ = sandbox_command("claude", Path("/usr/bin/true"),
                                              Path("/usr/bin/python3"),
                                              {"prefix": "/usr", "base_prefix": "/usr"}, run, 1)
            mounts = [command[i + 1:i + 3] for i, part in enumerate(command)
                      if part in ("--ro-bind", "--bind")]
            self.assertNotIn(["/", "/"], mounts)
            self.assertIn([str(run / "state/home"), os.environ["HOME"]], mounts)
            self.assertIn([str(run / "workspace/inputs"), "/workspace/inputs"], mounts)
            self.assertEqual(env["HOME"], os.environ["HOME"])
            self.assertNotIn("CODEX_THREAD_ID", env)

    def test_unsafe_runtime_mount_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                sandbox_command("claude", Path("/usr/bin/true"), Path("/usr/bin/python3"),
                                {"prefix": "/", "base_prefix": "/usr"}, Path(directory), 1)

    def test_codex_successful_tool_read_required(self):
        def event(command, code, output="name: segyio\ndescription: SEG-Y processing"):
            return json.dumps({"type": "item.completed", "item": {
                "type": "command_execution", "command": command, "exit_code": code,
                "aggregated_output": output}})
        transcript = "\n".join([event("cat skills/lasio/SKILL.md", 1),
                                  event("cat /workspace/skills/segyio/SKILL.md", 0),
                                  event("echo skills/lasio/SKILL.md", 0, "name: lasio"),
                                  event("cat skills/lasio/SKILL.md", 0, "not the skill content")])
        evidence = extract_evidence("codex", transcript)
        self.assertEqual(evidence["observed_skill_reads"], ["segyio"])
        self.assertEqual(evidence["tool_commands"][0]["command"], "cat /workspace/skills/segyio/SKILL.md")

    def test_sensitive_or_complex_commands_publish_only_digest(self):
        event = json.dumps({"type": "item.completed", "item": {
            "type": "command_execution", "command": "cat /home/private/credentials", "exit_code": 0}})
        self.assertNotIn("command", extract_evidence("codex", event)["tool_commands"][0])

    def test_claude_pairs_read_with_successful_result(self):
        transcript = "\n".join(map(json.dumps, [
            {"message": {"content": [{"type": "tool_use", "id": "1", "name": "Read",
               "input": {"file_path": "/workspace/skills/lasio/SKILL.md"}}]}},
            {"message": {"content": [{"type": "tool_result", "tool_use_id": "1",
               "content": "name: lasio\ndescription: LAS read/write", "is_error": False}]}}]))
        self.assertEqual(extract_evidence("claude", transcript)["observed_skill_reads"], ["lasio"])
        self.assertEqual(extract_evidence("claude", transcript.splitlines()[0])["observed_skill_reads"], [])

    def test_self_report_is_not_observed_evidence(self):
        event = json.dumps({"type": "result", "result": "I used skills/lasio/SKILL.md"})
        self.assertEqual(extract_evidence("claude", event)["observed_skill_reads"], [])

    def test_failures_are_classified_without_publishing_secret_messages(self):
        self.assertEqual(classify_failure("Invalid API key secret-value", False, 1), "authentication_unavailable")
        self.assertEqual(classify_failure("bwrap: cannot mount", False, 1), "isolation_unavailable")
        self.assertEqual(classify_failure("", True, -9), "timeout")


if __name__ == "__main__":
    unittest.main()
