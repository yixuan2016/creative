"""PDKS -> ADS-WORK-09 conservative projection tests."""
import json
import tempfile
import unittest
import subprocess
import sys
from pathlib import Path

from pdks_ads_adapter import project_bundle
from personal_memory_sqlite import SQLiteBackedPersonalMemoryEngine

OWNER = "urn:pdks:demo:person:owner"
EVENT_ID = "urn:pdks:demo:event:meeting-1"
SOURCE_ID = "urn:pdks:demo:source:audio-1"
ASSERTION_ID = "urn:pdks:demo:assertion:1"


def envelope(object_id, object_type, payload, *, owner=OWNER, sensitivity="personal_work", source_refs=None, created="2026-11-19T09:00:00+08:00"):
    return {
        "pdks_version": "0.1.0",
        "object_id": object_id,
        "object_type": object_type,
        "created_at": created,
        "updated_at": created,
        "owner_ref": owner,
        "domains": ["work"],
        "provenance": {"created_by": "urn:pdks:agent:test", **({"source_refs": source_refs} if source_refs else {})},
        "governance": {"sensitivity": sensitivity, "access_scope": "owner_only"},
        "lifecycle": {"status": "active", "version": 1},
        "payload": payload,
    }


def sample_records(capture_method="api_import", consent_ref=None):
    source = envelope(SOURCE_ID, "source_asset", {
        "source_type": "audio", "origin_system": "test-importer",
        "source_locator": "urn:local:source:audio-1",
        "captured_at": "2026-11-19T09:05:00+08:00",
        "media_type": "audio/mpeg", "capture_method": capture_method,
    })
    if consent_ref:
        source["governance"]["consent_ref"] = consent_ref
    event = envelope(EVENT_ID, "event", {
        "event_type": "work.meeting.internal_meeting",
        "event_taxonomy_version": "0.1.0",
        "title": "Project discussion", "description": "Reviewed current risks.",
        "start_at": "2026-11-19T09:00:00+08:00", "end_at": "2026-11-19T09:30:00+08:00",
        "time_precision": "exact", "participants": [], "context_refs": ["urn:pdks:demo:project:1"],
        "evidence_refs": [], "classification_status": "classified",
    }, source_refs=[SOURCE_ID])
    knowledge = envelope("urn:pdks:demo:knowledge:1", "knowledge_asset", {
        "knowledge_type": "insight", "title": "A reusable lesson",
        "summary": "A reusable lesson derived from the project discussion.",
        "content": "Detailed lesson.", "applicability": ["project planning"],
        "limitations": ["Requires context review"], "derived_from_refs": [EVENT_ID, ASSERTION_ID],
        "verification_status": "draft",
    })
    context = envelope("urn:pdks:demo:context:1", "personal_context", {
        "context_type": "current_focus", "subject_ref": OWNER,
        "value": "Currently focusing on personal knowledge systems.",
        "verification_status": "inferred", "confidence_level": "medium",
        "evidence_refs": [EVENT_ID], "review_policy": "suggest_update",
    })
    action = envelope("urn:pdks:demo:action:1", "action", {
        "action_type": "task", "title": "Review the PDKS mapping",
        "description": "Review event and memory mapping.", "status": "open",
        "assignee_ref": OWNER, "created_from_refs": [EVENT_ID],
        "due_at": "2026-11-25T18:00:00+08:00", "priority": "normal",
    })
    assertion = envelope(ASSERTION_ID, "assertion", {
        "assertion_type": "opinion", "content": "This is a reported opinion.",
        "asserted_by_ref": "urn:pdks:demo:person:leader", "epistemic_status": "reported",
        "evidence_refs": [],
    })
    return [event, source, knowledge, context, action, assertion]


class PDKSToADSAdapterTests(unittest.TestCase):
    def test_bundled_pdks_scenario_passes_schema_and_taxonomy_validation(self):
        root = Path(__file__).resolve().parents[1]
        skill = root / "skills" / "pdks-personal-knowledge"
        scenario = skill / "examples" / "scenarios" / "voice-meeting"
        records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(scenario.glob("*.json"))]
        from pdks_ads_adapter import validate_pdks_records
        validate_pdks_records(
            records,
            schema_path=skill / "assets" / "pdks-0.1-record.schema.json",
            taxonomy_path=skill / "assets" / "pdks-event-taxonomy-0.1.json",
        )

    def test_happy_path_projects_event_memories_and_intent_only(self):
        result = project_bundle(sample_records(), owner_ref=OWNER)
        self.assertEqual(len(result["event_ledger"]), 1)
        self.assertEqual(len(result["memory_items"]), 2)
        self.assertEqual(len(result["intent_objects"]), 1)
        self.assertEqual(result["agent_action_proposals"], [])
        self.assertIsNone(result["enterprise_projection"])
        self.assertEqual(result["event_ledger"][0]["event_type"], "personal.work.meeting_internal_meeting")
        self.assertEqual(result["event_ledger"][0]["sharing_policy"]["default_scope"], "personal_only")
        self.assertFalse(result["event_ledger"][0]["sharing_policy"]["projection_allowed"])
        self.assertTrue(all(x["assertion_status"] == "candidate" for x in result["memory_items"]))
        self.assertEqual(result["intent_objects"][0]["confirmation_status"], "inferred_candidate")
        self.assertEqual(result["intent_objects"][0]["status"], "proposed")
        self.assertTrue(any(x["object_type"] == "assertion" for x in result["preserved_only"]))

    def test_device_capture_without_consent_is_blocked_and_dependents_do_not_project(self):
        result = project_bundle(sample_records(capture_method="device_capture"), owner_ref=OWNER)
        codes = {x["code"] for x in result["blocked"]}
        self.assertIn("consent_missing", codes)
        self.assertEqual(result["event_ledger"], [])
        self.assertEqual(result["memory_items"], [])
        self.assertEqual(result["intent_objects"], [])

    def test_device_capture_requires_validated_authorization_reference(self):
        records = sample_records(capture_method="device_capture", consent_ref="consent-001")
        denied = project_bundle(records, owner_ref=OWNER, valid_authorization_refs=[])
        allowed = project_bundle(records, owner_ref=OWNER, valid_authorization_refs=["consent-001"])
        self.assertEqual(denied["event_ledger"], [])
        self.assertEqual(len(allowed["event_ledger"]), 1)
        self.assertEqual(allowed["event_ledger"][0]["source_refs"][0]["capture_mode"], "device_capture")
        self.assertEqual(allowed["event_ledger"][0]["processing_provenance"]["capture_method"], "device")

    def test_connector_capture_without_active_authorization_is_blocked(self):
        records = sample_records(capture_method="system_sync", consent_ref="consent-002")
        result = project_bundle(records, owner_ref=OWNER, valid_authorization_refs=[])
        self.assertIn("consent_not_validated", {x["code"] for x in result["blocked"]})

    def test_missing_event_start_time_is_blocked(self):
        records = sample_records()
        records[0]["payload"].pop("start_at")
        result = project_bundle(records, owner_ref=OWNER)
        self.assertIn("missing_time", {x["code"] for x in result["blocked"]})
        self.assertEqual(result["event_ledger"], [])

    def test_action_assigned_to_another_person_is_not_personal_intent(self):
        records = sample_records()
        records[4]["payload"]["assignee_ref"] = "someone-else"
        result = project_bundle(records, owner_ref=OWNER)
        self.assertIn("assignee_mismatch", {x["code"] for x in result["blocked"]})
        self.assertEqual(result["intent_objects"], [])

    def test_context_for_another_subject_is_blocked(self):
        records = sample_records()
        records[3]["payload"]["subject_ref"] = "someone-else"
        result = project_bundle(records, owner_ref=OWNER)
        self.assertIn("owner_mismatch", {x["code"] for x in result["blocked"]})

    def test_sqlite_runtime_applies_projection_atomically_and_persistently(self):
        projection = project_bundle(sample_records(), owner_ref=OWNER)
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "runtime.sqlite3"
            engine = SQLiteBackedPersonalMemoryEngine(OWNER, db)
            counts = engine.apply_pdks_projection(projection)
            self.assertEqual(counts, {"events": 1, "memories": 2, "intents": 1, "agent_actions": 0})
            reopened = SQLiteBackedPersonalMemoryEngine(OWNER, db)
            self.assertEqual(len(reopened.events), 1)
            self.assertEqual(len(reopened.memories), 2)
            self.assertEqual(len(reopened.intents), 1)
            self.assertEqual(reopened.actions, {})
            self.assertEqual(reopened.build_operating_context(purpose="planning")["intents"], [])
            self.assertEqual(len(reopened.build_operating_context(purpose="planning", include_candidates=True)["intents"]), 1)

    def test_confirmed_memory_requires_explicit_owner_write(self):
        records = sample_records()
        records[2]["payload"]["verification_status"] = "confirmed"
        projection = project_bundle(records, owner_ref=OWNER)
        self.assertEqual(projection["memory_items"][0]["memory_lifecycle"], "active")
        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "runtime.sqlite3"
            agent_engine = SQLiteBackedPersonalMemoryEngine(OWNER, db)
            with self.assertRaises(PermissionError):
                agent_engine.apply_pdks_projection(projection)
            self.assertEqual(agent_engine.events, [])
            owner_engine = SQLiteBackedPersonalMemoryEngine(OWNER, db)
            counts = owner_engine.apply_pdks_projection(projection, actor_ref=OWNER)
            self.assertEqual(counts["memories"], 2)
            self.assertTrue(any(x["memory_lifecycle"] == "active" for x in owner_engine.memories.values()))

    def test_runtime_rejects_projection_for_another_owner(self):
        projection = project_bundle(sample_records(), owner_ref=OWNER)
        projection["owner_ref"] = "someone-else"
        with tempfile.TemporaryDirectory() as td:
            engine = SQLiteBackedPersonalMemoryEngine(OWNER, Path(td) / "runtime.sqlite3")
            with self.assertRaises(PermissionError):
                engine.apply_pdks_projection(projection)
            self.assertEqual(engine.events, [])

    def test_runtime_rechecks_authorization_references(self):
        records = sample_records(capture_method="device_capture", consent_ref="consent-003")
        projection = project_bundle(records, owner_ref=OWNER, valid_authorization_refs=["consent-003"])
        projection["validated_authorization_refs"] = []
        with tempfile.TemporaryDirectory() as td:
            engine = SQLiteBackedPersonalMemoryEngine(OWNER, Path(td) / "runtime.sqlite3")
            with self.assertRaises(PermissionError):
                engine.apply_pdks_projection(projection)
            self.assertEqual(engine.events, [])

    def test_projection_with_forbidden_agent_action_is_atomic(self):
        projection = project_bundle(sample_records(), owner_ref=OWNER)
        projection["agent_action_proposals"] = [{"proposal_id": "must-not-be-created"}]
        with tempfile.TemporaryDirectory() as td:
            engine = SQLiteBackedPersonalMemoryEngine(OWNER, Path(td) / "runtime.sqlite3")
            with self.assertRaises(PermissionError):
                engine.apply_pdks_projection(projection)
            self.assertEqual(engine.events, [])
            self.assertEqual(engine.memories, {})
            self.assertEqual(engine.intents, {})

    def test_cli_end_to_end_project_apply_context_and_integrity(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            records_dir = root / "records"
            records_dir.mkdir()
            for record in sample_records():
                path = records_dir / f"{record['object_type']}-{record['object_id'].split(':')[-1]}.json"
                path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
            db = root / "vault.sqlite3"
            projection_path = root / "projection.json"
            cli = Path(__file__).with_name("personal_memory_cli.py")

            project = subprocess.run([
                sys.executable, str(cli), "project-pdks", "--records-dir", str(records_dir),
                "--owner", OWNER, "--output", str(projection_path), "--skip-pdks-validation",
            ], capture_output=True, text=True)
            self.assertEqual(project.returncode, 0, project.stdout + project.stderr)
            init = subprocess.run([
                sys.executable, str(cli), "init", "--db", str(db), "--owner", OWNER,
            ], capture_output=True, text=True)
            self.assertEqual(init.returncode, 0, init.stdout + init.stderr)
            apply = subprocess.run([
                sys.executable, str(cli), "apply-projection", "--db", str(db),
                "--owner", OWNER, "--projection", str(projection_path),
            ], capture_output=True, text=True)
            self.assertEqual(apply.returncode, 0, apply.stdout + apply.stderr)
            context = subprocess.run([
                sys.executable, str(cli), "context", "--db", str(db), "--owner", OWNER,
                "--purpose", "personal_planning", "--include-candidates",
            ], capture_output=True, text=True)
            self.assertEqual(context.returncode, 0, context.stdout + context.stderr)
            self.assertEqual(len(json.loads(context.stdout)["memories"]), 2)
            integrity = subprocess.run([
                sys.executable, str(cli), "integrity-check", "--db", str(db),
            ], capture_output=True, text=True)
            self.assertEqual(integrity.returncode, 0, integrity.stdout + integrity.stderr)
            self.assertTrue(json.loads(integrity.stdout)["ok"])

    def test_projection_output_matches_repository_ads_schemas_when_available(self):
        root = Path(__file__).resolve().parents[1]
        schema_files = {
            "event": root / "schemas/ads-personal-event-ledger-v0.1.schema.json",
            "memory": root / "schemas/ads-personal-memory-item-v0.1.schema.json",
            "intent": root / "schemas/ads-personal-intent-object-v0.1.schema.json",
        }
        if not all(path.exists() for path in schema_files.values()):
            self.skipTest("Repository ADS schemas are not present in this standalone test folder.")
        from jsonschema import Draft202012Validator, FormatChecker
        schemas = {k: Draft202012Validator(json.loads(v.read_text(encoding="utf-8")), format_checker=FormatChecker()) for k, v in schema_files.items()}
        projection = project_bundle(sample_records(), owner_ref=OWNER)
        for item in projection["event_ledger"]:
            schemas["event"].validate(item)
        for item in projection["memory_items"]:
            schemas["memory"].validate(item)
        for item in projection["intent_objects"]:
            schemas["intent"].validate(item)


if __name__ == "__main__":
    unittest.main()
