"""ADS-WORK-09 personal event, memory, intent and agent action contract tests."""
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, FormatChecker, ValidationError

from personal_memory_engine import PersonalMemoryEngine

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {
    "event": json.loads((ROOT / "schemas/ads-personal-event-ledger-v0.1.schema.json").read_text(encoding="utf-8")),
    "memory": json.loads((ROOT / "schemas/ads-personal-memory-item-v0.1.schema.json").read_text(encoding="utf-8")),
    "intent": json.loads((ROOT / "schemas/ads-personal-intent-object-v0.1.schema.json").read_text(encoding="utf-8")),
    "action": json.loads((ROOT / "schemas/ads-personal-agent-action-v0.1.schema.json").read_text(encoding="utf-8")),
}
EXAMPLE = json.loads((ROOT / "examples/ads-personal-memory-loop-v0.1.json").read_text(encoding="utf-8"))


class PersonalMemoryContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validators = {
            key: Draft202012Validator(schema, format_checker=FormatChecker())
            for key, schema in SCHEMAS.items()
        }

    def test_all_schemas_are_valid(self):
        for schema in SCHEMAS.values():
            Draft202012Validator.check_schema(schema)

    def test_example_event_records_match_schema(self):
        for event in EXAMPLE["event_ledger"]:
            self.validators["event"].validate(event)

    def test_example_memory_items_match_schema(self):
        for memory in EXAMPLE["memory_items"]:
            self.validators["memory"].validate(memory)

    def test_example_intent_matches_schema(self):
        self.validators["intent"].validate(EXAMPLE["intent_objects"][0])

    def test_example_agent_action_matches_schema(self):
        self.validators["action"].validate(EXAMPLE["agent_action_proposal"])

    def test_personal_life_event_is_private(self):
        event = next(x for x in EXAMPLE["event_ledger"] if x["event_type"] == "personal.life.commitment_created")
        self.assertEqual(event["sharing_policy"]["default_scope"], "personal_only")
        self.assertFalse(event["sharing_policy"]["projection_allowed"])

    def test_sensitive_memory_requires_human_review(self):
        memory = next(x for x in EXAMPLE["memory_items"] if x["classification"] == "personal_sensitive")
        self.assertTrue(memory["derivation"]["human_review_required"])
        invalid = json.loads(json.dumps(memory))
        invalid["derivation"]["human_review_required"] = False
        with self.assertRaises(ValidationError):
            self.validators["memory"].validate(invalid)

    def test_candidate_memory_is_not_confirmed_fact(self):
        memory = json.loads(json.dumps(EXAMPLE["memory_items"][0]))
        memory["assertion_status"] = "candidate"
        memory["memory_lifecycle"] = "candidate"
        self.validators["memory"].validate(memory)
        self.assertNotEqual(memory["assertion_status"], "confirmed")

    def test_shareable_memory_requires_authorization(self):
        memory = json.loads(json.dumps(EXAMPLE["memory_items"][0]))
        memory["sharing_policy"].update({
            "shareable": True, "authorization_ref": None, "authorized_purposes": [], "expires_at": None
        })
        with self.assertRaises(ValidationError):
            self.validators["memory"].validate(memory)

    def test_l2_action_requires_approval(self):
        action = json.loads(json.dumps(EXAMPLE["agent_action_proposal"]))
        action["approval"]["required"] = False
        with self.assertRaises(ValidationError):
            self.validators["action"].validate(action)

    def test_connector_capture_requires_authorization_reference(self):
        event = json.loads(json.dumps(EXAMPLE["event_ledger"][0]))
        event["source_refs"][0]["capture_mode"] = "connector_sync"
        event["source_refs"][0]["capture_authorization_ref"] = None
        with self.assertRaises(ValidationError):
            self.validators["event"].validate(event)

    def test_inferred_intent_cannot_be_active_without_confirmation(self):
        intent = json.loads(json.dumps(EXAMPLE["intent_objects"][0]))
        intent["confirmation_status"] = "inferred_candidate"
        intent["status"] = "active"
        with self.assertRaises(ValidationError):
            self.validators["intent"].validate(intent)

    def _engine_with_event(self):
        engine = PersonalMemoryEngine("person-demo-001")
        engine.append_event(EXAMPLE["event_ledger"][0])
        return engine

    def test_ledger_is_idempotent(self):
        engine = self._engine_with_event()
        engine.append_event(EXAMPLE["event_ledger"][0])
        self.assertEqual(len(engine.events), 1)

    def test_event_id_cannot_be_reused_with_different_content(self):
        engine = self._engine_with_event()
        changed = json.loads(json.dumps(EXAMPLE["event_ledger"][0]))
        changed["payload"]["summary"] = "changed"
        with self.assertRaises(ValueError):
            engine.append_event(changed)

    def test_idempotency_key_cannot_be_reused_with_different_content(self):
        engine = self._engine_with_event()
        changed = json.loads(json.dumps(EXAMPLE["event_ledger"][0]))
        changed["event_id"] = "another-event"
        changed["payload"]["summary"] = "changed"
        with self.assertRaises(ValueError):
            engine.append_event(changed)

    def test_non_owner_cannot_append_to_personal_ledger(self):
        engine = PersonalMemoryEngine("person-demo-001")
        event = json.loads(json.dumps(EXAMPLE["event_ledger"][0]))
        event["subject_ref"] = "someone-else"
        with self.assertRaises(PermissionError):
            engine.append_event(event)

    def test_model_derived_memory_starts_as_candidate(self):
        engine = self._engine_with_event()
        memory = engine.derive_memory("pevt-demo-commitment-001", "mem-candidate", "commitment", "Candidate claim")
        self.assertEqual(memory["memory_lifecycle"], "candidate")
        self.assertEqual(memory["assertion_status"], "candidate")

    def test_only_owner_can_confirm_memory(self):
        engine = self._engine_with_event()
        engine.derive_memory("pevt-demo-commitment-001", "mem-candidate", "commitment", "Candidate claim")
        with self.assertRaises(PermissionError):
            engine.confirm_memory("mem-candidate", actor_ref="other-person")
        confirmed = engine.confirm_memory("mem-candidate", actor_ref="person-demo-001")
        self.assertEqual(confirmed["memory_lifecycle"], "active")

    def test_withdrawn_memory_is_not_retrieved(self):
        engine = self._engine_with_event()
        engine.derive_memory("pevt-demo-commitment-001", "mem-active", "commitment", "A confirmed claim", user_confirmed=True)
        engine.withdraw_memory("mem-active", actor_ref="person-demo-001")
        self.assertEqual(engine.build_context(purpose="personal_planning")["memories"], [])

    def test_forgetting_source_suppresses_all_derived_memories(self):
        engine = self._engine_with_event()
        engine.derive_memory("pevt-demo-commitment-001", "mem-one", "commitment", "First claim", user_confirmed=True)
        engine.derive_memory("pevt-demo-commitment-001", "mem-two", "episodic", "Second claim", user_confirmed=True)
        engine.forget_source_event("pevt-demo-commitment-001", actor_ref="person-demo-001")
        self.assertEqual(engine.build_context(purpose="personal_planning")["memories"], [])
        with self.assertRaises(PermissionError):
            engine.derive_memory("pevt-demo-commitment-001", "mem-again", "commitment", "Recreated claim")

    def test_sensitive_memory_is_excluded_by_default(self):
        engine = self._engine_with_event()
        engine.derive_memory("pevt-demo-commitment-001", "mem-sensitive", "episodic", "Sensitive detail", user_confirmed=True, classification="personal_sensitive")
        self.assertEqual(engine.build_context(purpose="personal_planning")["memories"], [])
        self.assertEqual(len(engine.build_context(purpose="personal_planning", include_sensitive=True)["memories"]), 1)

    def test_l2_action_cannot_be_proposed_without_pending_approval(self):
        engine = PersonalMemoryEngine("person-demo-001")
        action = json.loads(json.dumps(EXAMPLE["agent_action_proposal"]))
        action["approval"]["required"] = False
        with self.assertRaises(PermissionError):
            engine.propose_action(action)

    def test_l2_action_cannot_be_marked_executed_before_approval(self):
        engine = PersonalMemoryEngine("person-demo-001")
        engine.propose_action(EXAMPLE["agent_action_proposal"])
        with self.assertRaises(PermissionError):
            engine.mark_execution_result("paction-demo-reminder-001", result_status="succeeded", verification_status="verified")

    def test_only_owner_can_approve_agent_action(self):
        engine = PersonalMemoryEngine("person-demo-001")
        engine.propose_action(EXAMPLE["agent_action_proposal"])
        with self.assertRaises(PermissionError):
            engine.approve_action("paction-demo-reminder-001", actor_ref="other-person", approval_ref="approval", plan_hash="sha256:plan")

    def test_action_can_complete_after_explicit_approval(self):
        engine = PersonalMemoryEngine("person-demo-001")
        engine.propose_action(EXAMPLE["agent_action_proposal"])
        engine.approve_action("paction-demo-reminder-001", actor_ref="person-demo-001", approval_ref="approval-demo-001", plan_hash="sha256:plan")
        result = engine.mark_execution_result("paction-demo-reminder-001", result_status="succeeded", verification_status="verified")
        self.assertEqual(result["execution"]["status"], "succeeded")


if __name__ == "__main__":
    unittest.main()
