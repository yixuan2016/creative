from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from pdks_capture_runtime.file_store import FileFirstVault, FileConflictError, FileStoreError
from pdks_capture_runtime.service import CaptureRuntime

OWNER = "urn:pdks:owner:file-store-test"


def now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def event_record(owner, source_id, object_id="urn:pdks:event:file-store-1"):
    return {
        "pdks_version": "0.1.0",
        "object_id": object_id,
        "object_type": "event",
        "created_at": now(),
        "updated_at": now(),
        "owner_ref": owner,
        "domains": ["work"],
        "provenance": {"created_by": "urn:pdks:agent:test", "source_refs": [source_id]},
        "governance": {"sensitivity": "personal_work", "access_scope": "owner_only"},
        "lifecycle": {"status": "active", "version": 1},
        "payload": {
            "event_type": "work.meeting.internal_meeting",
            "event_taxonomy_version": "0.1.0",
            "description": "File-first adapter integration test",
            "time_precision": "unknown",
        },
    }


class FileFirstVaultTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.vault_path = self.base / "PDKS-Vault"
        self.vault = FileFirstVault(self.vault_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_initialize_creates_portable_vault_and_manifest(self):
        result = self.vault.initialize()
        self.assertEqual(result["status"], "initialized")
        self.assertTrue((self.vault_path / "README.md").exists())
        self.assertTrue((self.vault_path / "PDKS-MANIFEST.json").exists())
        self.assertTrue((self.vault_path / "50-Meetings").is_dir())

    def test_refuses_nonempty_unmanaged_directory(self):
        self.vault_path.mkdir()
        (self.vault_path / "my-notes.md").write_text("# My notes", encoding="utf-8")
        with self.assertRaises(FileStoreError):
            self.vault.initialize()

    def test_jsonl_append_is_idempotent_and_immutable(self):
        self.vault.initialize()
        record = {"object_id": "urn:pdks:source:1", "object_type": "source_asset", "payload": {"origin_system": "test"}}
        first = self.vault.append_jsonl("90-Source-Records/test.jsonl", record)
        second = self.vault.append_jsonl("90-Source-Records/test.jsonl", record)
        self.assertEqual(first["status"], "written")
        self.assertEqual(second["status"], "duplicate")
        changed = dict(record)
        changed["payload"] = {"origin_system": "changed"}
        with self.assertRaises(FileConflictError):
            self.vault.append_jsonl("90-Source-Records/test.jsonl", changed)

    def test_attachment_content_addressing_deduplicates_different_names(self):
        self.vault.initialize()
        data = b"same audio bytes"
        a = self.vault.write_attachment(data, "meeting.m4a", "audio/mp4")
        b = self.vault.write_attachment(data, "renamed.bin", "application/octet-stream")
        self.assertEqual(a["sha256"], hashlib.sha256(data).hexdigest())
        self.assertEqual(a["path"], b["path"])
        self.assertEqual(b["status"], "duplicate")
        self.assertEqual(len(list((self.vault_path / "assets" / "sha256").rglob("*.*"))), 1)

    def test_knowledge_note_preserves_user_edits_as_conflict(self):
        self.vault.initialize()
        record = event_record(OWNER, "urn:pdks:source:1")
        first = self.vault.write_knowledge_note(record)
        self.assertEqual(first["status"], "written")
        note = self.vault_path / first["path"]
        content = note.read_text(encoding="utf-8")
        self.assertIn('pdks_id: "urn:pdks:event:file-store-1"', content)
        self.assertIn("File-first adapter integration test", content)
        note.write_text(content + "\nUser edit\n", encoding="utf-8")
        second = self.vault.write_knowledge_note(record)
        self.assertEqual(second["status"], "conflict")
        self.assertTrue((self.vault_path / second["incoming_copy"]).exists())
        self.assertIn("User edit", note.read_text(encoding="utf-8"))

    def test_runtime_projection_and_rebuildable_index(self):
        db = self.base / "runtime.sqlite3"
        blob_vault = self.base / "runtime-blobs"
        rt = CaptureRuntime(db, blob_vault)
        rt.create_owner(OWNER)
        capture = rt.capture_text(OWNER, "今天讨论了 File-first 存储。", domain="work")
        record = event_record(OWNER, capture["source_id"])
        with rt._connection() as con:
            evidence_row = con.execute("SELECT evidence_id FROM evidence_segments WHERE source_id=? LIMIT 1",
                                       (capture["source_id"],)).fetchone()
        record["payload"]["evidence_refs"] = [evidence_row["evidence_id"]]
        rt.propose_records(OWNER, [record], [capture["source_id"]], "test-agent")
        rt.approve_record(OWNER, record["object_id"])

        result = self.vault.sync_from_runtime(rt, OWNER, include_raw_sources=True)
        self.assertEqual(result["status"], "projected")
        self.assertEqual(result["counts"]["source_records"], 1)
        self.assertGreaterEqual(result["counts"]["evidence_records"], 1)
        self.assertEqual(result["counts"]["knowledge_notes"], 1)
        self.assertEqual(result["counts"]["attachments"], 1)
        note_files = list((self.vault_path / "20-Events").glob("*.md"))
        self.assertEqual(len(note_files), 1)
        note_text = note_files[0].read_text(encoding="utf-8")
        self.assertIn("[Source record](", note_text)
        self.assertIn("[Original attachment](", note_text)
        self.assertIn("[Evidence record](", note_text)

        verify = self.vault.verify_manifest()
        self.assertEqual(verify["status"], "ok", verify["errors"])

        index = self.vault.rebuild_index()
        self.assertEqual(index["integrity_check"], "ok")
        self.assertEqual(index["counts"]["source_records"], 1)
        self.assertEqual(index["counts"]["evidence_records"], 1)
        self.assertEqual(index["counts"]["attachment_index_records"], 1)
        self.assertEqual(index["counts"]["knowledge_notes"], 1)
        self.assertEqual(index["counts"]["attachments"], 1)

        con = sqlite3.connect(index["index_path"])
        try:
            note_count = con.execute("SELECT COUNT(*) FROM knowledge_notes").fetchone()[0]
        finally:
            con.close()
        self.assertEqual(note_count, 1)

    def test_path_traversal_is_rejected(self):
        self.vault.initialize()
        with self.assertRaises(FileStoreError):
            self.vault.append_jsonl("../outside.jsonl", {"object_id": "urn:pdks:bad"})


if __name__ == "__main__":
    unittest.main()
