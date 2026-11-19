import json
import re
import unittest
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMO_PATH = ROOT / "examples" / "ads-personal-assistant-os-demo-v0.1.json"
SCHEMA_PATH = ROOT / "schemas" / "ads-personal-assistant-os-demo-v0.1.schema.json"
PROTO = ROOT / "prototype" / "personal-assistant-os"
INDEX = PROTO / "index.html"
DATA_JS = PROTO / "demo-data.js"
APP_JS = PROTO / "app.js"
CORE_JS = PROTO / "core.js"


class ViewButtonParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.views = set()
        self.assets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-view" in attrs:
            self.views.add(attrs["data-view"])
        if tag == "script" and attrs.get("src"):
            self.assets.append(attrs["src"])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.assets.append(attrs.get("href"))


class PersonalAssistantOSPrototypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.demo = json.loads(DEMO_PATH.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.index = INDEX.read_text(encoding="utf-8")
        cls.app = APP_JS.read_text(encoding="utf-8")
        cls.core = CORE_JS.read_text(encoding="utf-8")
        cls.data_js = DATA_JS.read_text(encoding="utf-8")

    def test_demo_dataset_matches_json_schema(self):
        from jsonschema import Draft202012Validator, FormatChecker
        Draft202012Validator.check_schema(self.schema)
        validator = Draft202012Validator(self.schema, format_checker=FormatChecker())
        errors = sorted(validator.iter_errors(self.demo), key=lambda e: list(e.path))
        self.assertEqual([], [f"{list(e.path)}: {e.message}" for e in errors])

    def test_demo_data_bundle_matches_canonical_fixture(self):
        prefix = "window.ADS_DEMO_DATA = "
        self.assertIn(prefix, self.data_js)
        payload = self.data_js.split(prefix, 1)[1].rsplit(";", 1)[0]
        bundled = json.loads(payload)
        self.assertEqual(self.demo, bundled)

    def test_journey_contains_30_consecutive_days(self):
        days = self.demo["journey"]
        self.assertEqual(30, len(days))
        self.assertEqual(list(range(1, 31)), [x["day_index"] for x in days])
        parsed = [date.fromisoformat(x["date"]) for x in days]
        self.assertEqual([parsed[0] + timedelta(days=i) for i in range(30)], parsed)

    def test_all_event_sources_resolve(self):
        source_ids = {x["source_id"] for x in self.demo["sources"]}
        for event in self.demo["events"]:
            self.assertIn(event["source_id"], source_ids, event["event_id"])

    def test_all_derived_references_resolve(self):
        event_ids = {x["event_id"] for x in self.demo["events"]}
        for collection in ("memories", "intents", "actions"):
            for item in self.demo[collection]:
                for ref in item["source_event_refs"]:
                    self.assertIn(ref, event_ids, f"{collection}: {item}")

        for day in self.demo["journey"]:
            for ref in day["event_refs"]:
                self.assertIn(ref, event_ids, f"journey day {day['day_index']}")

    def test_inferred_commitment_is_not_active(self):
        inferred = [
            x for x in self.demo["intents"]
            if x["confirmation_status"] == "inferred_candidate"
        ]
        self.assertTrue(inferred)
        for item in inferred:
            self.assertEqual("proposed", item["status"])
            self.assertEqual("待确认", item["owner"])

    def test_l2_and_l3_actions_require_pending_approval(self):
        high_risk = [x for x in self.demo["actions"] if x["risk_tier"] in {"L2", "L3"}]
        self.assertTrue(high_risk)
        for action in high_risk:
            self.assertTrue(action["approval_required"])
            self.assertEqual("pending", action["approval_status"])
            self.assertEqual("not_started", action["execution_status"])

    def test_personal_scope_and_recording_are_private_by_default(self):
        policy = self.demo["policy"]
        self.assertEqual("personal_only", policy["context_default"])
        self.assertFalse(policy["enterprise_projection"])
        self.assertFalse(policy["auto_recording"])

    def test_five_workspaces_are_present_in_semantic_navigation(self):
        parser = ViewButtonParser()
        parser.feed(self.index)
        self.assertEqual({"today", "inbox", "timeline", "goals", "myai"}, parser.views)

    def test_static_assets_exist(self):
        parser = ViewButtonParser()
        parser.feed(self.index)
        for asset in parser.assets:
            self.assertTrue((PROTO / asset).exists(), asset)

    def test_demo_frontend_does_not_connect_to_external_services(self):
        combined = self.app + self.core + self.data_js
        forbidden = [
            "fetch(", "XMLHttpRequest", "WebSocket",
            "navigator.mediaDevices", "getUserMedia(", "localStorage", "sessionStorage"
        ]
        for token in forbidden:
            self.assertNotIn(token, combined)

    def test_frontend_explains_demo_boundary(self):
        self.assertIn("不连接真实钉钉", self.index)
        self.assertIn("模拟", self.index)
        self.assertIn("没有执行真实写入", self.app)

    def test_required_interactions_are_implemented(self):
        for action in (
            "process-inbox", "confirm-memory", "correct-memory", "withdraw-memory",
            "confirm-intent", "reject-intent", "pause-source", "resume-source",
            "revoke-source", "toggle-automation", "confirm-action-approval",
            "confirm-action-rejection", "export-session", "reset-demo"
        ):
            self.assertIn(action, self.app)

    def test_core_logic_has_no_external_execution_adapter(self):
        self.assertIn("function approveAction", self.core)
        self.assertIn("execution_status = \"not_started\"", self.core)
        self.assertIn("never performs an external write", self.core)


if __name__ == "__main__":
    unittest.main()
