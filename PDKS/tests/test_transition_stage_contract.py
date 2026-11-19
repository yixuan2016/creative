import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "pdks-personal-knowledge"

class TransitionalStageContractTests(unittest.TestCase):
    def test_stage_validator_passes(self):
        result = subprocess.run(
            [sys.executable, str(SKILL_ROOT / "scripts" / "validate_skill_stage.py"), "--json"],
            capture_output=True, text=True, check=False
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["stage"], "transitional_skill_development")
        self.assertEqual(report["status"], "valid")

    def test_skill_version_and_maturity_are_explicit(self):
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn('skill_version: "0.3.4"', text)
        self.assertIn('maturity: "experimental"', text)
        self.assertIn("transitional Skill development", text)

    def test_ontology_layering_is_proposal_only(self):
        profile = json.loads((SKILL_ROOT / "protocols/pdks-development-stage-profile-0.1.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["ontology_layering"]["status"], "research_proposal_only")
        self.assertFalse(profile["ontology_layering"]["may_change_published_core"])

    def test_cross_host_runs_are_not_falsely_claimed(self):
        profile = json.loads((SKILL_ROOT / "protocols/pdks-development-stage-profile-0.1.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["cross_host_validation"]["status"], "protocol_prepared_not_executed")
        self.assertEqual(profile["cross_host_validation"]["actual_runs"], 0)

    def test_capture_runtime_remains_experimental_and_local(self):
        profile = json.loads((SKILL_ROOT / "protocols/pdks-development-stage-profile-0.1.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["capture_runtime"]["runtime_version"], "0.1.0")
        self.assertEqual(profile["capture_runtime"]["status"], "experimental_local_reference_implementation")
        self.assertEqual(profile["capability_matrix"]["native_provider_connectors"], "not_implemented")

    def test_no_new_stable_ontology_version(self):
        profile = json.loads((SKILL_ROOT / "protocols/pdks-development-stage-profile-0.1.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["release"]["ontology_version"], "0.2.1")
        self.assertEqual(profile["frozen_baselines"]["ontology"], "0.2.1")

if __name__ == "__main__":
    unittest.main()
