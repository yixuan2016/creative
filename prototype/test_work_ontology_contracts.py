"""Contract tests for ADS-WORK-08 ontology and personal-to-enterprise projection."""
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker, ValidationError


ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY_SCHEMA = json.loads((ROOT / "schemas/ads-work-ontology-v0.1.schema.json").read_text(encoding="utf-8"))
PERSONAL_SCHEMA = json.loads((ROOT / "schemas/ads-personal-context-event-v0.1.schema.json").read_text(encoding="utf-8"))
WORK_CONTEXT_SCHEMA = json.loads((ROOT / "schemas/ads-work-context-v0.1.schema.json").read_text(encoding="utf-8"))
ONTOLOGY = json.loads((ROOT / "ontologies/ads-work-ontology-v0.1.json").read_text(encoding="utf-8"))
EXAMPLE = json.loads((ROOT / "examples/ads-personal-to-enterprise-event-projection-v0.1.json").read_text(encoding="utf-8"))


class WorkOntologyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ontology_validator = Draft202012Validator(ONTOLOGY_SCHEMA, format_checker=FormatChecker())
        cls.personal_validator = Draft202012Validator(PERSONAL_SCHEMA, format_checker=FormatChecker())
        work_event_root = {
            "$schema": WORK_CONTEXT_SCHEMA["$schema"],
            "$defs": WORK_CONTEXT_SCHEMA["$defs"],
            "$ref": "#/$defs/WorkEvent",
        }
        cls.work_event_validator = Draft202012Validator(work_event_root, format_checker=FormatChecker())

    def test_schema_definitions_are_valid(self):
        Draft202012Validator.check_schema(ONTOLOGY_SCHEMA)
        Draft202012Validator.check_schema(PERSONAL_SCHEMA)

    def test_ontology_catalog_matches_manifest_schema(self):
        self.ontology_validator.validate(ONTOLOGY)

    def test_ontology_has_five_unique_layers(self):
        layers = ONTOLOGY["layers"]
        self.assertEqual(len(layers), 5)
        self.assertEqual({x["layer_id"] for x in layers}, {"L1", "L2", "L3", "L4", "L5"})

    def test_all_layer_concepts_resolve(self):
        class_ids = {x["class_id"] for x in ONTOLOGY["classes"]}
        for layer in ONTOLOGY["layers"]:
            for concept in layer["concepts"]:
                self.assertIn(concept, class_ids, f"Unresolved layer concept: {concept}")

    def test_all_parent_class_references_resolve(self):
        class_ids = {x["class_id"] for x in ONTOLOGY["classes"]}
        for item in ONTOLOGY["classes"]:
            parent = item["parent_class"]
            if parent is not None:
                self.assertIn(parent, class_ids, f"Unresolved parent class: {parent}")

    def test_relation_domain_and_range_resolve(self):
        class_ids = {x["class_id"] for x in ONTOLOGY["classes"]}
        for relation in ONTOLOGY["relations"]:
            self.assertIn(relation["domain"], class_ids, relation["predicate"])
            self.assertIn(relation["range"], class_ids, relation["predicate"])

    def test_event_taxonomy_class_and_type_resolve(self):
        class_ids = {x["class_id"] for x in ONTOLOGY["classes"]}
        event_types = {x["event_type"] for x in ONTOLOGY["event_taxonomy"]}
        for item in ONTOLOGY["event_taxonomy"]:
            self.assertIn(item["event_class"], class_ids, item["event_type"])
        for event in EXAMPLE["personal_events"]:
            self.assertIn(event["event_type"], event_types)

    def test_personal_events_match_personal_event_contract(self):
        for event in EXAMPLE["personal_events"]:
            self.personal_validator.validate(event)

    def test_enterprise_projection_matches_existing_work_event_contract(self):
        self.work_event_validator.validate(EXAMPLE["enterprise_projection"]["event"])

    def test_life_event_is_private_and_not_projected(self):
        life_event = next(x for x in EXAMPLE["personal_events"] if x["event_class"] == "personal.LifeEvent")
        self.assertEqual(life_event["sharing_policy"]["default_scope"], "personal_only")
        self.assertFalse(life_event["sharing_policy"]["projection_allowed"])
        self.assertIsNone(life_event["sharing_policy"]["authorization_ref"])
        serialized_projection = json.dumps(EXAMPLE["enterprise_projection"], ensure_ascii=False)
        self.assertNotIn(life_event["personal_event_id"], serialized_projection)
        self.assertNotIn(life_event["payload"]["summary"], serialized_projection)

    def test_enterprise_projection_is_minimized_and_authorized(self):
        work_event = next(x for x in EXAMPLE["personal_events"] if x["event_class"] == "personal.WorkEvent")
        projection = EXAMPLE["enterprise_projection"]
        enterprise_event = projection["event"]
        self.assertTrue(work_event["sharing_policy"]["projection_allowed"])
        self.assertTrue(work_event["sharing_policy"]["authorization_ref"])
        self.assertEqual(projection["authorization_ref"], enterprise_event["authorization_ref"])
        self.assertEqual(projection["purpose"], "project_delivery_follow_up")
        self.assertNotIn("private_note", enterprise_event["payload"])
        self.assertNotIn(work_event["personal_event_id"], json.dumps(enterprise_event, ensure_ascii=False))
        self.assertTrue(projection["lineage_token"].startswith("lineage:opaque-"))

    def test_personal_event_cannot_enable_projection_without_authorization(self):
        event = next(x for x in EXAMPLE["personal_events"] if x["event_class"] == "personal.WorkEvent")
        invalid = json.loads(json.dumps(event))
        invalid["sharing_policy"]["authorization_ref"] = None
        with self.assertRaises(ValidationError):
            self.personal_validator.validate(invalid)

    def test_mapping_and_class_identifiers_are_unique(self):
        class_ids = [x["class_id"] for x in ONTOLOGY["classes"]]
        rule_ids = [x["rule_id"] for x in ONTOLOGY["mapping_rules"]]
        predicates = [x["predicate"] for x in ONTOLOGY["relations"]]
        self.assertEqual(len(class_ids), len(set(class_ids)))
        self.assertEqual(len(rule_ids), len(set(rule_ids)))
        self.assertEqual(len(predicates), len(set(predicates)))


if __name__ == "__main__":
    unittest.main()
