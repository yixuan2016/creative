import importlib.util
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "pdks-personal-knowledge"
SCENARIOS = SKILL / "examples" / "scenarios"

def load_module(name):
    path = SKILL / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def run_main(module, argv):
    old = sys.argv
    output = StringIO()
    try:
        sys.argv = [module.__file__] + argv
        with redirect_stdout(output):
            code = module.main()
        return code, output.getvalue()
    finally:
        sys.argv = old

class ReleaseSmokeTests(unittest.TestCase):
    def test_skill_entry_and_assets(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: pdks-personal-knowledge", text)
        self.assertIn('skill_version: "0.3.4"', text)
        for name in [
            "pdks-0.1-record.schema.json",
            "pdks-event-taxonomy-0.1.json",
            "pdks-core-ontology-0.1.ttl",
            "pdks-core-shapes-0.1.ttl",
            "pdks-json-to-ontology-mapping-0.1.json"
        ]:
            self.assertTrue((SKILL / "assets" / name).exists(), name)
        self.assertTrue((SKILL / "assets" / "ontology" / "0.2.0" / "pdks-core-ontology-0.2.ttl").exists())
        self.assertTrue((SKILL / "assets" / "ontology" / "0.2.1" / "pdks-core-ontology-0.2.ttl").exists())
        self.assertTrue((SKILL / "assets" / "ontology" / "0.2.1" / "ontology-manifest.json").exists())

    def test_all_scenarios_validate(self):
        module = load_module("validate_records")
        code, messages, summary = module.validate(SCENARIOS, strict_refs=True)
        self.assertEqual(code, 0, messages)
        self.assertEqual(summary["records"], 29)
        self.assertEqual(summary["status"], "valid")

    def test_all_scripts_compile(self):
        for f in (SKILL / "scripts").glob("*.py"):
            compile(f.read_text(encoding="utf-8"), str(f), "exec")

    def test_search_and_daily_review(self):
        scenario = SCENARIOS / "voice-meeting"
        search = load_module("search_records")
        code, out = run_main(search, [str(scenario), "语音", "--object-type", "event"])
        self.assertEqual(code, 0)
        self.assertIn('"count": 1', out)
        review = load_module("daily_review")
        code, out = run_main(review, [str(scenario), "--date", "2026-11-18"])
        self.assertEqual(code, 0)
        self.assertIn('"events": 1', out)

    def test_export_verify_and_migration_plan(self):
        scenario = SCENARIOS / "voice-meeting"
        with tempfile.TemporaryDirectory() as td:
            bundle = Path(td) / "voice-meeting.zip"
            plan = Path(td) / "migration-plan.json"
            build = load_module("build_bundle")
            code, _ = run_main(build, ["--records", str(scenario), "--output", str(bundle)])
            self.assertEqual(code, 0)
            verify = load_module("verify_bundle")
            code, out = run_main(verify, [str(bundle)])
            self.assertEqual(code, 0, out)
            self.assertIn('"integrity": "passed"', out)
            migrate = load_module("plan_migration")
            code, _ = run_main(migrate, [str(bundle), "--output", str(plan), "--target-name", "test-target"])
            self.assertEqual(code, 0)
            data = json.loads(plan.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "prepared_not_imported")
            self.assertEqual(data["record_count"], 11)
            self.assertEqual(data["bundle_integrity"], "passed")

if __name__ == "__main__":
    unittest.main()
