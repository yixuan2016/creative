"""Conservative PDKS 0.1 -> ADS-WORK-09 projection adapter.

The adapter projects only personal events, candidate memories and candidate Intents.
It never creates enterprise events or Personal Agent Action Proposals. Connector/device
capture requires an authorization reference supplied by a trusted authorization resolver.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

MAPPING_VERSION = "ads-pdks-bridge@0.1.0"
ADS_ONTOLOGY_VERSION = "ads.work-ontology@0.1.0"


class ProjectionBlocked(PermissionError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _stable_id(prefix: str, source_id: str) -> str:
    digest = hashlib.sha256(source_id.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}-{digest}"


def _parse_datetime(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ProjectionBlocked("missing_time", f"{field} is required for PDKS -> ADS projection.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProjectionBlocked("invalid_time", f"{field} is not a valid ISO date-time.") from exc
    if parsed.tzinfo is None:
        raise ProjectionBlocked("timezone_missing", f"{field} must include an explicit UTC offset.")
    return parsed


def _timezone_label(value: str, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    dt = _parse_datetime(value, "occurred_at")
    offset = dt.utcoffset()
    if offset is None or offset.total_seconds() == 0:
        return "UTC"
    minutes = int(offset.total_seconds() // 60)
    sign = "+" if minutes >= 0 else "-"
    minutes = abs(minutes)
    return f"UTC{sign}{minutes // 60:02d}:{minutes % 60:02d}"


def _classification(record: dict[str, Any]) -> str:
    value = record.get("governance", {}).get("sensitivity", "personal_work")
    mapping = {
        "personal_private": "personal_sensitive",
        "personal_work": "personal",
        "organization_internal": "restricted",
        "restricted": "restricted",
        "public": "personal",
    }
    return mapping.get(value, "restricted")


def _capture_mode(source: dict[str, Any], valid_authorization_refs: set[str]) -> tuple[str, str, str | None]:
    payload = source.get("payload", {})
    method = payload.get("capture_method")
    mapping = {
        "manual_upload": ("manual_import", "import"),
        "api_import": ("manual_import", "import"),
        "system_sync": ("connector_sync", "connector"),
        "device_capture": ("device_capture", "device"),
        "automatic": ("connector_sync", "connector"),
    }
    if method not in mapping:
        raise ProjectionBlocked("unsupported_capture_mode", f"Unsupported PDKS capture_method: {method!r}.")
    capture_mode, capture_method = mapping[method]
    consent_ref = source.get("governance", {}).get("consent_ref")
    if capture_mode in {"connector_sync", "device_capture"}:
        if not consent_ref:
            raise ProjectionBlocked("consent_missing", f"{method} requires governance.consent_ref.")
        if consent_ref not in valid_authorization_refs:
            raise ProjectionBlocked("consent_not_validated", "The consent reference is not present in the trusted active-authorization set.")
    return capture_mode, capture_method, consent_ref


def _resolve_source_records(event: dict[str, Any], index: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    refs = list(event.get("provenance", {}).get("source_refs", []))
    if not refs:
        for evidence_ref in event.get("payload", {}).get("evidence_refs", []):
            evidence = index.get(evidence_ref)
            if evidence and evidence.get("object_type") == "evidence_segment":
                source_ref = evidence.get("payload", {}).get("source_ref")
                if source_ref and source_ref not in refs:
                    refs.append(source_ref)
    if not refs:
        raise ProjectionBlocked("source_missing", "Event has no resolvable PDKS Source Asset reference.")
    sources = []
    for ref in refs:
        source = index.get(ref)
        if not source or source.get("object_type") != "source_asset":
            raise ProjectionBlocked("source_unresolved", f"Source Asset reference cannot be resolved: {ref}")
        sources.append(source)
    return sources


def project_event(
    event: dict[str, Any],
    records_by_id: dict[str, dict[str, Any]],
    *,
    owner_ref: str,
    valid_authorization_refs: Iterable[str] = (),
) -> tuple[dict[str, Any], list[str]]:
    """Project one PDKS Event into ADS Personal Event Ledger; return record and warnings."""
    if event.get("object_type") != "event":
        raise ValueError("project_event expects a PDKS event record")
    if event.get("owner_ref") != owner_ref:
        raise ProjectionBlocked("owner_mismatch", "PDKS event owner_ref does not match the target personal owner.")
    if event.get("lifecycle", {}).get("status", "active") != "active":
        raise ProjectionBlocked("event_not_active", "Only active PDKS events can be projected.")

    payload = event.get("payload", {})
    occurred = payload.get("start_at")
    occurred_dt = _parse_datetime(occurred, "payload.start_at")
    recorded_at = event.get("created_at")
    _parse_datetime(recorded_at, "created_at")

    source_records = _resolve_source_records(event, records_by_id)
    valid_auth = set(valid_authorization_refs)
    source_refs = []
    processing_capture_methods = []
    warnings = []
    for source in source_records:
        source_payload = source.get("payload", {})
        capture_mode, processing_capture_method, consent_ref = _capture_mode(source, valid_auth)
        processing_capture_methods.append(processing_capture_method)
        captured_at = source_payload.get("captured_at")
        if captured_at:
            _parse_datetime(captured_at, "source_asset.payload.captured_at")
        else:
            captured_at = recorded_at
            warnings.append(f"{source.get('object_id')}: captured_at missing; used PDKS created_at as observed_at.")
        content_hash = source_payload.get("content_hash")
        if isinstance(content_hash, dict):
            content_hash = content_hash.get("value")
        source_ref = {
            "source_system": source_payload.get("origin_system", "pdks-import"),
            "native_record_id": source_payload.get("native_record_id") or source.get("object_id"),
            "capture_mode": capture_mode,
            "capture_authorization_ref": consent_ref,
            "content_ref": source_payload.get("source_locator", source.get("object_id")),
        }
        if content_hash:
            source_ref["content_hash"] = content_hash
        version = source.get("lifecycle", {}).get("version")
        if version is not None:
            source_ref["record_version"] = str(version)
        source_refs.append(source_ref)

    event_type = payload.get("event_type")
    if not isinstance(event_type, str) or len(event_type.split(".")) < 2:
        raise ProjectionBlocked("event_type_invalid", "PDKS event_type must contain a domain and subtype.")
    parts = event_type.split(".")
    domain = parts[0]
    subtype = "_".join(parts[1:])
    ads_event_type = f"personal.{domain}.{subtype}"

    actor_refs = []
    for participant in payload.get("participants", []):
        entity_ref = participant.get("entity_ref")
        entity = records_by_id.get(entity_ref, {})
        entity_type = entity.get("payload", {}).get("entity_type")
        identity_status = participant.get("identity_status")
        if identity_status != "confirmed":
            actor_type = "unknown"
        else:
            actor_type = entity_type if entity_type in {"person", "role", "agent", "system"} else "unknown"
        if entity_ref:
            actor_refs.append({"actor_type": actor_type, "actor_id": entity_ref})

    observed_at = source_records[0].get("payload", {}).get("captured_at") or recorded_at
    observed_dt = _parse_datetime(observed_at, "observed_at")
    explicit_timezone = payload.get("timezone")
    timezone_label = _timezone_label(occurred, explicit_timezone)

    classification = _classification(event)
    status = payload.get("assertion_status", "observed")
    if status not in {"confirmed", "observed", "inferred", "disputed", "rejected", "unknown"}:
        status = "observed"
        warnings.append("Unsupported assertion_status was normalized to observed.")

    projected = {
        "event_id": _stable_id("pevt-pdks", event["object_id"]),
        "subject_ref": owner_ref,
        "event_type": ads_event_type,
        "event_schema_version": "0.1.0",
        "occurred_at": occurred_dt.isoformat(),
        "observed_at": observed_dt.isoformat(),
        "recorded_at": _parse_datetime(recorded_at, "created_at").isoformat(),
        "timezone": timezone_label,
        "actor_refs": actor_refs,
        "object_refs": list(payload.get("context_refs", [])),
        "payload": {
            "summary": payload.get("title") or payload.get("description") or event["object_id"],
            "description": payload.get("description"),
            "pdks_event_type": event_type,
            "pdks_event_taxonomy_version": payload.get("event_taxonomy_version"),
            "pdks_record_ref": event["object_id"],
            "start_at": payload.get("start_at"),
            "end_at": payload.get("end_at"),
        },
        "source_refs": source_refs,
        "evidence_refs": list(payload.get("evidence_refs", [])),
        "assertion_status": status,
        "classification": classification,
        "purpose_tags": sorted(set(event.get("domains", []) + ["pdks_projection"])),
        "ontology_version": ADS_ONTOLOGY_VERSION,
        "processing_provenance": {
            "capture_method": processing_capture_methods[0],
            "extraction_method": "model_assisted",
            "extractor_version": MAPPING_VERSION,
            "human_reviewed": bool(payload.get("human_reviewed", False)),
        },
        "sharing_policy": {
            "default_scope": "personal_only",
            "projection_allowed": False,
            "authorized_purposes": [],
            "authorization_ref": None,
            "expires_at": None,
        },
        "retention": {
            "policy_ref": "personal-default-v0.1",
            "retain_until": None,
            "deletion_state": "active",
        },
        "lifecycle_status": "active",
        "idempotency_key": f"pdks:{event['object_id']}:v{event.get('lifecycle', {}).get('version', 1)}",
        "extensions": {
            "pdks_record_ref": event["object_id"],
            "pdks_standard_version": event.get("pdks_version", "0.1.0"),
            "pdks_domains": event.get("domains", []),
            "event_time_precision": payload.get("time_precision"),
            "source_record_refs": [x.get("object_id") for x in source_records],
        },
    }
    return projected, warnings


def _map_confidence(value: Any) -> float:
    if isinstance(value, (int, float)) and 0 <= value <= 1:
        return float(value)
    return {"high": 0.85, "medium": 0.60, "low": 0.35}.get(value, 0.50)


def project_memory(
    record: dict[str, Any],
    *,
    owner_ref: str,
    event_id_map: dict[str, str],
) -> dict[str, Any]:
    record_type = record.get("object_type")
    if record_type not in {"knowledge_asset", "personal_context"}:
        raise ValueError("project_memory expects knowledge_asset or personal_context")
    payload = record.get("payload", {})
    if record_type == "personal_context" and payload.get("subject_ref") != owner_ref:
        raise ProjectionBlocked("owner_mismatch", "Personal Context subject_ref does not match the personal owner.")

    candidate_refs = []
    for key in ("derived_from_refs", "evidence_refs", "source_refs"):
        for ref in payload.get(key, []):
            if ref in event_id_map and event_id_map[ref] not in candidate_refs:
                candidate_refs.append(event_id_map[ref])
    if not candidate_refs:
        raise ProjectionBlocked("source_event_missing", "Memory candidate has no successfully projected source Event.")

    if record_type == "knowledge_asset":
        kind = payload.get("knowledge_type")
        memory_type = {
            "method": "procedural", "procedure": "procedural",
            "experience": "episodic", "case": "episodic",
            "concept": "semantic", "fact": "semantic", "principle": "semantic",
            "lesson": "semantic", "insight": "semantic",
        }.get(kind, "semantic")
        statement = payload.get("summary") or payload.get("content") or payload.get("title")
        verification = payload.get("verification_status", "draft")
    else:
        kind = payload.get("context_type")
        memory_type = {
            "role": "semantic", "capability": "semantic", "responsibility": "semantic",
            "constraint": "semantic", "working_style": "semantic", "goal": "goal",
            "preference": "preference", "relationship": "relationship",
            "current_focus": "project_context",
        }.get(kind, "semantic")
        statement = payload.get("value")
        verification = payload.get("verification_status", "inferred")

    if not statement:
        raise ProjectionBlocked("memory_statement_missing", "Knowledge/Context statement is empty.")
    confirmed = verification in {"confirmed", "corroborated", "verified"}
    lifecycle = record.get("lifecycle", {}).get("status", "active")
    if lifecycle != "active":
        raise ProjectionBlocked("memory_not_active", "Only active PDKS knowledge/context records can be projected.")
    classification = _classification(record)
    created_at = record.get("created_at")
    updated_at = record.get("updated_at") or created_at
    _parse_datetime(created_at, "created_at")
    _parse_datetime(updated_at, "updated_at")
    confidence = _map_confidence(payload.get("confidence_level", payload.get("confidence")))
    evidence_refs = list(payload.get("evidence_refs", []))
    if record_type == "knowledge_asset":
        evidence_refs.extend(x for x in payload.get("derived_from_refs", []) if x not in evidence_refs and x not in event_id_map)

    memory = {
        "memory_id": _stable_id("pmem-pdks", record["object_id"]),
        "subject_ref": owner_ref,
        "memory_type": memory_type,
        "claim": {"statement": statement},
        "source_event_refs": candidate_refs,
        "evidence_refs": evidence_refs,
        "assertion_status": "confirmed" if confirmed else "candidate",
        "confidence": confidence,
        "classification": classification,
        "memory_lifecycle": "active" if confirmed else "candidate",
        "created_at": _parse_datetime(created_at, "created_at").isoformat(),
        "updated_at": _parse_datetime(updated_at, "updated_at").isoformat(),
        "derivation": {
            "method": "human_curated" if confirmed else "model_assisted",
            "algorithm_version": MAPPING_VERSION,
            "generated_at": _parse_datetime(updated_at, "updated_at").isoformat(),
            "human_review_required": classification == "personal_sensitive" or not confirmed,
        },
        "review_policy": {
            "update_policy": "user_confirmed" if confirmed else "periodic_review",
            "conflict_policy": "preserve_and_surface",
            "review_frequency_days": 30,
        },
        "user_controls": {
            "can_confirm": True, "can_correct": True, "can_withdraw": True, "can_export": True,
        },
        "sharing_policy": {
            "default_scope": "personal_only", "shareable": False,
            "authorized_purposes": [], "authorization_ref": None, "expires_at": None,
        },
        "ontology_version": ADS_ONTOLOGY_VERSION,
        "extensions": {
            "pdks_record_ref": record["object_id"],
            "pdks_object_type": record_type,
            "pdks_subtype": kind,
            "pdks_verification_status": verification,
            "pdks_confidence_level": payload.get("confidence_level"),
        },
    }
    if confirmed:
        memory["last_confirmed_at"] = memory["updated_at"]
    return memory


def project_action_to_intent(
    action: dict[str, Any],
    *,
    owner_ref: str,
    event_id_map: dict[str, str],
) -> dict[str, Any]:
    if action.get("object_type") != "action":
        raise ValueError("project_action_to_intent expects a PDKS action record")
    if action.get("owner_ref") != owner_ref:
        raise ProjectionBlocked("owner_mismatch", "PDKS Action owner_ref does not match the personal owner.")
    payload = action.get("payload", {})
    assignee = payload.get("assignee_ref")
    if assignee and assignee != owner_ref:
        raise ProjectionBlocked("assignee_mismatch", "An Action assigned to someone else cannot become this owner's personal Intent.")
    source_events = list(dict.fromkeys(event_id_map[x] for x in payload.get("created_from_refs", []) if x in event_id_map))
    if not source_events:
        raise ProjectionBlocked("source_event_missing", "PDKS Action has no successfully projected source Event.")
    created_at = action.get("created_at")
    updated_at = action.get("updated_at") or created_at
    _parse_datetime(created_at, "created_at")
    _parse_datetime(updated_at, "updated_at")

    owner_confirmed = payload.get("owner_confirmed") is True or payload.get("confirmation_status") == "user_confirmed"
    original_status = payload.get("status", "open")
    status_map = {
        "open": "proposed", "pending": "proposed", "todo": "proposed",
        "in_progress": "active", "active": "active", "blocked": "blocked",
        "done": "completed", "completed": "completed", "cancelled": "cancelled", "expired": "expired",
    }
    status = status_map.get(original_status, "proposed") if owner_confirmed else "proposed"
    action_type = payload.get("action_type", "task")
    intent_type = action_type if action_type in {"goal", "commitment", "task", "routine", "project"} else "task"
    priority = payload.get("priority")
    if priority not in {"low", "normal", "high", "critical"}:
        priority = "normal"

    intent = {
        "intent_id": _stable_id("pintent-pdks", action["object_id"]),
        "subject_ref": owner_ref,
        "intent_type": intent_type,
        "title": payload.get("title") or "未命名个人行动",
        "description": payload.get("description", ""),
        "status": status,
        "confirmation_status": "user_confirmed" if owner_confirmed else "inferred_candidate",
        "owner_ref": owner_ref,
        "counterparty_refs": list(payload.get("counterparty_refs", [])),
        "start_at": payload.get("start_at"),
        "due_at": payload.get("due_at"),
        "priority": priority,
        "source_event_refs": source_events,
        "external_refs": [{"system": "pdks", "native_id": action["object_id"]}],
        "created_at": _parse_datetime(created_at, "created_at").isoformat(),
        "updated_at": _parse_datetime(updated_at, "updated_at").isoformat(),
        "classification": _classification(action),
        "sharing_policy": {"default_scope": "personal_only", "shareable": False, "authorization_ref": None},
        "ontology_version": ADS_ONTOLOGY_VERSION,
        "extensions": {
            "pdks_record_ref": action["object_id"],
            "pdks_action_type": action_type,
            "pdks_original_status": original_status,
            "owner_confirmation_required": not owner_confirmed,
        },
    }
    return intent


def validate_pdks_records(
    records: list[dict[str, Any]],
    *,
    schema_path: str | Path,
    taxonomy_path: str | Path,
) -> None:
    """Validate source records against the pinned PDKS JSON Schema and event taxonomy."""
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError as exc:
        raise RuntimeError("PDKS source validation requires jsonschema; install requirements-dev.txt") from exc
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    taxonomy = json.loads(Path(taxonomy_path).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = []
    for record in records:
        for error in validator.iter_errors(record):
            location = ".".join(str(x) for x in error.absolute_path) or "<root>"
            errors.append(f"{record.get('object_id', '<unknown>')}:{location}: {error.message}")
    codes = {
        event["code"]
        for domain in taxonomy.get("domains", [])
        for event in domain.get("events", [])
    }
    for record in records:
        if record.get("object_type") == "event":
            code = record.get("payload", {}).get("event_type")
            if code not in codes:
                errors.append(f"{record.get('object_id', '<unknown>')}: event_type is not in the pinned taxonomy: {code}")
    if errors:
        raise ProjectionBlocked("pdks_validation_failed", "PDKS source validation failed: " + " | ".join(errors[:12]))


def project_bundle(
    records: Iterable[dict[str, Any]],
    *,
    owner_ref: str,
    valid_authorization_refs: Iterable[str] = (),
    schema_path: str | Path | None = None,
    taxonomy_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build a conservative ADS-WORK-09 projection from a collection of PDKS records."""
    record_list = list(records)
    if (schema_path is None) != (taxonomy_path is None):
        raise ValueError("schema_path and taxonomy_path must be supplied together.")
    if schema_path is not None and taxonomy_path is not None:
        validate_pdks_records(record_list, schema_path=schema_path, taxonomy_path=taxonomy_path)
    index = {x["object_id"]: x for x in record_list if x.get("object_id")}
    event_ledger = []
    memory_items = []
    intent_objects = []
    preserved_only = []
    blocked = []
    warnings = []
    event_id_map: dict[str, str] = {}

    for record in record_list:
        if record.get("object_type") != "event":
            continue
        try:
            projected, notes = project_event(
                record, index, owner_ref=owner_ref,
                valid_authorization_refs=valid_authorization_refs,
            )
            event_ledger.append(projected)
            event_id_map[record["object_id"]] = projected["event_id"]
            warnings.extend(notes)
        except ProjectionBlocked as exc:
            blocked.append({"object_id": record.get("object_id"), "object_type": "event", "code": exc.code, "reason": str(exc)})

    for record in record_list:
        kind = record.get("object_type")
        if kind in {"knowledge_asset", "personal_context"}:
            try:
                memory_items.append(project_memory(record, owner_ref=owner_ref, event_id_map=event_id_map))
            except ProjectionBlocked as exc:
                blocked.append({"object_id": record.get("object_id"), "object_type": kind, "code": exc.code, "reason": str(exc)})
        elif kind == "action":
            try:
                intent_objects.append(project_action_to_intent(record, owner_ref=owner_ref, event_id_map=event_id_map))
            except ProjectionBlocked as exc:
                blocked.append({"object_id": record.get("object_id"), "object_type": kind, "code": exc.code, "reason": str(exc)})
        elif kind in {"assertion", "entity", "source_asset", "evidence_segment", "relationship"}:
            preserved_only.append({"object_id": record.get("object_id"), "object_type": kind, "reason": "No direct ADS-WORK-09 record equivalent; retain in PDKS and reference as needed."})

    return {
        "mapping_version": MAPPING_VERSION,
        "owner_ref": owner_ref,
        "validated_authorization_refs": sorted(set(valid_authorization_refs)),
        "event_ledger": event_ledger,
        "memory_items": memory_items,
        "intent_objects": intent_objects,
        "agent_action_proposals": [],
        "enterprise_projection": None,
        "preserved_only": preserved_only,
        "blocked": blocked,
        "warnings": warnings,
        "event_id_map": event_id_map,
    }
