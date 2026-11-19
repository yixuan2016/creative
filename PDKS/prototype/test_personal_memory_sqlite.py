"""Tests for the ADS-WORK-09 SQLite persistence adapter."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from personal_memory_sqlite import (
    ConcurrentWriteError,
    SQLiteBackedPersonalMemoryEngine,
    SQLitePersonalMemoryStore,
)

OWNER = "person-runtime-demo"
OTHER = "person-other-demo"


def sample_event(event_id="event-001", *, owner=OWNER, classification="personal"):
    return {
        "event_id": event_id,
        "subject_ref": owner,
        "event_type": "personal.work.meeting_internal_meeting",
        "event_schema_version": "0.1.0",
        "occurred_at": "2026-11-19T09:00:00+08:00",
        "observed_at": "2026-11-19T09:05:00+08:00",
        "recorded_at": "2026-11-19T09:06:00+08:00",
        "timezone": "UTC+08:00",
        "actor_refs": [{"actor_type": "person", "actor_id": owner}],
        "object_refs": [],
        "payload": {"summary": "Discussed project risks"},
        "source_refs": [{
            "source_system": "manual-note",
            "native_record_id": "note-001",
            "capture_mode": "manual_user_entry",
            "capture_authorization_ref": None,
        }],
        "assertion_status": "observed",
        "classification": classification,
        "purpose_tags": ["personal_planning"],
        "ontology_version": "ads.work-ontology@0.1.0",
        "processing_provenance": {
            "capture_method": "manual", "extraction_method": "human_curated",
            "extractor_version": "test", "human_reviewed": True,
        },
        "sharing_policy": {
            "default_scope": "personal_only", "projection_allowed": False,
            "authorized_purposes": [], "authorization_ref": None, "expires_at": None,
        },
        "retention": {
            "policy_ref": "personal-default-v0.1", "retain_until": None,
            "deletion_state": "active",
        },
        "lifecycle_status": "active",
        "idempotency_key": f"{event_id}-v1",
    }


def sample_intent(intent_id="intent-001", *, owner=OWNER, source="event-001", inferred=False):
    return {
        "intent_id": intent_id,
        "subject_ref": owner,
        "intent_type": "task",
        "title": "Prepare project risk list",
        "description": "Prepare and review the project risk list.",
        "status": "proposed" if inferred else "active",
        "confirmation_status": "inferred_candidate" if inferred else "user_confirmed",
        "owner_ref": owner,
        "source_event_refs": [source],
        "created_at": "2026-11-19T09:10:00+08:00",
        "updated_at": "2026-11-19T09:10:00+08:00",
        "classification": "personal",
        "sharing_policy": {
            "default_scope": "personal_only", "shareable": False,
            "authorization_ref": None,
        },
        "ontology_version": "ads.work-ontology@0.1.0",
    }


def sample_action():
    return {
        "proposal_id": "proposal-001",
        "subject_ref": OWNER,
        "task_ref": "intent-001",
        "purpose": "Create a personal reminder draft",
        "requested_by": "agent",
        "risk_tier": "L2",
        "approval": {
            "required": True, "status": "pending", "approved_by": None,
            "approved_at": None, "approval_ref": None, "approved_plan_hash": None,
        },
        "execution": {
            "status": "not_started", "started_at": None, "finished_at": None,
            "verification_status": "not_checked",
        },
    }


class SQLitePersonalMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "personal-memory.sqlite3"
        self.engine = SQLiteBackedPersonalMemoryEngine(OWNER, self.db)

    def tearDown(self):
        self.temp.cleanup()

    def reopen(self):
        return SQLiteBackedPersonalMemoryEngine(OWNER, self.db)

    def test_event_persists_across_restart(self):
        self.engine.append_event(sample_event())
        reopened = self.reopen()
        self.assertEqual(len(reopened.events), 1)
        self.assertEqual(reopened.events[0]["event_id"], "event-001")
        self.assertEqual(reopened._revision, 1)

    def test_idempotent_replay_after_restart_does_not_create_revision(self):
        event = sample_event()
        self.engine.append_event(event)
        revision = self.engine._revision
        reopened = self.reopen()
        reopened.append_event(event)
        self.assertEqual(reopened._revision, revision)
        self.assertEqual(len(reopened.events), 1)

    def test_event_id_reuse_with_different_content_is_rejected(self):
        self.engine.append_event(sample_event())
        changed = sample_event()
        changed["payload"]["summary"] = "Different content"
        with self.assertRaises(ValueError):
            self.engine.append_event(changed)

    def test_owner_partitions_are_isolated(self):
        self.engine.append_event(sample_event())
        other = SQLiteBackedPersonalMemoryEngine(OTHER, self.db)
        self.assertEqual(other.events, [])
        other.append_event(sample_event("other-event", owner=OTHER))
        self.assertEqual(len(self.reopen().events), 1)
        self.assertEqual(len(SQLiteBackedPersonalMemoryEngine(OTHER, self.db).events), 1)

    def test_non_owner_cannot_append_to_owner_partition(self):
        with self.assertRaises(PermissionError):
            self.engine.append_event(sample_event(owner=OTHER))

    def test_optimistic_concurrency_requires_refresh(self):
        stale = self.reopen()
        self.engine.append_event(sample_event("event-a"))
        with self.assertRaises(ConcurrentWriteError):
            stale.append_event(sample_event("event-b"))
        stale.refresh()
        stale.append_event(sample_event("event-b"))
        self.assertEqual(len(self.reopen().events), 2)

    def test_memory_confirmation_persists(self):
        self.engine.append_event(sample_event())
        self.engine.derive_memory("event-001", "memory-001", "semantic", "I am researching PDKS.")
        self.assertEqual(self.reopen().memories["memory-001"]["memory_lifecycle"], "candidate")
        reopened = self.reopen()
        reopened.confirm_memory("memory-001", actor_ref=OWNER)
        self.assertEqual(self.reopen().memories["memory-001"]["memory_lifecycle"], "active")

    def test_sensitive_memory_is_excluded_from_context_by_default(self):
        self.engine.append_event(sample_event())
        self.engine.derive_memory(
            "event-001", "memory-sensitive", "episodic", "Sensitive detail",
            user_confirmed=True, classification="personal_sensitive",
        )
        self.assertEqual(self.reopen().build_context(purpose="planning")["memories"], [])
        self.assertEqual(len(self.reopen().build_context(purpose="planning", include_sensitive=True)["memories"]), 1)

    def test_source_suppression_survives_restart_and_blocks_rederivation(self):
        self.engine.append_event(sample_event())
        self.engine.derive_memory("event-001", "memory-001", "semantic", "A derived claim", user_confirmed=True)
        self.engine.forget_source_event("event-001", actor_ref=OWNER)
        reopened = self.reopen()
        self.assertEqual(reopened.build_context(purpose="planning")["memories"], [])
        with self.assertRaises(PermissionError):
            reopened.derive_memory("event-001", "memory-002", "semantic", "Recreated claim")

    def test_source_suppression_pauses_dependent_intent_for_owner_review(self):
        self.engine.append_event(sample_event())
        self.engine.create_intent(sample_intent(), actor_ref=OWNER)
        self.engine.forget_source_event("event-001", actor_ref=OWNER)
        reopened = self.reopen()
        intent = reopened.intents["intent-001"]
        self.assertEqual(intent["status"], "paused")
        self.assertTrue(intent["extensions"]["source_suppressed"])
        self.assertTrue(intent["extensions"]["requires_owner_review"])
        self.assertEqual(reopened.build_operating_context(purpose="planning")["intents"], [])

    def test_intent_requires_owner_and_existing_unsuppressed_event(self):
        self.engine.append_event(sample_event())
        with self.assertRaises(PermissionError):
            self.engine.create_intent(sample_intent(owner=OTHER), actor_ref=OWNER)
        with self.assertRaises(KeyError):
            self.engine.create_intent(sample_intent(source="missing-event"), actor_ref=OWNER)
        created = self.engine.create_intent(sample_intent(), actor_ref=OWNER)
        self.assertEqual(created["intent_id"], "intent-001")
        self.assertEqual(self.reopen().intents["intent-001"]["title"], "Prepare project risk list")

    def test_inferred_intent_cannot_be_active(self):
        self.engine.append_event(sample_event())
        intent = sample_intent(inferred=True)
        intent["status"] = "active"
        with self.assertRaises(ValueError):
            self.engine.create_intent(intent, actor_ref=OWNER)

    def test_intent_update_is_versioned_and_protected(self):
        self.engine.append_event(sample_event())
        self.engine.create_intent(sample_intent(), actor_ref=OWNER)
        self.engine.update_intent("intent-001", {"status": "completed", "progress": 1.0}, actor_ref=OWNER)
        self.assertEqual(self.reopen().intents["intent-001"]["status"], "completed")
        with self.assertRaises(ValueError):
            self.engine.update_intent("intent-001", {"sharing_policy": {"default_scope": "public"}}, actor_ref=OWNER)

    def test_l2_action_and_approval_state_persist(self):
        self.engine.append_event(sample_event())
        self.engine.create_intent(sample_intent(), actor_ref=OWNER)
        self.engine.propose_action(sample_action())
        with self.assertRaises(PermissionError):
            self.engine.mark_execution_result("proposal-001", result_status="succeeded", verification_status="verified")
        reopened = self.reopen()
        reopened.approve_action("proposal-001", actor_ref=OWNER, approval_ref="approval-001", plan_hash="sha256:plan")
        reopened.mark_execution_result("proposal-001", result_status="succeeded", verification_status="verified")
        final = self.reopen().actions["proposal-001"]
        self.assertEqual(final["approval"]["status"], "approved")
        self.assertEqual(final["execution"]["status"], "succeeded")

    def test_action_cannot_reference_unknown_intent(self):
        with self.assertRaises(KeyError):
            self.engine.propose_action(sample_action())

    def test_audit_log_is_append_only_and_contains_no_record_payload(self):
        self.engine.append_event(sample_event())
        entries = self.engine.audit_log()
        self.assertEqual(entries[-1]["operation"], "append_event")
        self.assertIn("state_digest", entries[-1])
        self.assertNotIn("payload", entries[-1])
        conn = sqlite3.connect(self.db)
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE audit_log SET operation='tampered' WHERE sequence=1")
        finally:
            conn.close()

    def test_backup_and_integrity_check(self):
        self.engine.append_event(sample_event())
        backup = Path(self.temp.name) / "backup.sqlite3"
        self.engine.backup_to(backup)
        self.assertTrue(backup.exists())
        self.assertEqual(self.engine.store.integrity_check(), "ok")
        reopened = SQLiteBackedPersonalMemoryEngine(OWNER, backup)
        self.assertEqual(len(reopened.events), 1)

    def test_operating_context_filters_candidate_intents(self):
        self.engine.append_event(sample_event())
        self.engine.create_intent(sample_intent(inferred=True), actor_ref=OWNER)
        default = self.engine.build_operating_context(purpose="planning")
        inclusive = self.engine.build_operating_context(purpose="planning", include_candidates=True)
        self.assertEqual(default["intents"], [])
        self.assertEqual(len(inclusive["intents"]), 1)


if __name__ == "__main__":
    unittest.main()
