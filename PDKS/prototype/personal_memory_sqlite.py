"""SQLite persistence adapter for the ADS-WORK-09 personal memory reference engine.

This module deliberately reuses the in-memory PersonalMemoryEngine's business rules.
SQLite provides local persistence, optimistic concurrency, owner partitioning and a
metadata-only append-only audit trail. It is a reference runtime, not a production
security boundary: authentication, encryption-at-rest, key management, policy services,
connector authorization and distributed synchronization remain host responsibilities.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

try:  # Package import when used as a module.
    from .personal_memory_engine import PersonalMemoryEngine
except ImportError:  # Direct import from prototype/ in existing test runner.
    from personal_memory_engine import PersonalMemoryEngine


STORE_SCHEMA_VERSION = 1
TRUSTED_AGENT_ACTORS = {"agent:pdks-ads-bridge"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_json(value).encode("utf-8")).hexdigest()


class ConcurrentWriteError(RuntimeError):
    """Raised when another engine instance has committed since this one loaded."""


class StoreIntegrityError(RuntimeError):
    """Raised when persisted JSON cannot be decoded or the store is inconsistent."""


class SQLitePersonalMemoryStore:
    """Owner-partitioned SQLite repository with transactional snapshot commits."""

    def __init__(self, db_path: str | Path, *, timeout_seconds: float = 15.0):
        self.db_path = str(Path(db_path).expanduser().resolve())
        if self.db_path == ":memory:":
            raise ValueError("Use a file-backed SQLite database so state survives connections and restarts.")
        self.timeout_seconds = timeout_seconds
        Path(self.db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=self.timeout_seconds, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(f"PRAGMA busy_timeout = {int(self.timeout_seconds * 1000)}")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = FULL")
        return conn

    def _initialize(self) -> None:
        with closing(self._connect()) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS owners (
                    owner_ref TEXT PRIMARY KEY,
                    revision INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    owner_ref TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY (owner_ref, record_id),
                    FOREIGN KEY (owner_ref) REFERENCES owners(owner_ref) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS memories (
                    owner_ref TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY (owner_ref, record_id),
                    FOREIGN KEY (owner_ref) REFERENCES owners(owner_ref) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS intents (
                    owner_ref TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY (owner_ref, record_id),
                    FOREIGN KEY (owner_ref) REFERENCES owners(owner_ref) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS actions (
                    owner_ref TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    PRIMARY KEY (owner_ref, record_id),
                    FOREIGN KEY (owner_ref) REFERENCES owners(owner_ref) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS suppressed_sources (
                    owner_ref TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    suppressed_at TEXT NOT NULL,
                    PRIMARY KEY (owner_ref, event_id),
                    FOREIGN KEY (owner_ref) REFERENCES owners(owner_ref) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS audit_log (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_ref TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    operation TEXT NOT NULL,
                    actor_ref TEXT NOT NULL,
                    record_type TEXT,
                    record_id TEXT,
                    state_digest TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (owner_ref) REFERENCES owners(owner_ref) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_audit_owner_revision
                    ON audit_log(owner_ref, revision);
                CREATE TRIGGER IF NOT EXISTS audit_log_no_update
                    BEFORE UPDATE ON audit_log BEGIN
                    SELECT RAISE(ABORT, 'audit_log is append-only');
                END;
                CREATE TRIGGER IF NOT EXISTS audit_log_no_delete
                    BEFORE DELETE ON audit_log BEGIN
                    SELECT RAISE(ABORT, 'audit_log is append-only');
                END;
                """
            )
            conn.execute(
                "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (STORE_SCHEMA_VERSION, _now()),
            )

    def load_owner_state(self, owner_ref: str) -> dict[str, Any]:
        if not owner_ref:
            raise ValueError("owner_ref is required")
        with closing(self._connect()) as conn:
            conn.execute("BEGIN")
            now = _now()
            conn.execute(
                "INSERT OR IGNORE INTO owners(owner_ref, revision, created_at, updated_at) VALUES (?, 0, ?, ?)",
                (owner_ref, now, now),
            )
            owner = conn.execute("SELECT revision FROM owners WHERE owner_ref = ?", (owner_ref,)).fetchone()
            state: dict[str, Any] = {
                "owner_ref": owner_ref,
                "revision": int(owner["revision"]),
                "events": [],
                "memories": [],
                "intents": [],
                "actions": [],
                "suppressed_sources": [],
            }
            for table, key in (("events", "events"), ("memories", "memories"), ("intents", "intents"), ("actions", "actions")):
                rows = conn.execute(
                    f"SELECT payload_json FROM {table} WHERE owner_ref = ? ORDER BY record_id", (owner_ref,)
                ).fetchall()
                try:
                    state[key] = [json.loads(row["payload_json"]) for row in rows]
                except json.JSONDecodeError as exc:
                    conn.rollback()
                    raise StoreIntegrityError(f"Invalid JSON in {table} for owner {owner_ref}") from exc
            state["suppressed_sources"] = [
                row["event_id"] for row in conn.execute(
                    "SELECT event_id FROM suppressed_sources WHERE owner_ref = ? ORDER BY event_id", (owner_ref,)
                ).fetchall()
            ]
            conn.commit()
            return state

    def save_owner_state(
        self,
        owner_ref: str,
        state: dict[str, Any],
        *,
        expected_revision: int,
        operation: str,
        actor_ref: str,
        record_type: str | None = None,
        record_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        if state.get("owner_ref", owner_ref) != owner_ref:
            raise PermissionError("Snapshot owner does not match the target owner partition.")
        now = _now()
        digest = _digest(state)
        with closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                "INSERT OR IGNORE INTO owners(owner_ref, revision, created_at, updated_at) VALUES (?, 0, ?, ?)",
                (owner_ref, now, now),
            )
            current = int(conn.execute("SELECT revision FROM owners WHERE owner_ref = ?", (owner_ref,)).fetchone()["revision"])
            if current != expected_revision:
                conn.rollback()
                raise ConcurrentWriteError(
                    f"Stale owner revision: expected {expected_revision}, current revision is {current}. Call refresh() before retrying."
                )

            for table in ("events", "memories", "intents", "actions", "suppressed_sources"):
                conn.execute(f"DELETE FROM {table} WHERE owner_ref = ?", (owner_ref,))

            for table, id_key, items in (
                ("events", "event_id", state.get("events", [])),
                ("memories", "memory_id", state.get("memories", [])),
                ("intents", "intent_id", state.get("intents", [])),
                ("actions", "proposal_id", state.get("actions", [])),
            ):
                for item in items:
                    record_id = item.get(id_key)
                    if not record_id:
                        conn.rollback()
                        raise ValueError(f"{table} item is missing {id_key}")
                    conn.execute(
                        f"INSERT INTO {table}(owner_ref, record_id, payload_json) VALUES (?, ?, ?)",
                        (owner_ref, record_id, _json(item)),
                    )

            for event_id in sorted(set(state.get("suppressed_sources", []))):
                conn.execute(
                    "INSERT INTO suppressed_sources(owner_ref, event_id, suppressed_at) VALUES (?, ?, ?)",
                    (owner_ref, event_id, now),
                )

            new_revision = current + 1
            conn.execute(
                "UPDATE owners SET revision = ?, updated_at = ? WHERE owner_ref = ?",
                (new_revision, now, owner_ref),
            )
            audit_metadata = {
                "counts": {
                    "events": len(state.get("events", [])),
                    "memories": len(state.get("memories", [])),
                    "intents": len(state.get("intents", [])),
                    "actions": len(state.get("actions", [])),
                    "suppressed_sources": len(state.get("suppressed_sources", [])),
                },
                **(metadata or {}),
            }
            conn.execute(
                """INSERT INTO audit_log(
                    owner_ref, revision, operation, actor_ref, record_type, record_id,
                    state_digest, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (owner_ref, new_revision, operation, actor_ref, record_type, record_id,
                 digest, _json(audit_metadata), now),
            )
            conn.commit()
            return new_revision

    def get_audit_log(self, owner_ref: str, *, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 1000))
        with closing(self._connect()) as conn:
            rows = conn.execute(
                """SELECT sequence, revision, operation, actor_ref, record_type, record_id,
                          state_digest, metadata_json, created_at
                   FROM audit_log WHERE owner_ref = ? ORDER BY sequence DESC LIMIT ?""",
                (owner_ref, limit),
            ).fetchall()
        return [
            {
                "sequence": row["sequence"], "revision": row["revision"],
                "operation": row["operation"], "actor_ref": row["actor_ref"],
                "record_type": row["record_type"], "record_id": row["record_id"],
                "state_digest": row["state_digest"], "metadata": json.loads(row["metadata_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def integrity_check(self) -> str:
        with closing(self._connect()) as conn:
            rows = conn.execute("PRAGMA integrity_check").fetchall()
        return "; ".join(row[0] for row in rows)

    def backup_to(self, destination: str | Path) -> Path:
        destination = Path(destination).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination == Path(self.db_path).expanduser().resolve():
            raise ValueError("Backup destination must differ from the live database path.")
        with closing(self._connect()) as source:
            target = sqlite3.connect(str(destination))
            try:
                source.backup(target)
                target.execute("PRAGMA integrity_check")
                target.commit()
            finally:
                target.close()
        return destination


class SQLiteBackedPersonalMemoryEngine(PersonalMemoryEngine):
    """Persistent ADS-WORK-09 engine; business rules delegate to PersonalMemoryEngine."""

    def __init__(self, owner_ref: str, db_path: str | Path | None = None, *, store: SQLitePersonalMemoryStore | None = None):
        super().__init__(owner_ref)
        if store is None and db_path is None:
            raise ValueError("Provide db_path or store")
        self.store = store or SQLitePersonalMemoryStore(db_path)  # type: ignore[arg-type]
        self._revision = 0
        self._apply_state(self.store.load_owner_state(owner_ref))

    def _snapshot(self, engine: PersonalMemoryEngine | None = None) -> dict[str, Any]:
        source = engine or self
        return {
            "owner_ref": self.owner_ref,
            "events": deepcopy(source.events),
            "memories": deepcopy(list(source.memories.values())),
            "intents": deepcopy(list(source.intents.values())),
            "actions": deepcopy(list(source.actions.values())),
            "suppressed_sources": sorted(source.suppressed_sources),
        }

    def _apply_state(self, state: dict[str, Any]) -> None:
        self.events = deepcopy(state.get("events", []))
        self.memories = {x["memory_id"]: deepcopy(x) for x in state.get("memories", [])}
        self.intents = {x["intent_id"]: deepcopy(x) for x in state.get("intents", [])}
        self.actions = {x["proposal_id"]: deepcopy(x) for x in state.get("actions", [])}
        self.suppressed_sources = set(state.get("suppressed_sources", []))
        self._revision = int(state.get("revision", 0))

    def refresh(self) -> int:
        """Reload committed state after a ConcurrentWriteError or external update."""
        self._apply_state(self.store.load_owner_state(self.owner_ref))
        return self._revision

    def _mutate(
        self,
        operation: str,
        fn: Callable[[PersonalMemoryEngine], Any],
        *,
        actor_ref: str,
        record_type: str | None = None,
        record_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        candidate = PersonalMemoryEngine(self.owner_ref)
        candidate.events = deepcopy(self.events)
        candidate.memories = deepcopy(self.memories)
        candidate.intents = deepcopy(self.intents)
        candidate.actions = deepcopy(self.actions)
        candidate.suppressed_sources = set(self.suppressed_sources)
        result = fn(candidate)
        snapshot = self._snapshot(candidate)
        if snapshot == self._snapshot():  # Exact idempotent replay: no extra revision.
            return deepcopy(result)
        new_revision = self.store.save_owner_state(
            self.owner_ref, snapshot, expected_revision=self._revision,
            operation=operation, actor_ref=actor_ref, record_type=record_type,
            record_id=record_id, metadata=metadata,
        )
        self._apply_state({**snapshot, "revision": new_revision})
        return deepcopy(result)

    def append_event(self, event: dict[str, Any]) -> dict[str, Any]:
        return self._mutate(
            "append_event", lambda e: e.append_event(event),
            actor_ref=event.get("subject_ref", "unknown"), record_type="event",
            record_id=event.get("event_id"),
        )

    def derive_memory(self, event_id: str, memory_id: str, memory_type: str, statement: str, **kwargs: Any) -> dict[str, Any]:
        return self._mutate(
            "derive_memory",
            lambda e: e.derive_memory(event_id, memory_id, memory_type, statement, **kwargs),
            actor_ref="agent:personal-memory-engine", record_type="memory", record_id=memory_id,
            metadata={"source_event_id": event_id},
        )

    def confirm_memory(self, memory_id: str, *, actor_ref: str) -> dict[str, Any]:
        return self._mutate(
            "confirm_memory", lambda e: e.confirm_memory(memory_id, actor_ref=actor_ref),
            actor_ref=actor_ref, record_type="memory", record_id=memory_id,
        )

    def correct_memory(self, old_memory_id: str, new_memory: dict[str, Any], *, actor_ref: str) -> dict[str, Any]:
        return self._mutate(
            "correct_memory", lambda e: e.correct_memory(old_memory_id, new_memory, actor_ref=actor_ref),
            actor_ref=actor_ref, record_type="memory", record_id=new_memory.get("memory_id"),
            metadata={"supersedes": old_memory_id},
        )

    def withdraw_memory(self, memory_id: str, *, actor_ref: str) -> None:
        return self._mutate(
            "withdraw_memory", lambda e: e.withdraw_memory(memory_id, actor_ref=actor_ref),
            actor_ref=actor_ref, record_type="memory", record_id=memory_id,
        )

    def forget_source_event(self, event_id: str, *, actor_ref: str) -> None:
        def apply(engine: PersonalMemoryEngine) -> None:
            engine.forget_source_event(event_id, actor_ref=actor_ref)
            # Do not silently delete a user's commitment. Pause derived Intents and require review.
            for intent in engine.intents.values():
                if event_id in intent.get("source_event_refs", []):
                    intent.setdefault("extensions", {})["source_suppressed"] = True
                    intent["extensions"]["requires_owner_review"] = True
                    if intent.get("status") in {"proposed", "active", "blocked"}:
                        intent["status"] = "paused"
                    intent["updated_at"] = _now()

        return self._mutate(
            "suppress_source_event", apply,
            actor_ref=actor_ref, record_type="event", record_id=event_id,
            metadata={"propagation": "derived_memories_withdrawn_intents_paused"},
        )

    def _add_intent_to_state(self, engine: PersonalMemoryEngine, intent: dict[str, Any], *, actor_ref: str) -> dict[str, Any]:
        if intent.get("subject_ref") != self.owner_ref:
            raise PermissionError("Intent subject_ref must match the personal owner.")
        required = {
            "intent_id", "subject_ref", "intent_type", "title", "status",
            "confirmation_status", "source_event_refs", "created_at", "updated_at",
            "classification", "sharing_policy", "ontology_version",
        }
        missing = sorted(required - set(intent))
        if missing:
            raise ValueError(f"Intent is missing required fields: {', '.join(missing)}")
        if not isinstance(intent.get("sharing_policy"), dict):
            raise ValueError("Intent sharing_policy must be an object.")
        if intent["sharing_policy"].get("default_scope") != "personal_only":
            raise PermissionError("Personal Intent must default to personal_only.")
        if intent["sharing_policy"].get("shareable") is True:
            raise PermissionError("Intent sharing requires a separate authorization workflow.")
        candidate_only = intent["confirmation_status"] == "inferred_candidate"
        if actor_ref != self.owner_ref and not (actor_ref in TRUSTED_AGENT_ACTORS and candidate_only):
            raise PermissionError("Only the owner can create confirmed Intent; the registered PDKS bridge may only add an inferred candidate.")
        if candidate_only and intent["status"] not in {"proposed", "paused"}:
            raise ValueError("An inferred candidate Intent cannot be active or completed.")
        source_refs = intent.get("source_event_refs", [])
        if not source_refs or len(source_refs) != len(set(source_refs)):
            raise ValueError("Intent must reference one or more unique source events.")
        event_ids = {x["event_id"] for x in engine.events}
        missing_sources = [x for x in source_refs if x not in event_ids]
        if missing_sources:
            raise KeyError(f"Intent references unknown source events: {missing_sources}")
        if any(x in engine.suppressed_sources for x in source_refs):
            raise PermissionError("Intent cannot be created from a suppressed source event.")
        intent_id = intent["intent_id"]
        if intent_id in engine.intents:
            if engine.intents[intent_id] == intent:
                return deepcopy(engine.intents[intent_id])
            raise ValueError("intent_id already exists with different content.")
        engine.intents[intent_id] = deepcopy(intent)
        return deepcopy(intent)

    def create_intent(self, intent: dict[str, Any], *, actor_ref: str) -> dict[str, Any]:
        return self._mutate(
            "create_intent", lambda e: self._add_intent_to_state(e, intent, actor_ref=actor_ref),
            actor_ref=actor_ref, record_type="intent", record_id=intent.get("intent_id"),
        )

    def import_memory(self, memory: dict[str, Any], *, actor_ref: str) -> dict[str, Any]:
        def apply(engine: PersonalMemoryEngine) -> dict[str, Any]:
            if memory.get("subject_ref") != self.owner_ref:
                raise PermissionError("Memory subject_ref must match the personal owner.")
            required = {"memory_id", "memory_type", "claim", "source_event_refs", "assertion_status", "confidence", "classification", "memory_lifecycle", "created_at", "updated_at", "derivation", "review_policy", "user_controls", "sharing_policy", "ontology_version"}
            missing = sorted(required - set(memory))
            if missing:
                raise ValueError(f"Memory is missing required fields: {', '.join(missing)}")
            if not isinstance(memory.get("claim"), dict) or not memory["claim"].get("statement"):
                raise ValueError("Memory claim.statement is required.")
            if not isinstance(memory.get("sharing_policy"), dict) or memory["sharing_policy"].get("default_scope") != "personal_only":
                raise PermissionError("Imported personal memory must default to personal_only.")
            if memory["sharing_policy"].get("shareable") is True:
                raise PermissionError("Memory sharing requires a separate authorization workflow.")
            source_refs = memory.get("source_event_refs", [])
            if not source_refs or len(source_refs) != len(set(source_refs)):
                raise ValueError("Memory must reference one or more unique source events.")
            event_ids = {x["event_id"] for x in engine.events}
            missing_sources = [x for x in source_refs if x not in event_ids]
            if missing_sources:
                raise KeyError(f"Memory references unknown source events: {missing_sources}")
            if any(x in engine.suppressed_sources for x in source_refs):
                raise PermissionError("Memory cannot be imported from a suppressed source event.")
            candidate_only = memory.get("assertion_status") == "candidate" or memory.get("memory_lifecycle") == "candidate"
            if actor_ref != self.owner_ref and not (actor_ref in TRUSTED_AGENT_ACTORS and candidate_only):
                raise PermissionError("Only the owner can import active memory; the registered PDKS bridge may only import candidates.")
            if memory.get("classification") == "personal_sensitive" and not memory.get("derivation", {}).get("human_review_required"):
                raise PermissionError("Sensitive memory must require human review.")
            memory_id = memory["memory_id"]
            if memory_id in engine.memories:
                if engine.memories[memory_id] == memory:
                    return deepcopy(engine.memories[memory_id])
                raise ValueError("memory_id already exists with different content.")
            engine.memories[memory_id] = deepcopy(memory)
            return deepcopy(memory)

        return self._mutate(
            "import_memory", apply, actor_ref=actor_ref, record_type="memory",
            record_id=memory.get("memory_id"),
        )

    def apply_pdks_projection(self, projection: dict[str, Any], *, actor_ref: str = "agent:pdks-ads-bridge") -> dict[str, int]:
        """Atomically persist a validated PDKS projection; never creates Agent Action Proposals."""
        if actor_ref != self.owner_ref and actor_ref not in TRUSTED_AGENT_ACTORS:
            raise PermissionError("Projection actor must be the owner or the registered PDKS bridge identity.")
        if projection.get("owner_ref") != self.owner_ref:
            raise PermissionError("Projection owner_ref does not match this personal vault.")
        if projection.get("mapping_version") != "ads-pdks-bridge@0.1.0":
            raise ValueError("Unsupported or missing PDKS-to-ADS mapping version.")
        if projection.get("enterprise_projection") is not None:
            raise PermissionError("Personal runtime cannot apply an enterprise projection.")
        validated_authorizations = set(projection.get("validated_authorization_refs", []))
        for event in projection.get("event_ledger", []):
            sharing = event.get("sharing_policy", {})
            if sharing.get("default_scope") != "personal_only" or sharing.get("projection_allowed") is not False:
                raise PermissionError("Projected personal events must remain personal_only and non-projectable by default.")
            for source in event.get("source_refs", []):
                if source.get("capture_mode") in {"connector_sync", "device_capture"}:
                    ref = source.get("capture_authorization_ref")
                    if not ref or ref not in validated_authorizations:
                        raise PermissionError("Projected connector/device source lacks a validated active authorization reference.")

        def apply(engine: PersonalMemoryEngine) -> dict[str, int]:
            counts = {"events": 0, "memories": 0, "intents": 0, "agent_actions": 0}
            for event in projection.get("event_ledger", []):
                before = len(engine.events)
                engine.append_event(event)
                counts["events"] += len(engine.events) - before
            for memory in projection.get("memory_items", []):
                before = len(engine.memories)
                # Apply the same safety rules as import_memory against the candidate state.
                if memory.get("subject_ref") != self.owner_ref:
                    raise PermissionError("Projected memory subject_ref does not match owner.")
                candidate_only = memory.get("assertion_status") == "candidate" and memory.get("memory_lifecycle") == "candidate"
                owner_confirmed = memory.get("assertion_status") == "confirmed" and memory.get("memory_lifecycle") == "active"
                if not candidate_only and not (actor_ref == self.owner_ref and owner_confirmed):
                    raise PermissionError("An agent may only import candidate memories; active memory requires an explicit owner-confirmed write.")
                if memory.get("classification") == "personal_sensitive" and not memory.get("derivation", {}).get("human_review_required"):
                    raise PermissionError("Sensitive projected memory must require human review.")
                refs = memory.get("source_event_refs", [])
                if not refs or any(ref not in {x["event_id"] for x in engine.events} for ref in refs):
                    raise KeyError("Projected memory must reference successfully stored events.")
                if any(ref in engine.suppressed_sources for ref in refs):
                    raise PermissionError("Projected memory references a suppressed event.")
                mid = memory["memory_id"]
                if mid in engine.memories:
                    if engine.memories[mid] != memory:
                        raise ValueError("Projected memory ID collision.")
                else:
                    engine.memories[mid] = deepcopy(memory)
                counts["memories"] += len(engine.memories) - before
            for intent in projection.get("intent_objects", []):
                before = len(engine.intents)
                self._add_intent_to_state(engine, intent, actor_ref=actor_ref)
                counts["intents"] += len(engine.intents) - before
            # Assertions, entities, source/evidence records remain in PDKS or are references only.
            # Agent Action Proposals must be created by the ADS planner, never by PDKS projection.
            if projection.get("agent_action_proposals"):
                raise PermissionError("PDKS projection cannot create Agent Action Proposals.")
            counts["agent_actions"] = 0
            return counts

        return self._mutate(
            "apply_pdks_projection", apply, actor_ref=actor_ref,
            metadata={"projection_contract": "ADS-PDKS-INT-001", "agent_action_proposals_created": 0},
        )

    def update_intent(self, intent_id: str, patch: dict[str, Any], *, actor_ref: str) -> dict[str, Any]:
        allowed = {"title", "description", "desired_outcome", "status", "priority", "progress", "due_at", "next_action", "review_at", "counterparty_refs", "dependency_refs"}
        if set(patch) - allowed:
            raise ValueError(f"Unsupported or protected Intent fields: {sorted(set(patch) - allowed)}")

        def apply(engine: PersonalMemoryEngine) -> dict[str, Any]:
            if actor_ref != self.owner_ref:
                raise PermissionError("Only the personal owner can update an Intent.")
            intent = engine.intents[intent_id]
            if intent.get("confirmation_status") == "inferred_candidate" and patch.get("status") == "active":
                raise ValueError("An inferred candidate Intent cannot be activated before owner confirmation.")
            if "status" in patch and patch["status"] not in {"proposed", "active", "paused", "blocked", "completed", "cancelled", "expired"}:
                raise ValueError("Unsupported Intent status.")
            intent.update(deepcopy(patch))
            intent["updated_at"] = _now()
            return deepcopy(intent)

        return self._mutate(
            "update_intent", apply, actor_ref=actor_ref, record_type="intent", record_id=intent_id,
        )

    def propose_action(self, action: dict[str, Any]) -> dict[str, Any]:
        def apply(engine: PersonalMemoryEngine) -> dict[str, Any]:
            task_ref = action.get("task_ref")
            if task_ref and task_ref not in engine.intents:
                raise KeyError(f"Agent Action Proposal references unknown Intent: {task_ref}")
            return engine.propose_action(action)

        return self._mutate(
            "propose_agent_action", apply, actor_ref=action.get("requested_by", "agent"),
            record_type="agent_action", record_id=action.get("proposal_id"),
        )

    def approve_action(self, proposal_id: str, *, actor_ref: str, approval_ref: str, plan_hash: str) -> dict[str, Any]:
        return self._mutate(
            "approve_agent_action",
            lambda e: e.approve_action(proposal_id, actor_ref=actor_ref, approval_ref=approval_ref, plan_hash=plan_hash),
            actor_ref=actor_ref, record_type="agent_action", record_id=proposal_id,
        )

    def mark_execution_result(self, proposal_id: str, *, result_status: str, verification_status: str) -> dict[str, Any]:
        return self._mutate(
            "record_action_result",
            lambda e: e.mark_execution_result(proposal_id, result_status=result_status, verification_status=verification_status),
            actor_ref="runtime:executor", record_type="agent_action", record_id=proposal_id,
        )

    def build_operating_context(
        self, *, purpose: str, include_candidates: bool = False, include_sensitive: bool = False,
    ) -> dict[str, Any]:
        context = self.build_context(
            purpose=purpose, include_candidates=include_candidates, include_sensitive=include_sensitive,
        )
        allowed_intent_statuses = {"active", "blocked", "paused"}
        if include_candidates:
            allowed_intent_statuses.add("proposed")
        intents = []
        for item in self.intents.values():
            if item.get("status") not in allowed_intent_statuses:
                continue
            if item.get("classification") == "personal_sensitive" and not include_sensitive:
                continue
            if item.get("confirmation_status") == "inferred_candidate" and not include_candidates:
                continue
            if any(ref in self.suppressed_sources for ref in item.get("source_event_refs", [])):
                continue
            intents.append({
                "intent_id": item["intent_id"], "intent_type": item["intent_type"],
                "title": item["title"], "status": item["status"],
                "confirmation_status": item["confirmation_status"],
                "due_at": item.get("due_at"), "source_event_refs": list(item["source_event_refs"]),
            })
        return {**context, "intents": intents, "store_revision": self._revision}

    def audit_log(self, *, limit: int = 100) -> list[dict[str, Any]]:
        return self.store.get_audit_log(self.owner_ref, limit=limit)

    def backup_to(self, destination: str | Path) -> Path:
        return self.store.backup_to(destination)

    def export_snapshot(self) -> dict[str, Any]:
        return {
            "format": "ADS-Personal-Memory-Snapshot",
            "format_version": "0.1.0",
            "owner_ref": self.owner_ref,
            "store_revision": self._revision,
            "exported_at": _now(),
            "state": self._snapshot(),
        }
