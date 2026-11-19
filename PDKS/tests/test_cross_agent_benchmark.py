import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "pdks-personal-knowledge"
BENCH = SKILL_ROOT / "benchmarks"

class CrossAgentBenchmarkTests(unittest.TestCase):
    def test_benchmark_has_twelve_synthetic_cases(self):
        manifest = json.loads((BENCH / "benchmark-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["synthetic_cases"], 12)
        for name in manifest["case_files"]:
            case = json.loads((BENCH / "cases" / name).read_text(encoding="utf-8"))
            self.assertIn("case_id", case)
            self.assertIn("expected_record_types", case)
            self.assertIn("review_focus", case)

    def test_evaluator_fixture_passes(self):
        result = subprocess.run([
            sys.executable, str(SKILL_ROOT / "scripts" / "evaluate_benchmark.py"),
            "--case", str(BENCH / "fixtures/fixture-case.json"),
            "--candidate", str(BENCH / "fixtures/fixture-candidate.json")
        ], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "machine_pass")
        self.assertTrue(report["human_review_required"])

    def test_evaluator_rejects_privacy_boundary_violation(self):
        result = subprocess.run([
            sys.executable, str(SKILL_ROOT / "scripts" / "evaluate_benchmark.py"),
            "--case", str(BENCH / "fixtures/fixture-case.json"),
            "--candidate", str(BENCH / "fixtures/fixture-candidate-bad-privacy.json")
        ], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "machine_review_required")
        failed = {item["name"] for item in report["machine_checks"] if not item["passed"]}
        self.assertIn("least_privilege_owner_only", failed)

    def test_agent_prompts_do_not_leak_gold_labels(self):
        manifest = json.loads((BENCH / "benchmark-manifest.json").read_text(encoding="utf-8"))
        for name in manifest["case_files"]:
            case = json.loads((BENCH / "cases" / name).read_text(encoding="utf-8"))
            prompt = (BENCH / "prompts" / (case["case_id"] + ".md")).read_text(encoding="utf-8")
            self.assertIn(case["input_text"], prompt)
            self.assertNotIn("expected_record_types", prompt)
            self.assertNotIn("required_terms", prompt)
            self.assertNotIn("forbidden_terms", prompt)

    def test_benchmark_protocol_requires_two_hosts_and_repeats(self):
        manifest = json.loads((BENCH / "benchmark-manifest.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(manifest["recommended_protocol"]["hosts_minimum"], 2)
        self.assertEqual(manifest["recommended_protocol"]["runs_per_case_per_host"], 3)

    def test_skill_declares_new_version_and_stage(self):
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('skill_version: "0.3.4"', skill)
        self.assertIn('runtime_track: "0.5.0"', skill)
        self.assertIn("transitional Skill development", skill)

if __name__ == "__main__":
    unittest.main()
