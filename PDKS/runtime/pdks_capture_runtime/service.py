from __future__ import annotations
from pathlib import Path
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import json
import os
import secrets
import shutil
import sqlite3
from contextlib import contextmanager
import uuid
import zipfile
import io

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    Draft202012Validator = None
    FormatChecker = None

from .errors import (
    AuthorizationError, ConsentRequiredError, ConflictError,
    NotFoundError, PayloadTooLargeError, ValidationError
)
from .extractors import extract_text, source_type_for, media_type_for, chunk_text
from .models import (
    API_SCOPES, CAPTURE_METHODS, CONSENT_REQUIRED_METHODS, DOMAINS,
    SENSITIVITY, SOURCE_KINDS, Principal, dumps, loads, utc_now, parse_time
)

MAX_CAPTURE_BYTES = 10 * 1024 * 1024

class CaptureRuntime:
    """Single-owner local reference runtime. Not production-hardened."""

    def __init__(self, db_path: str | Path, vault_dir: str | Path, schema_path: str | Path | None = None):
        self.db_path = Path(db_path).expanduser().resolve()
        self.vault_dir = Path(vault_dir).expanduser().resolve()
        self.schema_path = Path(schema_path).resolve() if schema_path else Path(__file__).parent / "assets" / "pdks-0.1-record.schema.json"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()
        try:
            self.db_path.chmod(0o600)
            self.vault_dir.chmod(0o700)
        except OSError:
            pass
        self._schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
        if Draft202012Validator is None:
            raise RuntimeError("jsonschema is required. Install runtime/requirements.txt.")
        self._validator = Draft202012Validator(self._schema, format_checker=FormatChecker())

    def _connect(self):
        con = sqlite3.connect(self.db_path, timeout=10, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=FULL")
        return con

    @contextmanager
    def _connection(self):
        con = self._connect()
        try:
            yield con
        finally:
            con.close()

    @contextmanager
    def _transaction(self):
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            yield con
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def _init_db(self):
        with self._connection() as con:
            con.executescript("""
            CREATE TABLE IF NOT EXISTS owners(
              owner_ref TEXT PRIMARY KEY, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS consents(
              consent_ref TEXT PRIMARY KEY, owner_ref TEXT NOT NULL,
              source_kind TEXT NOT NULL, purposes_json TEXT NOT NULL,
              scopes_json TEXT NOT NULL, data_categories_json TEXT NOT NULL,
              actions_json TEXT NOT NULL, issued_at TEXT NOT NULL,
              expires_at TEXT, revoked_at TEXT, status TEXT NOT NULL,
              note TEXT, FOREIGN KEY(owner_ref) REFERENCES owners(owner_ref)
            );
            CREATE TABLE IF NOT EXISTS api_tokens(
              token_hash TEXT PRIMARY KEY, owner_ref TEXT NOT NULL,
              agent_id TEXT NOT NULL, scopes_json TEXT NOT NULL,
              created_at TEXT NOT NULL, revoked_at TEXT,
              FOREIGN KEY(owner_ref) REFERENCES owners(owner_ref)
            );
            CREATE TABLE IF NOT EXISTS captures(
              capture_id TEXT PRIMARY KEY, owner_ref TEXT NOT NULL,
              status TEXT NOT NULL, source_kind TEXT NOT NULL,
              capture_method TEXT NOT NULL, source_id TEXT NOT NULL,
              extracted_text TEXT, warnings_json TEXT NOT NULL,
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
              idempotency_key TEXT, FOREIGN KEY(owner_ref) REFERENCES owners(owner_ref),
              UNIQUE(owner_ref,idempotency_key)
            );
            CREATE TABLE IF NOT EXISTS source_assets(
              source_id TEXT PRIMARY KEY, capture_id TEXT NOT NULL,
              owner_ref TEXT NOT NULL, source_kind TEXT NOT NULL,
              source_type TEXT NOT NULL, origin_system TEXT,
              source_locator TEXT, filename TEXT, media_type TEXT,
              content_hash TEXT, size_bytes INTEGER, captured_at TEXT,
              occurred_at TEXT, capture_method TEXT NOT NULL,
              consent_ref TEXT, domain TEXT NOT NULL, sensitivity TEXT NOT NULL,
              status TEXT NOT NULL, raw_path TEXT, source_record_json TEXT,
              created_at TEXT NOT NULL,
              FOREIGN KEY(owner_ref) REFERENCES owners(owner_ref)
            );
            CREATE TABLE IF NOT EXISTS evidence_segments(
              evidence_id TEXT PRIMARY KEY, source_id TEXT NOT NULL,
              owner_ref TEXT NOT NULL, locator TEXT NOT NULL,
              modality TEXT NOT NULL, excerpt TEXT, evidence_record_json TEXT,
              created_at TEXT NOT NULL,
              FOREIGN KEY(source_id) REFERENCES source_assets(source_id),
              FOREIGN KEY(owner_ref) REFERENCES owners(owner_ref)
            );
            CREATE TABLE IF NOT EXISTS records(
              record_id TEXT PRIMARY KEY, owner_ref TEXT NOT NULL,
              object_type TEXT NOT NULL, record_json TEXT,
              review_state TEXT NOT NULL, agent_id TEXT NOT NULL,
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
              deleted_at TEXT, FOREIGN KEY(owner_ref) REFERENCES owners(owner_ref)
            );
            CREATE TABLE IF NOT EXISTS record_sources(
              record_id TEXT NOT NULL, source_id TEXT NOT NULL,
              PRIMARY KEY(record_id,source_id),
              FOREIGN KEY(record_id) REFERENCES records(record_id),
              FOREIGN KEY(source_id) REFERENCES source_assets(source_id)
            );
            CREATE TABLE IF NOT EXISTS audit_log(
              audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
              owner_ref TEXT NOT NULL, actor_id TEXT NOT NULL,
              operation TEXT NOT NULL, object_refs_json TEXT NOT NULL,
              outcome TEXT NOT NULL, created_at TEXT NOT NULL,
              FOREIGN KEY(owner_ref) REFERENCES owners(owner_ref)
            );
            CREATE INDEX IF NOT EXISTS idx_captures_owner_time ON captures(owner_ref,created_at);
            CREATE INDEX IF NOT EXISTS idx_records_owner_state ON records(owner_ref,review_state);
            CREATE INDEX IF NOT EXISTS idx_sources_owner_status ON source_assets(owner_ref,status);
            """)

    def _audit(self, con, owner_ref, actor_id, operation, refs, outcome="success"):
        con.execute(
            "INSERT INTO audit_log(owner_ref,actor_id,operation,object_refs_json,outcome,created_at) VALUES(?,?,?,?,?,?)",
            (owner_ref, actor_id, operation, dumps(refs), outcome, utc_now())
        )

    def create_owner(self, owner_ref: str):
        if not owner_ref or not owner_ref.strip():
            raise ValidationError("owner_ref must not be empty")
        with self._connection() as con:
            con.execute("INSERT OR IGNORE INTO owners(owner_ref,created_at) VALUES(?,?)", (owner_ref, utc_now()))
        return {"owner_ref": owner_ref, "status": "ready"}

    def issue_token(self, owner_ref: str, agent_id: str, scopes: list[str]):
        if not agent_id:
            raise ValidationError("agent_id is required")
        invalid = sorted(set(scopes) - API_SCOPES)
        if invalid:
            raise ValidationError(f"Unknown API scopes: {invalid}")
        with self._transaction() as con:
            if not con.execute("SELECT 1 FROM owners WHERE owner_ref=?", (owner_ref,)).fetchone():
                raise NotFoundError("Owner does not exist; initialize it first.")
            token = secrets.token_urlsafe(36)
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            con.execute(
                "INSERT INTO api_tokens(token_hash,owner_ref,agent_id,scopes_json,created_at) VALUES(?,?,?,?,?)",
                (token_hash, owner_ref, agent_id, dumps(sorted(set(scopes))), utc_now())
            )
            self._audit(con, owner_ref, "owner-cli", "token.issue", [agent_id])
        return {"token": token, "agent_id": agent_id, "scopes": sorted(set(scopes)), "warning": "Token is shown once. Store it in the host secret manager; never commit it."}

    def revoke_token(self, owner_ref: str, agent_id: str):
        with self._transaction() as con:
            cur = con.execute("UPDATE api_tokens SET revoked_at=? WHERE owner_ref=? AND agent_id=? AND revoked_at IS NULL",
                              (utc_now(), owner_ref, agent_id))
            self._audit(con, owner_ref, "owner-cli", "token.revoke", [agent_id])
            return {"agent_id": agent_id, "revoked_tokens": cur.rowcount}

    def authenticate(self, token: str) -> Principal:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with self._connection() as con:
            row = con.execute("SELECT * FROM api_tokens WHERE token_hash=? AND revoked_at IS NULL", (token_hash,)).fetchone()
        if not row:
            raise AuthorizationError("Invalid or revoked bearer token")
        return Principal(row["owner_ref"], row["agent_id"], frozenset(loads(row["scopes_json"], [])))

    def _require_scope(self, principal: Principal, scope: str):
        if scope not in principal.scopes:
            raise AuthorizationError(f"Token lacks required scope: {scope}")

    def create_consent(self, owner_ref: str, source_kind: str, purposes: list[str],
                       scopes: list[str], data_categories: list[str], actions: list[str],
                       expires_at: str | None = None, note: str | None = None, actor_id="owner"):
        if source_kind not in SOURCE_KINDS:
            raise ValidationError(f"Unsupported source_kind: {source_kind}")
        if not purposes or not scopes or not data_categories or not actions:
            raise ValidationError("purposes, scopes, data_categories and actions must be explicit and non-empty")
        if "capture" not in actions:
            raise ValidationError("Consent must explicitly include action 'capture'")
        if expires_at and parse_time(expires_at) is None:
            raise ValidationError("expires_at must be an ISO-8601 timestamp")
        consent_ref = "urn:pdks:consent:" + str(uuid.uuid4())
        with self._transaction() as con:
            if not con.execute("SELECT 1 FROM owners WHERE owner_ref=?", (owner_ref,)).fetchone():
                raise NotFoundError("Owner does not exist")
            con.execute("""INSERT INTO consents(consent_ref,owner_ref,source_kind,purposes_json,scopes_json,
                data_categories_json,actions_json,issued_at,expires_at,status,note)
                VALUES(?,?,?,?,?,?,?,?,?,'active',?)""",
                (consent_ref, owner_ref, source_kind, dumps(purposes), dumps(scopes),
                 dumps(data_categories), dumps(actions), utc_now(), expires_at, note))
            self._audit(con, owner_ref, actor_id, "consent.create", [consent_ref])
        return {"consent_ref": consent_ref, "status": "active", "source_kind": source_kind,
                "purposes": purposes, "scopes": scopes, "data_categories": data_categories,
                "actions": actions, "expires_at": expires_at}

    def revoke_consent(self, owner_ref: str, consent_ref: str, actor_id="owner"):
        with self._transaction() as con:
            row = con.execute("SELECT * FROM consents WHERE consent_ref=? AND owner_ref=?", (consent_ref, owner_ref)).fetchone()
            if not row:
                raise NotFoundError("Consent not found")
            con.execute("UPDATE consents SET revoked_at=?,status='revoked' WHERE consent_ref=?", (utc_now(), consent_ref))
            self._audit(con, owner_ref, actor_id, "consent.revoke", [consent_ref])
        return {"consent_ref": consent_ref, "status": "revoked",
                "note": "Future capture is blocked. Existing data is not deleted automatically."}

    def _check_consent(self, owner_ref, source_kind, domain, consent_ref):
        if not consent_ref:
            raise ConsentRequiredError(f"{source_kind} requires an explicit active consent_ref")
        with self._connection() as con:
            row = con.execute("SELECT * FROM consents WHERE consent_ref=? AND owner_ref=?", (consent_ref, owner_ref)).fetchone()
        if not row or row["status"] != "active" or row["revoked_at"]:
            raise ConsentRequiredError("Consent is missing, revoked, or not active")
        if row["source_kind"] != source_kind:
            raise ConsentRequiredError("Consent source_kind does not match capture source")
        now = datetime.now(timezone.utc)
        expires = parse_time(row["expires_at"])
        if expires and expires <= now:
            raise ConsentRequiredError("Consent has expired")
        granted_scopes = loads(row["scopes_json"], [])
        if not any(scope == "read" or scope.startswith("read_") for scope in granted_scopes):
            raise ConsentRequiredError("Consent does not authorize read access")
        if "capture" not in loads(row["actions_json"], []):
            raise ConsentRequiredError("Consent does not authorize capture")
        if "personal_knowledge_capture" not in loads(row["purposes_json"], []):
            raise ConsentRequiredError("Consent purpose must include personal_knowledge_capture")
        categories = loads(row["data_categories_json"], [])
        if "*" not in categories and domain not in categories:
            raise ConsentRequiredError(f"Consent does not cover data category: {domain}")
        return row

    def _store_blob(self, data: bytes, filename: str):
        digest = hashlib.sha256(data).hexdigest()
        suffix = Path(filename).suffix.lower()[:12]
        directory = self.vault_dir / digest[:2]
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / (digest + suffix)
        if not path.exists():
            path.write_bytes(data)
            try: path.chmod(0o600)
            except OSError: pass
        return digest, path

    def _source_record(self, source_id, owner_ref, source_type, origin_system, source_locator,
                       captured_at, media_type, digest, size, capture_method, consent_ref,
                       domain, sensitivity):
        now = utc_now()
        return {
            "pdks_version": "0.1.0",
            "object_id": source_id,
            "object_type": "source_asset",
            "created_at": now, "updated_at": now, "owner_ref": owner_ref,
            "domains": [domain],
            "provenance": {"created_by": "urn:pdks:runtime:capture"},
            "governance": {"sensitivity": sensitivity, "access_scope": "owner_only",
                           **({"consent_ref": consent_ref} if consent_ref else {})},
            "lifecycle": {"status": "active", "version": 1},
            "payload": {
                "source_type": source_type, "origin_system": origin_system or "user_provided",
                "source_locator": source_locator, "captured_at": captured_at,
                "media_type": media_type, "content_hash": {"algorithm": "sha256", "value": digest},
                "size_bytes": size, "capture_method": capture_method,
                "extensions": {"runtime_version": "0.1.1", "source_kind": "unknown"}
            }
        }

    def _evidence_record(self, evidence_id, source_id, owner_ref, domain, sensitivity, start, end, excerpt):
        now = utc_now()
        return {
            "pdks_version": "0.1.0", "object_id": evidence_id, "object_type": "evidence_segment",
            "created_at": now, "updated_at": now, "owner_ref": owner_ref, "domains": [domain],
            "provenance": {"created_by": "urn:pdks:runtime:evidence", "source_refs": [source_id]},
            "governance": {"sensitivity": sensitivity, "access_scope": "owner_only"},
            "lifecycle": {"status": "active", "version": 1},
            "payload": {"source_ref": source_id,
                        "locator": {"kind": "text", "char_start": start, "char_end": end},
                        "excerpt": excerpt, "modality": "text", "transcript_status": "not_applicable"}
        }

    def _capture(self, owner_ref, data, filename, source_kind="manual", origin_system=None,
                 source_locator=None, domain="other", sensitivity="personal_private",
                 capture_method="manual_upload", consent_ref=None, occurred_at=None,
                 idempotency_key=None, declared_source_type=None, actor_id="owner"):
        if source_kind not in SOURCE_KINDS: raise ValidationError(f"Unsupported source_kind: {source_kind}")
        if capture_method not in CAPTURE_METHODS: raise ValidationError(f"Unsupported capture_method: {capture_method}")
        if domain not in DOMAINS: raise ValidationError(f"Unsupported domain: {domain}")
        if sensitivity not in SENSITIVITY: raise ValidationError(f"Unsupported sensitivity: {sensitivity}")
        if not isinstance(data, bytes): raise ValidationError("Capture data must be bytes")
        if len(data) > MAX_CAPTURE_BYTES: raise PayloadTooLargeError(f"Maximum capture size is {MAX_CAPTURE_BYTES} bytes")
        if occurred_at and parse_time(occurred_at) is None:
            raise ValidationError("occurred_at must be an ISO-8601 timestamp; use unknown rather than inventing a date")
        if capture_method in CONSENT_REQUIRED_METHODS:
            self._check_consent(owner_ref, source_kind, domain, consent_ref)
        elif consent_ref:
            with self._connection() as con:
                grant=con.execute("SELECT status,revoked_at FROM consents WHERE consent_ref=? AND owner_ref=?",
                                  (consent_ref,owner_ref)).fetchone()
            if not grant or grant["status"]!="active" or grant["revoked_at"]:
                raise ConsentRequiredError("A supplied consent_ref must resolve to an active grant for this owner")
        safe_filename = Path(filename.replace("\\", "/")).name or "upload.bin"
        digest = hashlib.sha256(data).hexdigest()
        locator = source_locator or ("upload://" + safe_filename)
        with self._connection() as con:
            if not con.execute("SELECT 1 FROM owners WHERE owner_ref=?", (owner_ref,)).fetchone():
                raise NotFoundError("Owner does not exist")
            if idempotency_key:
                prior = con.execute("""SELECT c.capture_id,c.source_id,c.status,s.content_hash
                    FROM captures c JOIN source_assets s ON c.source_id=s.source_id
                    WHERE c.owner_ref=? AND c.idempotency_key=?""",
                    (owner_ref,idempotency_key)).fetchone()
                if prior:
                    if prior["content_hash"] != digest:
                        raise ConflictError("Idempotency key was reused with different content")
                    return {"capture_id":prior["capture_id"],"source_id":prior["source_id"],
                            "status":prior["status"],"duplicate":True}
            duplicate = con.execute("""SELECT capture_id,source_id FROM source_assets
                WHERE owner_ref=? AND source_kind=? AND content_hash=? AND source_locator=? AND status='active'""",
                (owner_ref,source_kind,digest,locator)).fetchone()
            if duplicate:
                return {"capture_id":duplicate["capture_id"],"source_id":duplicate["source_id"],
                        "status":"duplicate","duplicate":True}
        digest, raw_path = self._store_blob(data, safe_filename)
        media = media_type_for(safe_filename)
        source_type = source_type_for(safe_filename, declared_source_type)
        if source_type not in {"audio","message","document","email","image","video","webpage","calendar_record","note","other"}:
            raise ValidationError("source_type is outside PDKS 0.1 vocabulary")
        extracted, extract_status, media, warnings = extract_text(data, filename, media)
        captured_at = utc_now()
        source_id = "urn:pdks:source:" + str(uuid.uuid4())
        capture_id = "urn:pdks:capture:" + str(uuid.uuid4())
        source_record = self._source_record(source_id, owner_ref, source_type, origin_system,
            locator, captured_at, media, digest, len(data), capture_method, consent_ref, domain, sensitivity)
        source_record["payload"]["extensions"]["source_kind"] = source_kind
        source_record["payload"]["extensions"]["extract_status"] = extract_status
        if occurred_at:
            source_record["payload"]["original_created_at"] = occurred_at
        self._validate_record(source_record,owner_ref)
        with self._transaction() as con:
            if not con.execute("SELECT 1 FROM owners WHERE owner_ref=?", (owner_ref,)).fetchone():
                raise NotFoundError("Owner does not exist")
            if idempotency_key:
                prior = con.execute("""SELECT c.capture_id,c.source_id,c.status,s.content_hash
                    FROM captures c JOIN source_assets s ON c.source_id=s.source_id
                    WHERE c.owner_ref=? AND c.idempotency_key=?""",
                    (owner_ref,idempotency_key)).fetchone()
                if prior:
                    if prior["content_hash"] != digest:
                        raise ConflictError("Idempotency key was reused with different content")
                    return {"capture_id": prior["capture_id"], "source_id": prior["source_id"],
                            "status": prior["status"], "duplicate": True}
            # Same owner, same source kind and content hash is treated as a duplicate source.
            duplicate = con.execute("SELECT capture_id,source_id FROM source_assets WHERE owner_ref=? AND source_kind=? AND content_hash=? AND source_locator=? AND status='active'",
                                     (owner_ref,source_kind,digest,locator)).fetchone()
            if duplicate:
                return {"capture_id": duplicate["capture_id"], "source_id": duplicate["source_id"],
                        "status": "duplicate", "duplicate": True}
            con.execute("""INSERT INTO source_assets(source_id,capture_id,owner_ref,source_kind,source_type,
                origin_system,source_locator,filename,media_type,content_hash,size_bytes,captured_at,occurred_at,
                capture_method,consent_ref,domain,sensitivity,status,raw_path,source_record_json,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'active',?,?,?)""",
                (source_id,capture_id,owner_ref,source_kind,source_type,origin_system or "user_provided",
                 locator,safe_filename,media,digest,len(data),captured_at,occurred_at,capture_method,
                 consent_ref,domain,sensitivity,str(raw_path),dumps(source_record),captured_at))
            status = "awaiting_agent" if extracted else "awaiting_extractor"
            con.execute("""INSERT INTO captures(capture_id,owner_ref,status,source_kind,capture_method,source_id,
                extracted_text,warnings_json,created_at,updated_at,idempotency_key)
                VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (capture_id,owner_ref,status,source_kind,capture_method,source_id,extracted,dumps(warnings),
                 captured_at,captured_at,idempotency_key))
            if extracted:
                for start,end,excerpt in chunk_text(extracted):
                    evidence_id = "urn:pdks:evidence:" + str(uuid.uuid4())
                    evidence_record = self._evidence_record(evidence_id,source_id,owner_ref,domain,sensitivity,start,end,excerpt)
                    self._validate_record(evidence_record,owner_ref)
                    con.execute("""INSERT INTO evidence_segments(evidence_id,source_id,owner_ref,locator,modality,
                        excerpt,evidence_record_json,created_at) VALUES(?,?,?,?,?,?,?,?)""",
                        (evidence_id,source_id,owner_ref,f"char:{start}-{end}","text",excerpt,dumps(evidence_record),captured_at))
            self._audit(con,owner_ref,actor_id,"capture.ingest",[capture_id,source_id],status)
        return {"capture_id":capture_id,"source_id":source_id,"status":status,"source_type":source_type,
                "extract_status":extract_status,"content_hash":digest,"size_bytes":len(data),
                "evidence_segments":len(chunk_text(extracted)) if extracted else 0,"warnings":warnings,"duplicate":False}

    def capture_text(self, owner_ref: str, text: str, source_kind="manual", origin_system="manual_entry",
                     source_locator=None, domain="other", sensitivity="personal_private",
                     capture_method="manual_upload", consent_ref=None, occurred_at=None,
                     idempotency_key=None, actor_id="owner", declared_source_type="note"):
        if not isinstance(text,str) or not text.strip(): raise ValidationError("text must not be empty")
        return self._capture(owner_ref,text.encode("utf-8"),"capture.txt",source_kind,origin_system,
            source_locator,domain,sensitivity,capture_method,consent_ref,occurred_at,idempotency_key,
            declared_source_type,actor_id)

    def capture_file(self, owner_ref: str, filename: str, data: bytes, **kwargs):
        safe_name=Path(filename.replace("\\","/")).name or "upload.bin"
        return self._capture(owner_ref,data,safe_name,**kwargs)

    def get_capture(self, owner_ref: str, capture_id: str):
        with self._connection() as con:
            row = con.execute("""SELECT c.*,s.source_kind AS source_kind_record,s.source_type,
                s.source_locator,s.captured_at,s.occurred_at,s.capture_method AS source_capture_method,
                s.origin_system,s.filename,s.media_type,s.content_hash,s.size_bytes,
                s.domain,s.sensitivity,s.consent_ref,s.status AS source_status
                FROM captures c JOIN source_assets s ON c.source_id=s.source_id
                WHERE c.owner_ref=? AND c.capture_id=?""",(owner_ref,capture_id)).fetchone()
        if not row: raise NotFoundError("Capture not found")
        return dict(row) | {"warnings": loads(row["warnings_json"],[])}

    def list_captures(self, owner_ref: str, limit=100):
        with self._connection() as con:
            rows = con.execute("""SELECT capture_id,status,source_kind,capture_method,source_id,created_at,updated_at
                FROM captures WHERE owner_ref=? ORDER BY created_at DESC LIMIT ?""",(owner_ref,min(max(limit,1),500))).fetchall()
        return [dict(r) for r in rows]

    def create_consent_from_principal(self, principal, payload):
        return self.create_consent(principal.owner_ref, actor_id=principal.agent_id, **payload)

    def _validate_record(self, record, owner_ref):
        errors = sorted(self._validator.iter_errors(record), key=lambda e: list(e.path))
        if errors:
            raise ValidationError("PDKS schema validation failed: " + "; ".join(f"{list(e.path)} {e.message}" for e in errors[:8]))
        if record.get("owner_ref") != owner_ref:
            raise AuthorizationError("Record owner_ref does not match authenticated owner")
        if record.get("governance",{}).get("access_scope") != "owner_only":
            raise AuthorizationError("0.5.0 prototype accepts owner_only records only")
        return True

    def propose_records(self, owner_ref: str, records: list[dict], source_ids: list[str], agent_id: str):
        if not records: raise ValidationError("records must not be empty")
        if not source_ids: raise ValidationError("source_ids must identify the source material used")
        with self._transaction() as con:
            placeholders = ",".join("?" for _ in source_ids)
            sources = con.execute(f"SELECT source_id,consent_ref FROM source_assets WHERE owner_ref=? AND status='active' AND source_id IN ({placeholders})",
                                  [owner_ref,*source_ids]).fetchall()
            source_map = {r["source_id"]:r["consent_ref"] for r in sources}
            if set(source_ids) != set(source_map):
                raise AuthorizationError("One or more source_ids are missing, deleted, or belong to another owner")
            inserted=[]
            for record in records:
                self._validate_record(record,owner_ref)
                refs = record.get("provenance",{}).get("source_refs",[])
                if not refs or not set(refs).issubset(set(source_ids)):
                    raise ValidationError("Every candidate record must cite one or more supplied source asset IDs")
                required_consents = {source_map[x] for x in refs if source_map[x]}
                record_consent = record.get("governance",{}).get("consent_ref")
                if required_consents and not required_consents.issubset({record_consent}):
                    raise AuthorizationError("Record governance.consent_ref must preserve the source consent reference")
                evidence_refs=record.get("payload",{}).get("evidence_refs",[])
                for evidence_ref in evidence_refs:
                    evidence=con.execute("""SELECT 1 FROM evidence_segments WHERE evidence_id=? AND owner_ref=?
                        AND source_id IN (""" + placeholders + ")",
                        [evidence_ref,owner_ref,*source_ids]).fetchone()
                    if not evidence:
                        raise ValidationError(f"evidence_ref does not resolve to supplied owner sources: {evidence_ref}")
                record_id = record["object_id"]
                if con.execute("SELECT 1 FROM records WHERE record_id=?",(record_id,)).fetchone():
                    raise ConflictError(f"Record already exists: {record_id}")
                now=utc_now()
                con.execute("""INSERT INTO records(record_id,owner_ref,object_type,record_json,review_state,
                    agent_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)""",
                    (record_id,owner_ref,record["object_type"],dumps(record),"candidate",agent_id,now,now))
                for source_id in refs:
                    con.execute("INSERT INTO record_sources(record_id,source_id) VALUES(?,?)",(record_id,source_id))
                inserted.append(record_id)
            self._audit(con,owner_ref,agent_id,"records.propose",inserted)
        return {"status":"needs_review","record_ids":inserted,"count":len(inserted),
                "note":"Candidate records are not owner-confirmed and are excluded from normal context/export by default."}

    def approve_record(self, owner_ref: str, record_id: str, actor_id="owner"):
        with self._transaction() as con:
            row=con.execute("SELECT * FROM records WHERE owner_ref=? AND record_id=?",(owner_ref,record_id)).fetchone()
            if not row: raise NotFoundError("Record not found")
            if row["review_state"] != "candidate": raise ConflictError("Only candidate records can be approved")
            con.execute("UPDATE records SET review_state='accepted',updated_at=? WHERE record_id=?",(utc_now(),record_id))
            self._audit(con,owner_ref,actor_id,"record.approve",[record_id])
        return {"record_id":record_id,"review_state":"accepted"}

    def list_records(self, owner_ref: str, review_state="accepted", limit=100):
        with self._connection() as con:
            if review_state == "all":
                rows=con.execute("SELECT record_id,object_type,review_state,agent_id,created_at,updated_at FROM records WHERE owner_ref=? AND record_json IS NOT NULL ORDER BY created_at DESC LIMIT ?",
                                 (owner_ref,min(max(limit,1),500))).fetchall()
            else:
                rows=con.execute("SELECT record_id,object_type,review_state,agent_id,created_at,updated_at FROM records WHERE owner_ref=? AND review_state=? AND record_json IS NOT NULL ORDER BY created_at DESC LIMIT ?",
                                 (owner_ref,review_state,min(max(limit,1),500))).fetchall()
        return [dict(r) for r in rows]

    def search_records(self, owner_ref: str, query: str, review_state="accepted", limit=50):
        if not query: return []
        with self._connection() as con:
            rows=con.execute("SELECT record_id,object_type,record_json,review_state FROM records WHERE owner_ref=? AND review_state=? AND record_json IS NOT NULL",
                             (owner_ref,review_state)).fetchall()
        q=query.casefold()
        out=[]
        for row in rows:
            obj=loads(row["record_json"],{})
            if q in json.dumps(obj,ensure_ascii=False).casefold():
                out.append({"record_id":row["record_id"],"object_type":row["object_type"],"review_state":row["review_state"],"record":obj})
            if len(out)>=limit: break
        return out

    def get_record(self, owner_ref: str, record_id: str):
        with self._connection() as con:
            row=con.execute("SELECT record_json,review_state,object_type,agent_id,created_at,updated_at FROM records WHERE owner_ref=? AND record_id=?",
                            (owner_ref,record_id)).fetchone()
        if not row or row["record_json"] is None:
            raise NotFoundError("Record not found or has been deleted")
        return {"record_id":record_id,"object_type":row["object_type"],"review_state":row["review_state"],
                "agent_id":row["agent_id"],"created_at":row["created_at"],"updated_at":row["updated_at"],
                "record":loads(row["record_json"])}

    def delete_source(self, owner_ref: str, source_id: str, actor_id="owner"):
        with self._transaction() as con:
            source=con.execute("SELECT * FROM source_assets WHERE owner_ref=? AND source_id=? AND status='active'",(owner_ref,source_id)).fetchone()
            if not source: raise NotFoundError("Active source not found")
            dependent=con.execute("SELECT record_id FROM record_sources WHERE source_id=?",(source_id,)).fetchall()
            record_ids=[r["record_id"] for r in dependent]
            raw_path=source["raw_path"]
            if raw_path:
                try: Path(raw_path).unlink(missing_ok=True)
                except OSError as exc: raise ConflictError(f"Could not delete source blob: {exc}")
            con.execute("DELETE FROM evidence_segments WHERE source_id=?",(source_id,))
            for rid in record_ids:
                con.execute("UPDATE records SET record_json=NULL,review_state='deleted_by_source_request',deleted_at=?,updated_at=? WHERE record_id=?",
                            (utc_now(),utc_now(),rid))
                con.execute("DELETE FROM record_sources WHERE record_id=?",(rid,))
            con.execute("""UPDATE source_assets SET source_kind='other',source_type='other',
                origin_system=NULL,source_locator=NULL,filename=NULL,media_type=NULL,content_hash=NULL,
                size_bytes=NULL,captured_at=NULL,occurred_at=NULL,capture_method='manual_upload',
                consent_ref=NULL,domain='other',sensitivity='personal_private',raw_path=NULL,
                source_record_json=NULL,status='deleted_tombstone' WHERE source_id=?""",(source_id,))
            con.execute("""UPDATE captures SET status='deleted',source_kind='manual',capture_method='manual_upload',
                extracted_text=NULL,warnings_json='[]',updated_at=? WHERE source_id=?""",(utc_now(),source_id))
            self._audit(con,owner_ref,actor_id,"source.delete",[source_id,*record_ids])
        return {"source_id":source_id,"status":"deleted_locally","dependent_records_purged":len(record_ids),
                "note":"Local source blob, extracted text, evidence and dependent record bodies were purged. External copies, OS snapshots and prior backups require separate cleanup."}

    def export_bundle(self, owner_ref: str, output_path: str | Path, include_candidates=False, include_raw_sources=False):
        output_path=Path(output_path).expanduser().resolve()
        states=("accepted","candidate") if include_candidates else ("accepted",)
        with self._transaction() as con:
            placeholders=",".join("?" for _ in states)
            records=con.execute(f"SELECT record_json FROM records WHERE owner_ref=? AND review_state IN ({placeholders}) AND record_json IS NOT NULL",
                                [owner_ref,*states]).fetchall()
            sources=con.execute("SELECT * FROM source_assets WHERE owner_ref=? AND status='active'",(owner_ref,)).fetchall()
            evidence=con.execute("SELECT evidence_record_json FROM evidence_segments WHERE owner_ref=? AND evidence_record_json IS NOT NULL",(owner_ref,)).fetchall()
        record_objs=[loads(r["record_json"]) for r in records]
        source_objs=[loads(r["source_record_json"]) for r in sources if r["source_record_json"]]
        evidence_objs=[loads(r["evidence_record_json"]) for r in evidence if r["evidence_record_json"]]
        payloads={
            "records/records.jsonl":"".join(dumps(x)+"\n" for x in record_objs).encode(),
            "sources/source-assets.jsonl":"".join(dumps(x)+"\n" for x in source_objs).encode(),
            "evidence/evidence-segments.jsonl":"".join(dumps(x)+"\n" for x in evidence_objs).encode()
        }
        if include_raw_sources:
            for source in sources:
                if source["raw_path"] and Path(source["raw_path"]).exists():
                    payloads[f"raw-sources/{source['source_id'].split(':')[-1]}-{Path(source['filename'] or 'source.bin').name}"]=Path(source["raw_path"]).read_bytes()
        manifest={
            "bundle_format":"PDKS-BUNDLE-0.2",
            "runtime_version":"0.1.1",
            "pdks_standard_version":"0.1.0",
            "record_schema_version":"0.1.x",
            "ontology_version":"0.2.1",
            "owner_ref":owner_ref,
            "exported_at":utc_now(),
            "include_candidates":include_candidates,
            "include_raw_sources":include_raw_sources,
            "counts":{"records":len(record_objs),"source_assets":len(source_objs),"evidence_segments":len(evidence_objs)},
            "files":{name:hashlib.sha256(data).hexdigest() for name,data in payloads.items()}
        }
        output_path.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(output_path,"w",zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json",dumps(manifest).encode())
            for name,data in payloads.items(): zf.writestr(name,data)
        try:
            output_path.chmod(0o600)
        except OSError:
            pass
        with self._transaction() as con:
            self._audit(con,owner_ref,"owner","data.export",[str(output_path.name)])
        return {"status":"exported","path":str(output_path),"counts":manifest["counts"],
                "include_raw_sources":include_raw_sources,"sha256":hashlib.sha256(output_path.read_bytes()).hexdigest()}

    def verify_bundle(self, bundle_path: str | Path):
        with zipfile.ZipFile(bundle_path) as zf:
            manifest=json.loads(zf.read("manifest.json"))
            errors=[]
            for name,digest in manifest.get("files",{}).items():
                if name not in zf.namelist():
                    errors.append(f"missing:{name}")
                elif hashlib.sha256(zf.read(name)).hexdigest()!=digest:
                    errors.append(f"hash_mismatch:{name}")
        return {"valid":not errors,"errors":errors,"bundle_format":manifest.get("bundle_format"),
                "owner_ref":manifest.get("owner_ref"),"counts":manifest.get("counts")}

    def capture_from_principal(self, principal: Principal, payload):
        return self.capture_text(principal.owner_ref, actor_id=principal.agent_id, **payload)

    def get_capture_for_principal(self, principal: Principal, capture_id):
        return self.get_capture(principal.owner_ref,capture_id)

    def propose_for_principal(self, principal: Principal, payload):
        return self.propose_records(principal.owner_ref,payload["records"],payload["source_ids"],principal.agent_id)

    def approve_for_principal(self, principal: Principal, record_id):
        return self.approve_record(principal.owner_ref,record_id,principal.agent_id)

    def get_record_for_principal(self, principal: Principal, record_id):
        return self.get_record(principal.owner_ref,record_id)
