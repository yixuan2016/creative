import json, subprocess, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "skill-development/0.3.2-transition"

class TransitionalStageContractTests(unittest.TestCase):
    def test_stage_validator_passes(self):
        r = subprocess.run([sys.executable, str(BASE/"scripts/validate_skill_stage.py"), "--json"],capture_output=True,text=True)
        self.assertEqual(r.returncode, 0, r.stdout+r.stderr)
        self.assertEqual(json.loads(r.stdout)["status"], "valid")

    def test_ontology_baseline_is_frozen(self):
        p = json.loads((BASE/"pdks-development-stage-profile-0.1.json").read_text(encoding="utf-8"))
        self.assertEqual(p["frozen_baselines"]["ontology"], "0.2.1")

    def test_ontology_layering_is_not_published(self):
        p = json.loads((BASE/"pdks-development-stage-profile-0.1.json").read_text(encoding="utf-8"))
        self.assertEqual(p["ontology_layering"]["status"], "research_proposal_only")
        self.assertFalse(p["ontology_layering"]["may_change_published_core"])

if __name__ == "__main__":
    unittest.main()
