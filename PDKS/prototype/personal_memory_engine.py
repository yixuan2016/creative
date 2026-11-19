"""Minimal reference engine for ADS-WORK-09 personal event and memory lifecycle."""
from __future__ import annotations
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PersonalMemoryEngine:
    def __init__(self, owner_ref: str):
        self.owner_ref = owner_ref
        self.events: list[dict[str, Any]] = []
        self.memories: dict[str, dict[str, Any]] = {}
        self.intents: dict[str, dict[str, Any]] = {}
        self.actions: dict[str, dict[str, Any]] = {}
        self.suppressed_sources: set[str] = set()

    def append_event(self, event: dict[str, Any]) -> dict[str, Any]:
        if event.get("subject_ref") != self.owner_ref:
            raise PermissionError("A personal ledger can only append events for its owner.")
        event_id = event.get("event_id")
        if not event_id:
            raise ValueError("event_id is required.")
        existing = next((x for x in self.events if x["event_id"] == event_id), None)
        if existing:
            if existing != event:
                raise ValueError("An event_id cannot be reused with different content.")
            return deepcopy(existing)
        idem = event.get("idempotency_key")
        if idem:
            existing_by_key = next((x for x in self.events if x.get("idempotency_key") == idem), None)
            if existing_by_key:
                if existing_by_key != event:
                    raise ValueError("An idempotency_key cannot be reused with different content.")
                return deepcopy(existing_by_key)
        self.events.append(deepcopy(event))
        return deepcopy(event)

    def derive_memory(self, event_id: str, memory_id: str, memory_type: str, statement: str, *, user_confirmed: bool = False, classification: str = "personal", confidence: float = 0.6) -> dict[str, Any]:
        event = next((x for x in self.events if x["event_id"] == event_id), None)
        if not event:
            raise KeyError(f"Unknown source event: {event_id}")
        if event_id in self.suppressed_sources or event.get("retention", {}).get("deletion_state") in {"suppressed", "deleted"}:
            raise PermissionError("A withdrawn or deleted source cannot recreate memory.")
        if memory_id in self.memories:
            raise ValueError("memory_id already exists.")
        now = _now()
        memory = {
            "memory_id": memory_id, "subject_ref": self.owner_ref, "memory_type": memory_type,
            "claim": {"statement": statement}, "source_event_refs": [event_id],
            "assertion_status": "confirmed" if user_confirmed else "candidate",
            "confidence": confidence, "classification": classification,
            "memory_lifecycle": "active" if user_confirmed else "candidate",
            "created_at": now, "updated_at": now,
            "derivation": {"method": "user_declared" if user_confirmed else "model_assisted", "algorithm_version": "0.1.0", "generated_at": now, "human_review_required": classification == "personal_sensitive" or not user_confirmed},
            "review_policy": {"update_policy": "user_confirmed" if user_confirmed else "periodic_review", "conflict_policy": "preserve_and_surface", "review_frequency_days": 30},
            "user_controls": {"can_confirm": True, "can_correct": True, "can_withdraw": True, "can_export": True},
            "sharing_policy": {"default_scope": "personal_only", "shareable": False, "authorized_purposes": [], "authorization_ref": None, "expires_at": None},
            "ontology_version": "ads.work-ontology@0.1.0",
        }
        self.memories[memory_id] = memory
        return deepcopy(memory)

    def confirm_memory(self, memory_id: str, *, actor_ref: str) -> dict[str, Any]:
        if actor_ref != self.owner_ref:
            raise PermissionError("Only the memory owner can confirm a personal memory.")
        memory = self.memories[memory_id]
        if memory["memory_lifecycle"] in {"withdrawn", "superseded", "expired"}:
            raise ValueError("This memory is not confirmable.")
        memory["assertion_status"] = "confirmed"
        memory["memory_lifecycle"] = "active"
        memory["updated_at"] = _now()
        memory["last_confirmed_at"] = memory["updated_at"]
        return deepcopy(memory)

    def correct_memory(self, old_memory_id: str, new_memory: dict[str, Any], *, actor_ref: str) -> dict[str, Any]:
        if actor_ref != self.owner_ref:
            raise PermissionError("Only the memory owner can correct a personal memory.")
        old = self.memories[old_memory_id]
        if new_memory["memory_id"] in self.memories:
            raise ValueError("The replacement memory_id already exists.")
        replacement = deepcopy(new_memory)
        replacement["supersedes"] = old_memory_id
        old["memory_lifecycle"] = "superseded"
        old["updated_at"] = _now()
        self.memories[replacement["memory_id"]] = replacement
        return deepcopy(replacement)

    def withdraw_memory(self, memory_id: str, *, actor_ref: str) -> None:
        if actor_ref != self.owner_ref:
            raise PermissionError("Only the memory owner can withdraw a personal memory.")
        memory = self.memories[memory_id]
        memory["memory_lifecycle"] = "withdrawn"
        memory["updated_at"] = _now()

    def forget_source_event(self, event_id: str, *, actor_ref: str) -> None:
        if actor_ref != self.owner_ref:
            raise PermissionError("Only the memory owner can request source forgetting.")
        if not any(x["event_id"] == event_id for x in self.events):
            raise KeyError(event_id)
        self.suppressed_sources.add(event_id)
        for memory in self.memories.values():
            if event_id in memory["source_event_refs"]:
                memory["memory_lifecycle"] = "withdrawn"
                memory["updated_at"] = _now()

    def build_context(self, *, purpose: str, include_candidates: bool = False, include_sensitive: bool = False) -> dict[str, Any]:
        allowed_statuses = {"active"}
        if include_candidates:
            allowed_statuses.add("candidate")
        selected = []
        for memory in self.memories.values():
            if memory["memory_lifecycle"] not in allowed_statuses:
                continue
            if memory["classification"] == "personal_sensitive" and not include_sensitive:
                continue
            if any(ref in self.suppressed_sources for ref in memory["source_event_refs"]):
                continue
            selected.append({"memory_id": memory["memory_id"], "memory_type": memory["memory_type"], "statement": memory["claim"]["statement"], "assertion_status": memory["assertion_status"], "confidence": memory["confidence"], "source_event_refs": list(memory["source_event_refs"])})
        return {"owner_ref": self.owner_ref, "purpose": purpose, "memories": selected}

    def propose_action(self, action: dict[str, Any]) -> dict[str, Any]:
        if action["subject_ref"] != self.owner_ref:
            raise PermissionError("The action proposal must belong to the personal owner.")
        if action["proposal_id"] in self.actions:
            raise ValueError("proposal_id already exists.")
        if action["risk_tier"] in {"L2", "L3"}:
            if not action["approval"]["required"] or action["approval"]["status"] != "pending":
                raise PermissionError("L2/L3 actions must wait for explicit user approval.")
        if action["execution"]["status"] != "not_started":
            raise ValueError("A new proposal must not already be executing.")
        self.actions[action["proposal_id"]] = deepcopy(action)
        return deepcopy(action)

    def approve_action(self, proposal_id: str, *, actor_ref: str, approval_ref: str, plan_hash: str) -> dict[str, Any]:
        if actor_ref != self.owner_ref:
            raise PermissionError("Only the personal owner can approve an action.")
        action = self.actions[proposal_id]
        if not action["approval"]["required"] or action["approval"]["status"] != "pending":
            raise ValueError("This action is not awaiting approval.")
        action["approval"].update({"status": "approved", "approved_by": actor_ref, "approved_at": _now(), "approval_ref": approval_ref, "approved_plan_hash": plan_hash})
        return deepcopy(action)

    def mark_execution_result(self, proposal_id: str, *, result_status: str, verification_status: str) -> dict[str, Any]:
        action = self.actions[proposal_id]
        if action["risk_tier"] in {"L2", "L3"} and action["approval"]["status"] != "approved":
            raise PermissionError("Execution is blocked until explicit approval is recorded.")
        if result_status not in {"succeeded", "failed", "cancelled", "partial"}:
            raise ValueError("Unsupported terminal execution status.")
        action["execution"]["status"] = result_status
        action["execution"]["finished_at"] = _now()
        action["execution"]["verification_status"] = verification_status
        return deepcopy(action)
