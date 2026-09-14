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
from scripts.evaluate_agents import classify_failure, extract_evidence, stage_workspace, sandbox_command, main


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
        self.assertEqual(len(json.loads((workspace / "skill-catalog.json").read_text())), 36)
        self.assertIn("expected", oracle)


class EvidenceTests(unittest.TestCase):
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
