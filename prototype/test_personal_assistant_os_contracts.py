import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "ads-personal-assistant-daily-brief-v0.1.schema.json"
EXAMPLE_PATH = ROOT / "examples" / "ads-personal-assistant-os-daily-brief-v0.1.json"


class PersonalAssistantOSContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema, format_checker=FormatChecker())

    def test_daily_brief_matches_schema(self):
        errors = sorted(self.validator.iter_errors(self.example), key=lambda e: list(e.path))
        self.assertEqual([], [f"{list(e.path)}: {e.message}" for e in errors])

    def test_inferred_attention_is_not_silently_confirmed(self):
        inferred = [
            item for item in self.example["attention_items"]
            if item["assertion_status"] == "inferred"
        ]
        pending_refs = {
            ref
            for item in self.example["pending_confirmations"]
            for ref in item["source_refs"]
        }
        self.assertTrue(inferred)
        for item in inferred:
            self.assertTrue(set(item["source_refs"]).intersection(pending_refs))

    def test_personal_context_defaults_to_personal_only(self):
        self.assertEqual("personal_only", self.example["policy"]["personal_context_default"])

    def test_digest_does_not_force_interruptions(self):
        self.assertEqual("digest_only", self.example["policy"]["notification_mode"])

    def test_focus_items_are_bounded(self):
        self.assertLessEqual(len(self.example["focus_items"]), 5)
        self.assertLessEqual(len(self.example["suggestions"]), 3)

    def test_all_presented_items_have_source_refs(self):
        collections = ["focus_items", "upcoming", "attention_items", "pending_confirmations"]
        for collection in collections:
            for item in self.example[collection]:
                self.assertTrue(item["source_refs"], f"{collection}: {item.get('item_id')}")


if __name__ == "__main__":
    unittest.main()
