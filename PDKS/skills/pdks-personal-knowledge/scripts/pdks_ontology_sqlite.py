#!/usr/bin/env python3
"""SQLite persistence for canonical PDKS records plus a rebuildable RDF projection."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from rdflib import Graph
from rdflib.util import from_n3

try:
    from .pdks_ontology_runtime import OntologyRuntime, OntologyValidationError
except ImportError:
    from pdks_ontology_runtime import OntologyRuntime, OntologyValidationError


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

def _sha(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()

def _owner_graph(owner_ref: str, ontology_version: str) -> str:
    owner_key = hashlib.sha256(owner_ref.encode("utf-8")).hexdigest()[:24]
    return f"urn:pdks:graph:owner:{owner_key}:ontology:{ontology_version}"

class ConcurrentWriteError(RuntimeError):
    pass

class ObjectConflictError(RuntimeError):
    pass

class OntologySQLiteStore:
    """Single-owner import batches, optimistic revisions, immutable object snapshots.

    Canonical JSON records are authoritative. `pdks_triples` is a materialized RDF
    projection and can be deleted/rebuilt from `pdks_objects` under another ontology.
    """

    def __init__(self, db_path: str | Path, runtime: OntologyRuntime | None = None, *, timeout_seconds: float = 15):
        self.db_path = str(Path(db_path).expanduser().resolve())
        if self.db_path == ":memory:":
            raise ValueError("Use a file-backed SQLite database for restart persistence.")
        self.runtime = runtime or OntologyRuntime()
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.timeout_seconds = timeout_seconds
        self._initialize()
        self.register_ontology()

    def _connect(self):
        conn = sqlite3.connect(self.db_path, timeout=self.timeout_seconds, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute(f"PRAGMA busy_timeout={int(self.timeout_seconds*1000)}")
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=FULL")
        return conn

    def _initialize(self):
        with closing(self._connect()) as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS pdks_ontology_registry(
              ontology_version TEXT PRIMARY KEY, ontology_iri TEXT NOT NULL,
              manifest_sha256 TEXT NOT NULL, registered_at TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS pdks_owner_state(
              owner_ref TEXT PRIMARY KEY, revision INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS pdks_objects(
              owner_ref TEXT NOT NULL, object_id TEXT NOT NULL, object_type TEXT NOT NULL,
              record_json TEXT NOT NULL, record_sha256 TEXT NOT NULL,
              ontology_version TEXT NOT NULL, record_version INTEGER NOT NULL,
              created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
              PRIMARY KEY(owner_ref,object_id),
              FOREIGN KEY(owner_ref) REFERENCES pdks_owner_state(owner_ref) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS pdks_object_versions(
              owner_ref TEXT NOT NULL, object_id TEXT NOT NULL, record_version INTEGER NOT NULL,
              record_json TEXT NOT NULL, record_sha256 TEXT NOT NULL, recorded_at TEXT NOT NULL,
              PRIMARY KEY(owner_ref,object_id,record_version)
            );
            CREATE TABLE IF NOT EXISTS pdks_triples(
              owner_ref TEXT NOT NULL, graph_iri TEXT NOT NULL, source_object_id TEXT NOT NULL,
              subject_iri TEXT NOT NULL, predicate_iri TEXT NOT NULL, object_n3 TEXT NOT NULL,
              ontology_version TEXT NOT NULL,
              PRIMARY KEY(owner_ref,graph_iri,source_object_id,subject_iri,predicate_iri,object_n3)
            );
            CREATE INDEX IF NOT EXISTS idx_pdks_triples_sp ON pdks_triples(owner_ref,subject_iri,predicate_iri);
            CREATE INDEX IF NOT EXISTS idx_pdks_triples_po ON pdks_triples(owner_ref,predicate_iri,object_n3);
            CREATE TABLE IF NOT EXISTS pdks_audit_log(
              audit_id INTEGER PRIMARY KEY AUTOINCREMENT, owner_ref TEXT NOT NULL,
              revision INTEGER NOT NULL, operation TEXT NOT NULL, actor_ref TEXT NOT NULL,
              object_count INTEGER NOT NULL, detail_json TEXT NOT NULL, created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS pdks_schema_migrations(
              version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL
            );
            INSERT OR IGNORE INTO pdks_schema_migrations(version,applied_at) VALUES(1,CURRENT_TIMESTAMP);
            """)

    def _ontology_manifest_hash(self) -> str:
        files = sorted(self.runtime.ontology_dir.glob("*"))
        digest = hashlib.sha256()
        for f in files:
            if f.is_file():
                digest.update(f.name.encode("utf-8"))
                digest.update(f.read_bytes())
        return digest.hexdigest()

    def register_ontology(self):
        with closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("UPDATE pdks_ontology_registry SET active=0")
            conn.execute(
                """INSERT INTO pdks_ontology_registry(ontology_version,ontology_iri,manifest_sha256,registered_at,active)
                   VALUES(?,?,?,?,1)
                   ON CONFLICT(ontology_version) DO UPDATE SET ontology_iri=excluded.ontology_iri,
                   manifest_sha256=excluded.manifest_sha256,active=1""",
                (self.runtime.ontology_version,self.runtime.ontology_iri,self._ontology_manifest_hash(),_now())
            )
            conn.commit()

    def revision(self, owner_ref: str) -> int:
        with closing(self._connect()) as conn:
            row=conn.execute("SELECT revision FROM pdks_owner_state WHERE owner_ref=?",(owner_ref,)).fetchone()
            return int(row["revision"]) if row else 0

    def import_records(self, owner_ref: str, records: Iterable[dict[str,Any]], *,
                       expected_revision: int | None = None, allow_updates: bool = False,
                       strict_refs: bool = False, actor_ref: str = "user:owner",
                       trusted_consent_refs: set[str] | None = None) -> dict[str,Any]:
        records=list(records)
        validation=self.runtime.validate_records(records,strict_refs=strict_refs,
                                                  trusted_consent_refs=trusted_consent_refs)
        if validation["status"]!="valid":
            raise OntologyValidationError(validation["errors"])
        if validation["owners"] != [owner_ref]:
            raise ValueError("All imported records must belong to the supplied owner_ref.")
        if not records:
            return {"status":"no_change","revision":self.revision(owner_ref),"inserted":0,"updated":0,"unchanged":0,"triples":0}
        projected={r["object_id"]:self.runtime.project_record(r) for r in records}
        graph_iri=_owner_graph(owner_ref,self.runtime.ontology_version)
        inserted=updated=unchanged=triple_count=0
        now=_now()
        with closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            state=conn.execute("SELECT revision FROM pdks_owner_state WHERE owner_ref=?",(owner_ref,)).fetchone()
            current=int(state["revision"]) if state else 0
            if expected_revision is not None and expected_revision!=current:
                conn.rollback()
                raise ConcurrentWriteError(f"Expected revision {expected_revision}, current revision is {current}.")
            if not state:
                conn.execute("INSERT INTO pdks_owner_state(owner_ref,revision,created_at,updated_at) VALUES(?,0,?,?)",(owner_ref,now,now))
            for record in records:
                oid=record["object_id"]
                body=_canonical(record)
                digest=_sha(record)
                existing=conn.execute("SELECT record_sha256,record_version FROM pdks_objects WHERE owner_ref=? AND object_id=?",(owner_ref,oid)).fetchone()
                if existing and existing["record_sha256"]==digest:
                    unchanged+=1
                    continue
                if existing and not allow_updates:
                    conn.rollback()
                    raise ObjectConflictError(f"Object {oid} already exists with different content; pass allow_updates=True after review.")
                version=(int(existing["record_version"])+1) if existing else 1
                conn.execute(
                    """INSERT INTO pdks_object_versions(owner_ref,object_id,record_version,record_json,record_sha256,recorded_at)
                       VALUES(?,?,?,?,?,?)""",(owner_ref,oid,version,body,digest,now)
                )
                conn.execute(
                    """INSERT INTO pdks_objects(owner_ref,object_id,object_type,record_json,record_sha256,ontology_version,record_version,created_at,updated_at)
                       VALUES(?,?,?,?,?,?,?,?,?)
                       ON CONFLICT(owner_ref,object_id) DO UPDATE SET object_type=excluded.object_type,
                       record_json=excluded.record_json,record_sha256=excluded.record_sha256,
                       ontology_version=excluded.ontology_version,record_version=excluded.record_version,updated_at=excluded.updated_at""",
                    (owner_ref,oid,record["object_type"],body,digest,self.runtime.ontology_version,version,record.get("created_at",now),record.get("updated_at",now))
                )
                conn.execute("DELETE FROM pdks_triples WHERE owner_ref=? AND source_object_id=?",(owner_ref,oid))
                graph=projected[oid]
                rows=[]
                for s,p,o in graph:
                    rows.append((owner_ref,graph_iri,oid,str(s),str(p),o.n3(),self.runtime.ontology_version))
                conn.executemany(
                    """INSERT OR IGNORE INTO pdks_triples(owner_ref,graph_iri,source_object_id,subject_iri,predicate_iri,object_n3,ontology_version)
                       VALUES(?,?,?,?,?,?,?)""",rows
                )
                triple_count+=len(rows)
                if existing: updated+=1
                else: inserted+=1
            changed=inserted+updated
            if changed:
                new_revision=current+1
                conn.execute("UPDATE pdks_owner_state SET revision=?,updated_at=? WHERE owner_ref=?",(new_revision,now,owner_ref))
                conn.execute(
                    """INSERT INTO pdks_audit_log(owner_ref,revision,operation,actor_ref,object_count,detail_json,created_at)
                       VALUES(?,?,?,?,?,?,?)""",
                    (owner_ref,new_revision,"ontology_import",actor_ref,changed,_canonical({"inserted":inserted,"updated":updated,"unchanged":unchanged,"ontology_version":self.runtime.ontology_version,"triple_assertions":triple_count,"trusted_consent_refs_verified":len(trusted_consent_refs or set())}),now)
                )
            else:
                new_revision=current
            conn.commit()
        unique_triples=len(self.export_graph(owner_ref))
        with closing(self._connect()) as conn:
            stored_assertions=conn.execute("SELECT COUNT(*) FROM pdks_triples WHERE owner_ref=?",(owner_ref,)).fetchone()[0]
        return {"status":"imported" if inserted or updated else "no_change","revision":new_revision,
                "inserted":inserted,"updated":updated,"unchanged":unchanged,"triples":unique_triples,
                "triple_assertions":stored_assertions,
                "ontology_version":self.runtime.ontology_version,"graph_iri":graph_iri}

    def list_objects(self, owner_ref: str, object_type: str | None = None) -> list[dict[str,Any]]:
        with closing(self._connect()) as conn:
            if object_type:
                rows=conn.execute("SELECT object_id,object_type,record_version,ontology_version,updated_at FROM pdks_objects WHERE owner_ref=? AND object_type=? ORDER BY object_id",(owner_ref,object_type)).fetchall()
            else:
                rows=conn.execute("SELECT object_id,object_type,record_version,ontology_version,updated_at FROM pdks_objects WHERE owner_ref=? ORDER BY object_type,object_id",(owner_ref,)).fetchall()
            return [dict(r) for r in rows]

    def get_object(self, owner_ref: str, object_id: str) -> dict[str,Any] | None:
        with closing(self._connect()) as conn:
            row=conn.execute("SELECT record_json FROM pdks_objects WHERE owner_ref=? AND object_id=?",(owner_ref,object_id)).fetchone()
            return json.loads(row["record_json"]) if row else None

    def export_graph(self, owner_ref: str) -> Graph:
        graph=Graph()
        self.runtime._bind(graph)
        with closing(self._connect()) as conn:
            rows=conn.execute("SELECT subject_iri,predicate_iri,object_n3 FROM pdks_triples WHERE owner_ref=? ORDER BY subject_iri,predicate_iri",(owner_ref,)).fetchall()
            for row in rows:
                graph.add((from_n3(f"<{row['subject_iri']}>"),from_n3(f"<{row['predicate_iri']}>"),from_n3(row["object_n3"])))
        return graph

    def export_turtle(self, owner_ref: str, output_path: str | Path | None = None) -> str:
        text=self.export_graph(owner_ref).serialize(format="turtle")
        if output_path:
            Path(output_path).write_text(text,encoding="utf-8")
        return text

    def query_subjects(self, owner_ref: str, predicate_iri: str, object_iri: str | None = None) -> list[str]:
        with closing(self._connect()) as conn:
            if object_iri:
                rows=conn.execute("SELECT DISTINCT subject_iri FROM pdks_triples WHERE owner_ref=? AND predicate_iri=? AND object_n3=? ORDER BY subject_iri",(owner_ref,predicate_iri,f"<{object_iri}>")).fetchall()
            else:
                rows=conn.execute("SELECT DISTINCT subject_iri FROM pdks_triples WHERE owner_ref=? AND predicate_iri=? ORDER BY subject_iri",(owner_ref,predicate_iri)).fetchall()
            return [r["subject_iri"] for r in rows]

    def query_sparql(self, owner_ref: str, query: str) -> list[dict[str,Any]]:
        """Run SPARQL against the selected owner's in-memory RDF projection."""
        graph=self.export_graph(owner_ref)
        result=graph.query(query)
        rows=[]
        for row in result:
            rows.append({str(var): (str(value) if value is not None else None)
                         for var,value in zip(result.vars,row)})
        return rows

    def audit(self, owner_ref: str) -> list[dict[str,Any]]:
        with closing(self._connect()) as conn:
            rows=conn.execute("SELECT revision,operation,actor_ref,object_count,detail_json,created_at FROM pdks_audit_log WHERE owner_ref=? ORDER BY audit_id",(owner_ref,)).fetchall()
            return [{**dict(r),"detail":json.loads(r["detail_json"])} for r in rows]

    def integrity_check(self) -> str:
        with closing(self._connect()) as conn:
            row=conn.execute("PRAGMA integrity_check").fetchone()
            return row[0]

    def rebuild_projection(self, owner_ref: str) -> dict[str,Any]:
        """Rebuild all RDF triples from canonical JSON records under the active ontology."""
        with closing(self._connect()) as conn:
            records=[json.loads(r["record_json"]) for r in conn.execute("SELECT record_json FROM pdks_objects WHERE owner_ref=? ORDER BY object_id",(owner_ref,)).fetchall()]
            current=self.revision(owner_ref)
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("DELETE FROM pdks_triples WHERE owner_ref=?",(owner_ref,))
            graph_iri=_owner_graph(owner_ref,self.runtime.ontology_version)
            count=0
            for record in records:
                graph=self.runtime.project_record(record)
                rows=[(owner_ref,graph_iri,record["object_id"],str(s),str(p),o.n3(),self.runtime.ontology_version) for s,p,o in graph]
                conn.executemany("INSERT OR IGNORE INTO pdks_triples(owner_ref,graph_iri,source_object_id,subject_iri,predicate_iri,object_n3,ontology_version) VALUES(?,?,?,?,?,?,?)",rows)
                count+=len(rows)
            conn.execute("UPDATE pdks_objects SET ontology_version=? WHERE owner_ref=?",(self.runtime.ontology_version,owner_ref))
            conn.commit()
        return {"status":"rebuilt","records":len(records),"triple_assertions":count,
                "triples":len(self.export_graph(owner_ref)),"revision":current,
                "ontology_version":self.runtime.ontology_version}

