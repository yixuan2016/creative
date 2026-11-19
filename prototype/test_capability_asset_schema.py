"""Validate the capability asset manifest contract and the published example."""
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "ads-capability-asset-v0.1.schema.json"
EXAMPLE_PATH = ROOT / "examples" / "ads-capability-project-risk-triage-v0.1.json"


class CapabilityAssetSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        cls.example = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
        cls.validator = Draft202012Validator(
            cls.schema,
            format_checker=FormatChecker(),
        )

    def test_schema_definition_is_valid(self):
        Draft202012Validator.check_schema(self.schema)

    def test_example_matches_manifest_schema(self):
        self.validator.validate(self.example)

    def test_candidate_does_not_claim_portability_without_evidence(self):
        profile = self.example["portability_profile"]
        self.assertEqual(profile["status"], "not_yet_validated")
        self.assertEqual(profile["validated_levels"], [])

    def test_manifest_declares_non_applicability_and_prohibited_actions(self):
        self.assertTrue(self.example["non_applicability"])
        self.assertTrue(self.example["prohibited_actions"])

    def test_manifest_preserves_provenance_and_governance_review(self):
        self.assertTrue(self.example["provenance"]["sources"])
        self.assertTrue(
            all(source["authorized_for_derivation"] for source in self.example["provenance"]["sources"])
        )
        self.assertIn(
            self.example["governance"]["privacy_review"],
            {"pending", "approved", "restricted", "not_required"},
        )

    def test_unknown_top_level_property_is_rejected(self):
        invalid = dict(self.example)
        invalid["unreviewed_shortcut"] = True
        with self.assertRaises(ValidationError):
            self.validator.validate(invalid)

    def test_missing_non_applicability_is_rejected(self):
        invalid = dict(self.example)
        invalid.pop("non_applicability")
        with self.assertRaises(ValidationError):
            self.validator.validate(invalid)


if __name__ == "__main__":
    unittest.main()
