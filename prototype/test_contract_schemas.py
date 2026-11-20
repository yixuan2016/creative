"""Validate seed records and generated context against the canonical JSON Schema."""
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker

from ads_context_engine import ContextEngine, load_seed


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "ads-work-context-v0.1.schema.json"


class ContractSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.seed = load_seed()

    @classmethod
    def validator(cls, definition_name):
        scoped_schema = {
            "$schema": cls.schema["$schema"],
            "$defs": cls.schema["$defs"],
            "$ref": "#/$defs/" + definition_name,
        }
        return Draft202012Validator(
            scoped_schema,
            format_checker=FormatChecker(),
        )

    def test_schema_definition_is_valid(self):
        Draft202012Validator.check_schema(self.schema)

    def test_seed_events_match_work_event_schema(self):
        validator = self.validator("WorkEvent")
        for event in self.seed["events"]:
            validator.validate(event)

    def test_seed_objects_match_business_object_schema(self):
        validator = self.validator("BusinessObject")
        for item in self.seed["objects"]:
            validator.validate(item)

    def test_seed_grants_match_authorization_grant_schema(self):
        validator = self.validator("AuthorizationGrant")
        for grant in self.seed["grants"]:
            validator.validate(grant)

    def test_generated_context_matches_context_package_schema(self):
        engine = ContextEngine(self.seed)
        engine.ingest_many(self.seed["events"])
        context = engine.build_context(self.seed["context_request"])
        self.validator("ContextPackage").validate(context)


if __name__ == "__main__":
    unittest.main()
