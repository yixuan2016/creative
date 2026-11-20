"""Minimal ADS work-context reference engine.

Python 3.10+, standard library only.
This is a local logic-validation prototype, not a production security boundary.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SEED = BASE_DIR.parent / "examples" / "project-delivery-seed-data.json"


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include a timezone offset")
    return parsed


def iso_time(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


class ContextEngine:
    REQUIRED_EVENT_FIELDS = (
        "event_id", "tenant_id", "event_type", "event_schema_version",
        "occurred_at", "observed_at", "recorded_at", "object_refs",
        "payload", "source_ref", "assertion_status", "classification",
        "purpose_tags", "ontology_version", "lifecycle_status",
    )

    def __init__(self, seed: dict[str, Any]) -> None:
        self.tenant_id = seed["tenant_id"]
        self.objects = {item["object_id"]: item for item in seed["objects"]}
        self.authority_rules = seed.get("authority_rules", {})
        self.grants = {item["grant_id"]: item for item in seed.get("grants", [])}
        self.known_unknowns = seed.get("known_unknowns", {})
        self.events: dict[str, dict[str, Any]] = {}
        self.idempotency_keys: set[str] = set()
        self.audit_log: list[dict[str, Any]] = []
        self.policy_version = seed.get("policy_version", "context-policy-0.1")
        self.ontology_version = seed.get("ontology_version", "ads-common-0.1")

    @staticmethod
    def idempotency_key(event: dict[str, Any]) -> str:
        source = event["source_ref"]
        return "|".join((
            event["tenant_id"],
            source["source_system"],
            source["native_record_id"],
            str(source.get("record_version", "")),
            event["event_type"],
        ))

    def ingest_event(self, event: dict[str, Any]) -> dict[str, str]:
        missing = [field for field in self.REQUIRED_EVENT_FIELDS if field not in event]
        if missing:
            raise ValueError("Missing required event fields: " + ", ".join(missing))
        if event["tenant_id"] != self.tenant_id:
            raise PermissionError("Tenant mismatch")
        for field in ("occurred_at", "observed_at", "recorded_at"):
            parse_time(event[field])
        if not isinstance(event["object_refs"], list) or not event["object_refs"]:
            raise ValueError("object_refs must be a non-empty list")
        unknown_objects = [oid for oid in event["object_refs"] if oid not in self.objects]
        if unknown_objects:
            raise ValueError("Unresolved object references: " + ", ".join(unknown_objects))
        if event["lifecycle_status"] != "active":
            return {"event_id": event["event_id"], "status": "ignored_inactive"}
        key = self.idempotency_key(event)
        if event["event_id"] in self.events or key in self.idempotency_keys:
            return {"event_id": event["event_id"], "status": "duplicate"}
        self.events[event["event_id"]] = event
        self.idempotency_keys.add(key)
        return {"event_id": event["event_id"], "status": "accepted"}

    def ingest_many(self, events: list[dict[str, Any]]) -> list[dict[str, str]]:
        return [self.ingest_event(event) for event in events]

    def _visible_events(
        self,
        object_id: str,
        property_name: str,
        allowed_classifications: set[str],
    ) -> list[dict[str, Any]]:
        owner_type = property_name.split(".", 1)[0] if "." in property_name else None
        return [
            event for event in self.events.values()
            if object_id in event["object_refs"]
            and event["payload"].get("property") == property_name
            and (owner_type is None or self.objects[object_id]["object_type"] == owner_type)
            and event["classification"] in allowed_classifications
            and event["lifecycle_status"] == "active"
        ]

    def current_state(
        self,
        object_id: str,
        property_name: str,
        allowed_classifications: set[str],
    ) -> dict[str, Any]:
        candidates = self._visible_events(object_id, property_name, allowed_classifications)
        authority = self.authority_rules.get(property_name)
        authoritative = [
            event for event in candidates
            if event["source_ref"]["source_system"] == authority
        ]
        sort_key = lambda event: (
            parse_time(event["occurred_at"]),
            str(event["source_ref"].get("record_version", "")),
        )

        if authoritative:
            winner = max(authoritative, key=sort_key)
            value = winner["payload"].get("new_value")
            status = "confirmed"
            authority_source = authority
            supporting = [winner["event_id"]]
            other_candidates = [
                event for event in candidates
                if event["event_id"] != winner["event_id"]
                and event["source_ref"]["source_system"] != authority
            ]
        elif candidates:
            winner = max(candidates, key=sort_key)
            value = winner["payload"].get("new_value")
            status = winner["assertion_status"]
            authority_source = None
            supporting = [winner["event_id"]]
            other_candidates = [event for event in candidates if event["event_id"] != winner["event_id"]]
        else:
            return {
                "object_id": object_id,
                "property": property_name,
                "value": None,
                "assertion_status": "unknown",
                "authority_source": authority,
                "supporting_refs": [],
                "conflicts": [],
                "unknowns": ["No eligible source event found"],
                "evaluated_at": iso_time(datetime.now(timezone.utc)),
                "rule_version": "state-rules-0.1",
            }

        conflicts = []
        for event in other_candidates:
            candidate_value = event["payload"].get("new_value")
            if candidate_value != value:
                conflicts.append({
                    "event_id": event["event_id"],
                    "source_system": event["source_ref"]["source_system"],
                    "value": candidate_value,
                    "assertion_status": event["assertion_status"],
                })

        return {
            "object_id": object_id,
            "property": property_name,
            "value": value,
            "assertion_status": status,
            "authority_source": authority_source,
            "supporting_refs": supporting,
            "conflicts": conflicts,
            "unknowns": [],
            "evaluated_at": iso_time(datetime.now(timezone.utc)),
            "rule_version": "state-rules-0.1",
        }

    def _find_grant(self, requester: str, tenant_id: str, purpose: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        for grant in self.grants.values():
            if (
                grant["subject_ref"] == requester
                and grant["tenant_id"] == tenant_id
                and purpose in grant["purposes"]
                and grant["status"] == "active"
                and parse_time(grant["expires_at"]) > now
            ):
                return grant
        raise PermissionError("POLICY_DENIED: no active grant for requester and purpose")

    def build_context(self, request: dict[str, Any]) -> dict[str, Any]:
        requester = request["requester_ref"]
        tenant_id = request["tenant_id"]
        purpose = request["purpose"]
        object_ids = request["object_ids"]
        if tenant_id != self.tenant_id:
            raise PermissionError("POLICY_DENIED: tenant mismatch")

        grant = self._find_grant(requester, tenant_id, purpose)
        allowed_scope = set(grant["scope_object_ids"])
        requested_scope = set(object_ids)
        if not requested_scope or not requested_scope.issubset(allowed_scope):
            raise PermissionError("POLICY_DENIED: requested object is outside grant scope")

        allowed_classes = set(grant["allowed_classifications"])
        window = request.get("time_window", {})
        start = parse_time(window["from"]) if window.get("from") else None
        end = parse_time(window["to"]) if window.get("to") else None

        timeline = []
        for event in self.events.values():
            if not requested_scope.intersection(event["object_refs"]):
                continue
            if event["classification"] not in allowed_classes or event["lifecycle_status"] != "active":
                continue
            occurred = parse_time(event["occurred_at"])
            if start and occurred < start:
                continue
            if end and occurred > end:
                continue
            timeline.append(event)
        timeline.sort(key=lambda event: parse_time(event["occurred_at"]))

        properties_by_object: dict[str, set[str]] = {}
        for event in self.events.values():
            if (
                requested_scope.intersection(event["object_refs"])
                and event["classification"] in allowed_classes
                and event["lifecycle_status"] == "active"
            ):
                property_name = event["payload"].get("property")
                if property_name:
                    owner_type = property_name.split(".", 1)[0] if "." in property_name else None
                    for object_id in requested_scope.intersection(event["object_refs"]):
                        if owner_type is None or self.objects[object_id]["object_type"] == owner_type:
                            properties_by_object.setdefault(object_id, set()).add(property_name)

        states = []
        unresolved = []
        state_support_ids: set[str] = set()
        for object_id, properties in properties_by_object.items():
            for property_name in sorted(properties):
                state = self.current_state(object_id, property_name, allowed_classes)
                states.append(state)
                state_support_ids.update(state["supporting_refs"])
                for conflict in state["conflicts"]:
                    unresolved.append({
                        "type": "state_conflict",
                        "object_id": object_id,
                        "property": property_name,
                        "event_id": conflict["event_id"],
                        "source_system": conflict["source_system"],
                    })
                for unknown in state["unknowns"]:
                    unresolved.append({
                        "type": "unknown",
                        "object_id": object_id,
                        "property": property_name,
                        "description": unknown,
                    })

        for object_id in requested_scope:
            for unknown in self.known_unknowns.get(object_id, []):
                unresolved.append({
                    "type": "business_unknown",
                    "object_id": object_id,
                    "description": unknown,
                })

        event_ids = sorted(
            {event["event_id"] for event in timeline}.union(state_support_ids)
        )
        now = datetime.now(timezone.utc)
        expires = min(now + timedelta(minutes=30), parse_time(grant["expires_at"]))
        context_id = "ctx-" + now.strftime("%Y%m%dT%H%M%S%fZ")

        context = {
            "context_id": context_id,
            "task_id": request["task_id"],
            "requester_ref": requester,
            "purpose": purpose,
            "scope": {
                "object_ids": sorted(requested_scope),
                "time_window": window,
            },
            "objects": [self.objects[oid] for oid in sorted(requested_scope)],
            "current_states": states,
            "timeline": timeline,
            "included_refs": {
                "object_ids": sorted(requested_scope),
                "event_ids": event_ids,
            },
            "unresolved_items": unresolved,
            "allowed_actions": grant["allowed_actions"],
            "approval_required_for": [
                "update_project_status",
                "reassign_task",
                "approve_decision",
                "send_customer_commitment",
            ],
            "authorization_refs": [grant["grant_id"]],
            "policy_version": grant.get("policy_version", self.policy_version),
            "ontology_version": self.ontology_version,
            "created_at": iso_time(now),
            "expires_at": iso_time(expires),
            "lifecycle_status": "active",
        }
        self.audit_log.append({
            "action": "context.build",
            "context_id": context_id,
            "requester_ref": requester,
            "purpose": purpose,
            "object_ids": sorted(requested_scope),
            "event_count": len(event_ids),
            "policy_version": context["policy_version"],
            "created_at": context["created_at"],
        })
        return context


def load_seed(path: Path = DEFAULT_SEED) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def run_demo() -> dict[str, Any]:
    seed = load_seed()
    engine = ContextEngine(seed)
    ingest_results = engine.ingest_many(seed["events"])
    duplicate_result = engine.ingest_event(seed["events"][0])
    context = engine.build_context(seed["context_request"])
    return {
        "ingest_results": ingest_results,
        "duplicate_demo": duplicate_result,
        "context_package": context,
        "audit_log": engine.audit_log,
    }


if __name__ == "__main__":
    print(json.dumps(run_demo(), ensure_ascii=False, indent=2))
