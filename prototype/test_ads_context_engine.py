"""Automated tests for the ADS work-context reference engine."""
import copy
import unittest

from ads_context_engine import ContextEngine, load_seed


class ContextEngineTests(unittest.TestCase):
    def setUp(self):
        self.seed = load_seed()
        self.engine = ContextEngine(self.seed)
        self.engine.ingest_many(self.seed["events"])

    def test_duplicate_event_is_idempotent(self):
        before = len(self.engine.events)
        result = self.engine.ingest_event(self.seed["events"][0])
        self.assertEqual(result["status"], "duplicate")
        self.assertEqual(len(self.engine.events), before)

    def test_authoritative_state_wins_and_conflict_is_preserved(self):
        state = self.engine.current_state(
            "obj_project_014", "project.status", {"internal"}
        )
        self.assertEqual(state["value"], "blocked")
        self.assertEqual(state["assertion_status"], "confirmed")
        self.assertEqual(state["authority_source"], "project-system")
        self.assertEqual(len(state["conflicts"]), 1)
        self.assertEqual(state["conflicts"][0]["value"], "on_track")
        self.assertEqual(state["conflicts"][0]["source_system"], "meeting-notes")

    def test_context_is_scoped_and_filters_restricted_events(self):
        context = self.engine.build_context(self.seed["context_request"])
        event_ids = set(context["included_refs"]["event_ids"])
        self.assertIn("evt_project_014_002", event_ids)
        self.assertNotIn("evt_project_014_004", event_ids)
        self.assertNotIn("evt_project_015_001", event_ids)
        self.assertEqual(context["current_states"][0]["value"], "blocked")
        self.assertTrue(context["unresolved_items"])
        self.assertIn("summarize", context["allowed_actions"])
        self.assertIn("update_project_status", context["approval_required_for"])

    def test_object_outside_grant_scope_is_denied(self):
        request = copy.deepcopy(self.seed["context_request"])
        request["object_ids"] = ["obj_project_015"]
        with self.assertRaises(PermissionError):
            self.engine.build_context(request)

    def test_wrong_purpose_is_denied(self):
        request = copy.deepcopy(self.seed["context_request"])
        request["purpose"] = "unrelated_personal_analysis"
        with self.assertRaises(PermissionError):
            self.engine.build_context(request)

    def test_unknown_object_reference_is_rejected(self):
        event = copy.deepcopy(self.seed["events"][0])
        event["event_id"] = "evt_unknown_object"
        event["source_ref"]["record_version"] = "999"
        event["object_refs"] = ["obj_does_not_exist"]
        with self.assertRaises(ValueError):
            self.engine.ingest_event(event)

    def test_tenant_mismatch_is_denied(self):
        request = copy.deepcopy(self.seed["context_request"])
        request["tenant_id"] = "tenant_other"
        with self.assertRaises(PermissionError):
            self.engine.build_context(request)


if __name__ == "__main__":
    unittest.main()
