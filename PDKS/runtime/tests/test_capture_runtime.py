from __future__ import annotations
import base64
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from datetime import datetime, timezone
from jsonschema import Draft202012Validator, FormatChecker

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"runtime"))
from pdks_capture_runtime.service import CaptureRuntime, MAX_CAPTURE_BYTES
from pdks_capture_runtime.errors import (
    AuthorizationError, ConsentRequiredError, ConflictError,
    NotFoundError, PayloadTooLargeError, ValidationError
)
from pdks_capture_runtime.api import make_handler
from pdks_capture_runtime.client import PDKSCaptureClient

OWNER="urn:pdks:owner:test"
def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def event_record(owner, source_id, object_id="urn:pdks:event:test-1", consent_ref=None):
    governance={"sensitivity":"personal_private","access_scope":"owner_only"}
    if consent_ref: governance["consent_ref"]=consent_ref
    return {
      "pdks_version":"0.1.0","object_id":object_id,"object_type":"event",
      "created_at":now(),"updated_at":now(),"owner_ref":owner,"domains":["work"],
      "provenance":{"created_by":"urn:pdks:agent:test","source_refs":[source_id]},
      "governance":governance,"lifecycle":{"status":"active","version":1},
      "payload":{"event_type":"work.meeting.internal_meeting","event_taxonomy_version":"0.1.0",
                 "description":"讨论项目方案","time_precision":"unknown"}
    }

class RuntimeCase(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.base=Path(self.tmp.name)
        self.rt=CaptureRuntime(self.base/"pdks.sqlite3",self.base/"vault")
        self.rt.create_owner(OWNER)

    def tearDown(self):
        self.tmp.cleanup()

    def capture(self, text="今天开会讨论了项目方案。", **kw):
        options={"domain":"work"}
        options.update(kw)
        return self.rt.capture_text(OWNER,text,**options)

    def test_manual_text_capture_creates_source_and_evidence(self):
        result=self.capture()
        self.assertEqual(result["status"],"awaiting_agent")
        self.assertEqual(result["source_type"],"note")
        self.assertEqual(result["evidence_segments"],1)
        details=self.rt.get_capture(OWNER,result["capture_id"])
        self.assertIn("今天开会",details["extracted_text"])

    def test_source_asset_and_evidence_follow_pinned_schema(self):
        result=self.capture()
        with self.rt._connection() as con:
            source=con.execute("SELECT source_record_json FROM source_assets WHERE source_id=?",(result["source_id"],)).fetchone()[0]
            evidence=con.execute("SELECT evidence_record_json FROM evidence_segments WHERE source_id=?",(result["source_id"],)).fetchone()[0]
        validator=Draft202012Validator(self.rt._schema,format_checker=FormatChecker())
        self.assertEqual(list(validator.iter_errors(json.loads(source))),[])
        self.assertEqual(list(validator.iter_errors(json.loads(evidence))),[])

    def test_idempotency_key_returns_same_capture(self):
        a=self.capture(idempotency_key="daily-2026-11-19")
        b=self.capture(idempotency_key="daily-2026-11-19")
        self.assertEqual(a["capture_id"],b["capture_id"])
        self.assertTrue(b["duplicate"])

    def test_content_deduplication_for_same_owner_and_source_kind(self):
        a=self.capture("same content")
        b=self.capture("same content")
        self.assertEqual(a["source_id"],b["source_id"])
        self.assertTrue(b["duplicate"])

    def test_idempotency_key_cannot_be_reused_for_different_content(self):
        self.capture("first content",idempotency_key="same-key")
        with self.assertRaises(ConflictError):
            self.capture("different content",idempotency_key="same-key")

    def test_same_content_from_different_source_locators_is_not_collapsed(self):
        a=self.capture("same text",source_locator="dingtalk://message/1")
        b=self.capture("same text",source_locator="email://message/2")
        self.assertNotEqual(a["source_id"],b["source_id"])

    def test_automatic_capture_denied_without_consent(self):
        with self.assertRaises(ConsentRequiredError):
            self.capture(source_kind="dingtalk",capture_method="system_sync")

    def test_automatic_capture_requires_matching_active_consent(self):
        consent=self.rt.create_consent(OWNER,"dingtalk",["personal_knowledge_capture"],["read_messages"],["work"],["capture"])
        result=self.capture(source_kind="dingtalk",capture_method="system_sync",consent_ref=consent["consent_ref"])
        self.assertEqual(result["status"],"awaiting_agent")

    def test_wrong_source_consent_is_denied(self):
        consent=self.rt.create_consent(OWNER,"wechat",["personal_knowledge_capture"],["read_messages"],["work"],["capture"])
        with self.assertRaises(ConsentRequiredError):
            self.capture(source_kind="dingtalk",capture_method="system_sync",consent_ref=consent["consent_ref"])

    def test_consent_without_read_scope_is_denied(self):
        consent=self.rt.create_consent(OWNER,"dingtalk",["personal_knowledge_capture"],["write"],["work"],["capture"])
        with self.assertRaises(ConsentRequiredError):
            self.capture(source_kind="dingtalk",capture_method="system_sync",consent_ref=consent["consent_ref"])

    def test_wrong_domain_consent_is_denied(self):
        consent=self.rt.create_consent(OWNER,"microphone",["personal_knowledge_capture"],["record"],["life"],["capture"])
        with self.assertRaises(ConsentRequiredError):
            self.capture(source_kind="microphone",capture_method="device_capture",consent_ref=consent["consent_ref"],domain="work")

    def test_revoked_consent_blocks_future_capture(self):
        consent=self.rt.create_consent(OWNER,"dingtalk",["personal_knowledge_capture"],["read"],["work"],["capture"])
        self.rt.revoke_consent(OWNER,consent["consent_ref"])
        with self.assertRaises(ConsentRequiredError):
            self.capture(source_kind="dingtalk",capture_method="system_sync",consent_ref=consent["consent_ref"])

    def test_capture_file_docx_or_text_and_unsupported_pdf_status(self):
        text_result=self.rt.capture_file(OWNER,"note.txt","文件中的工作记录".encode(),domain="work")
        pdf_result=self.rt.capture_file(OWNER,"scan.pdf",b"%PDF-FAKE",domain="work")
        self.assertEqual(text_result["status"],"awaiting_agent")
        self.assertEqual(pdf_result["status"],"awaiting_extractor")

    def test_html_script_is_not_in_extracted_text(self):
        html=b"<html><body><p>visible text</p><script>secret()</script></body></html>"
        result=self.rt.capture_file(OWNER,"clip.html",html,domain="learning")
        details=self.rt.get_capture(OWNER,result["capture_id"])
        self.assertIn("visible text",details["extracted_text"])
        self.assertNotIn("secret()",details["extracted_text"])

    def test_payload_size_limit(self):
        with self.assertRaises(PayloadTooLargeError):
            self.rt.capture_file(OWNER,"large.bin",b"x"*(MAX_CAPTURE_BYTES+1),domain="other")

    def test_candidate_record_requires_real_source_reference(self):
        result=self.capture()
        bad=event_record(OWNER,"urn:pdks:source:does-not-exist")
        with self.assertRaises(ValidationError):
            self.rt.propose_records(OWNER,[bad],[result["source_id"]],"agent-a")

    def test_candidate_record_is_validated_and_owner_approved_separately(self):
        result=self.capture()
        record=event_record(OWNER,result["source_id"])
        proposal=self.rt.propose_records(OWNER,[record],[result["source_id"]],"agent-a")
        self.assertEqual(proposal["status"],"needs_review")
        self.assertEqual(self.rt.list_records(OWNER,"accepted"),[])
        self.assertEqual(self.rt.list_records(OWNER,"candidate")[0]["record_id"],record["object_id"])
        self.rt.approve_record(OWNER,record["object_id"])
        self.assertEqual(self.rt.list_records(OWNER,"accepted")[0]["record_id"],record["object_id"])

    def test_candidate_evidence_refs_must_resolve_to_supplied_source(self):
        result=self.capture()
        with self.rt._connection() as con:
            evidence_id=con.execute("SELECT evidence_id FROM evidence_segments WHERE source_id=?",(result["source_id"],)).fetchone()[0]
        record=event_record(OWNER,result["source_id"])
        record["payload"]["evidence_refs"]=["urn:pdks:evidence:missing"]
        with self.assertRaises(ValidationError):
            self.rt.propose_records(OWNER,[record],[result["source_id"]],"agent-a")
        record["payload"]["evidence_refs"]=[evidence_id]
        self.rt.propose_records(OWNER,[record],[result["source_id"]],"agent-a")

    def test_record_for_different_owner_is_rejected(self):
        result=self.capture()
        record=event_record("urn:pdks:owner:other",result["source_id"])
        with self.assertRaises(AuthorizationError):
            self.rt.propose_records(OWNER,[record],[result["source_id"]],"agent-a")

    def test_non_owner_only_record_is_rejected(self):
        result=self.capture()
        record=event_record(OWNER,result["source_id"])
        record["governance"]["access_scope"]="organization_authorized"
        with self.assertRaises(AuthorizationError):
            self.rt.propose_records(OWNER,[record],[result["source_id"]],"agent-a")

    def test_connector_consent_reference_must_be_preserved(self):
        consent=self.rt.create_consent(OWNER,"dingtalk",["personal_knowledge_capture"],["read"],["work"],["capture"])
        result=self.capture(source_kind="dingtalk",capture_method="system_sync",consent_ref=consent["consent_ref"])
        record=event_record(OWNER,result["source_id"])
        with self.assertRaises(AuthorizationError):
            self.rt.propose_records(OWNER,[record],[result["source_id"]],"agent-a")
        record["governance"]["consent_ref"]=consent["consent_ref"]
        self.rt.propose_records(OWNER,[record],[result["source_id"]],"agent-a")

    def test_source_deletion_purges_blob_evidence_and_dependent_records(self):
        result=self.capture()
        record=event_record(OWNER,result["source_id"])
        self.rt.propose_records(OWNER,[record],[result["source_id"]],"agent-a")
        with self.rt._connection() as con:
            raw=con.execute("SELECT raw_path FROM source_assets WHERE source_id=?",(result["source_id"],)).fetchone()[0]
        self.assertTrue(Path(raw).exists())
        deleted=self.rt.delete_source(OWNER,result["source_id"])
        self.assertEqual(deleted["status"],"deleted_locally")
        self.assertFalse(Path(raw).exists())
        with self.rt._connection() as con:
            row=con.execute("SELECT record_json,review_state FROM records WHERE record_id=?",(record["object_id"],)).fetchone()
            cap=con.execute("SELECT extracted_text,status FROM captures WHERE capture_id=?",(result["capture_id"],)).fetchone()
        self.assertIsNone(row["record_json"])
        self.assertEqual(row["review_state"],"deleted_by_source_request")
        self.assertIsNone(cap["extracted_text"])
        self.assertEqual(cap["status"],"deleted")

    def test_export_bundle_verifies_and_excludes_raw_by_default(self):
        result=self.capture()
        record=event_record(OWNER,result["source_id"])
        self.rt.propose_records(OWNER,[record],[result["source_id"]],"agent-a")
        self.rt.approve_record(OWNER,record["object_id"])
        out=self.base/"export.zip"
        receipt=self.rt.export_bundle(OWNER,out)
        self.assertEqual(receipt["include_raw_sources"],False)
        self.assertTrue(self.rt.verify_bundle(out)["valid"])
        import zipfile
        with zipfile.ZipFile(out) as z:
            self.assertFalse(any(x.startswith("raw-sources/") for x in z.namelist()))

    def test_token_scopes_and_revocation(self):
        token=self.rt.issue_token(OWNER,"agent-a",["capture:write"])
        principal=self.rt.authenticate(token["token"])
        self.assertIn("capture:write",principal.scopes)
        self.assertNotIn("records:approve",principal.scopes)
        self.rt.revoke_token(OWNER,"agent-a")
        with self.assertRaises(AuthorizationError):
            self.rt.authenticate(token["token"])

    def test_multiple_agents_have_separate_tokens_but_same_owner_partition(self):
        a=self.rt.issue_token(OWNER,"agent-a",["capture:read","capture:write"])
        b=self.rt.issue_token(OWNER,"agent-b",["capture:read"])
        pa=self.rt.authenticate(a["token"]); pb=self.rt.authenticate(b["token"])
        self.assertEqual(pa.owner_ref,pb.owner_ref)
        self.assertNotEqual(pa.agent_id,pb.agent_id)
        self.assertNotIn("capture:write",pb.scopes)

    def test_token_is_bound_to_one_owner(self):
        self.rt.create_owner("urn:pdks:owner:other")
        token=self.rt.issue_token("urn:pdks:owner:other","agent-other",["capture:read"])
        principal=self.rt.authenticate(token["token"])
        self.assertEqual(principal.owner_ref,"urn:pdks:owner:other")
        self.assertEqual(self.rt.list_captures(principal.owner_ref),[])

    def test_http_api_capture_with_bearer_token(self):
        token=self.rt.issue_token(OWNER,"agent-http",["capture:write","capture:read"])
        server=ThreadingHTTPServer(("127.0.0.1",0),make_handler(self.rt))
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        try:
            import urllib.request
            body=json.dumps({"text":"API capture test","domain":"work"}).encode()
            req=urllib.request.Request(f"http://127.0.0.1:{server.server_port}/v1/captures/text",
                data=body,method="POST",headers={"Authorization":"Bearer "+token["token"],"Content-Type":"application/json"})
            with urllib.request.urlopen(req) as response:
                data=json.loads(response.read())
            self.assertEqual(data["status"],"awaiting_agent")
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)

if __name__=="__main__":
    unittest.main()
