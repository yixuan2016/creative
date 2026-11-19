from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from ...models import parse_time, utc_now
from .catalog import DWS_EVENT_CATALOG, MINUTES_SUMMARY_EVENT_KEY
from .cli import DWSCLI


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _safe_segment(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._:-]+", "_", value)[:160] or "unknown"


def _source_type(event_key: str) -> str:
    if event_key.startswith("user_im_message_"):
        return "message"
    if event_key.startswith("user_minutes_"):
        return "note"
    if event_key == "user_calendar_event_changed":
        return "calendar_record"
    if event_key.startswith("user_oa_"):
        return "other"
    if event_key.startswith("user_todo_"):
        return "other"
    return "other"


def _stable_event_id(event_key: str, event: dict[str, Any]) -> str:
    # DWS explicitly documents biz_id as the stable idempotency key for the
    # calendar stream and minutes events. Other reviewed event families use
    # event_id when present. Fall back to a canonical payload hash.
    candidates = ["biz_id", "event_id", "task_id", "task_uuid", "message_id", "calendar_event_id", "id"]
    for key in candidates:
        value = event.get(key)
        if value not in (None, ""):
            return f"{key}:{value}"
    digest = hashlib.sha256(_canonical_json(event).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _occurred_at(event: dict[str, Any]) -> str | None:
    # Only pass through explicit ISO-8601 strings. DWS uses several millisecond
    # numeric timestamps; those remain preserved in the original event JSON.
    for key in ("event_time", "create_time", "operation_time", "read_time", "recall_time", "eventTime"):
        value = event.get(key)
        if isinstance(value, str) and parse_time(value):
            return value
    return None


class DWSConnector:
    """Maps DWS personal stream events into PDKS Source Assets.

    This adapter captures provider evidence only. It does not infer or approve
    PDKS Event/Task/Knowledge records; those remain an Agent + owner-review step.
    """

    source_kind = "dingtalk"
    capture_method = "system_sync"

    def __init__(
        self,
        runtime,
        owner_ref: str,
        consent_ref: str,
        profile: str,
        *,
        domain: str = "work",
        sensitivity: str = "personal_work",
        cli: DWSCLI | None = None,
    ):
        if not owner_ref or not consent_ref or not profile:
            raise ValueError("owner_ref, consent_ref and exact DWS profile are required")
        if domain != "work":
            raise ValueError("DWS connector 0.1.0 only maps DingTalk sources to the work domain")
        if sensitivity not in {"personal_work", "organization_internal", "restricted"}:
            raise ValueError("Unsupported DWS data sensitivity")
        self.runtime = runtime
        self.owner_ref = owner_ref
        self.consent_ref = consent_ref
        self.profile = profile
        self.domain = domain
        self.sensitivity = sensitivity
        self.cli = cli or DWSCLI(profile=profile)

    def validate_preflight(self, event_keys: list[str] | None = None) -> dict[str, Any]:
        """Validate local consent, DWS login snapshot, selected profile and event schemas."""
        self.runtime._check_consent(self.owner_ref, self.source_kind, self.domain, self.consent_ref)
        auth = self.cli.auth_status()
        # Fail closed: missing/ambiguous auth state is not equivalent to authenticated.
        if auth.get("authenticated") is not True:
            raise PermissionError("DWS authentication is not positively confirmed; run `dws auth login` and retry")
        if auth.get("reason") not in (None, ""):
            raise PermissionError("DWS auth status is indeterminate; resolve the reported local auth state before capture")
        if auth.get("local_state_requires_repair") is True:
            raise PermissionError("DWS local auth state requires repair; no event subscription was started")
        if auth.get("local_state_unreadable") is True:
            raise PermissionError("DWS local auth state is unreadable; no event subscription was started")
        if auth.get("token_valid") is False:
            raise PermissionError("DWS reports that the current token is invalid; sign in again before capture")

        actual_profile = auth.get("profile") or auth.get("currentProfile")
        if not actual_profile and auth.get("corpId") and auth.get("userId"):
            actual_profile = f"{auth['corpId']}:{auth['userId']}"
        if not isinstance(actual_profile, str) or not actual_profile:
            raise PermissionError("DWS did not positively identify the active profile; no event subscription was started")
        if actual_profile != self.profile:
            raise PermissionError(
                "DWS returned a different active profile than the explicitly selected PDKS profile"
            )
        schemas = {}
        for event_key in event_keys or []:
            schema = self.cli.event_schema(event_key)
            if not isinstance(schema, dict) or not schema:
                raise PermissionError(f"DWS event schema could not be verified for {event_key}")
            schemas[event_key] = schema
        return {
            "consent": "active",
            "authenticated": auth.get("authenticated"),
            "profile_verified": bool(actual_profile == self.profile) if actual_profile else False,
            "profile": self.profile,
            "event_schemas_checked": sorted(schemas),
            "note": "Profile selection is explicit; tenant-side event delivery still requires real event receipt validation.",
        }

    def ingest_event(self, event_key: str, event: dict[str, Any]) -> dict[str, Any]:
        if event_key not in DWS_EVENT_CATALOG:
            raise ValueError(f"Unsupported DWS event key: {event_key}")
        if not isinstance(event, dict):
            raise ValueError("DWS event must be a JSON object")
        identity = _stable_event_id(event_key, event)
        canonical = _canonical_json({
            "provider": "dingtalk-dws",
            "provider_event_key": event_key,
            "provider_profile": self.profile,
            "event": event,
        })
        locator = f"dws://{_safe_segment(self.profile)}/{event_key}/{_safe_segment(identity)}"
        idempotency = hashlib.sha256(
            f"{self.owner_ref}|{self.profile}|{event_key}|{identity}".encode("utf-8")
        ).hexdigest()
        return self.runtime.capture_text(
            self.owner_ref,
            canonical,
            source_kind="dingtalk",
            origin_system="dingtalk_dws_cli",
            source_locator=locator,
            domain=self.domain,
            sensitivity=self.sensitivity,
            capture_method="system_sync",
            consent_ref=self.consent_ref,
            occurred_at=_occurred_at(event),
            idempotency_key=f"dws:{idempotency}",
            actor_id="dws-connector",
            declared_source_type=_source_type(event_key),
        )

    def enrich_minutes_summary(self, task_uuid: str) -> dict[str, Any]:
        """Fetch meeting summary content only when explicitly requested by caller."""
        self.runtime._check_consent(self.owner_ref, self.source_kind, self.domain, self.consent_ref)
        summary = self.cli.minutes_summary(task_uuid)
        summary_hash = hashlib.sha256(_canonical_json(summary).encode("utf-8")).hexdigest()
        canonical = _canonical_json({
            "provider": "dingtalk-dws",
            "provider_event_key": MINUTES_SUMMARY_EVENT_KEY,
            "provider_profile": self.profile,
            "task_uuid": task_uuid,
            "summary": summary,
        })
        return self.runtime.capture_text(
            self.owner_ref,
            canonical,
            source_kind="dingtalk",
            origin_system="dingtalk_dws_cli",
            source_locator=f"dws://{_safe_segment(self.profile)}/minutes-summary/{_safe_segment(task_uuid)}/{summary_hash[:16]}",
            domain=self.domain,
            sensitivity=self.sensitivity,
            capture_method="system_sync",
            consent_ref=self.consent_ref,
            idempotency_key="dws:minutes-summary:" + hashlib.sha256(
                f"{self.owner_ref}|{self.profile}|{task_uuid}|{summary_hash}".encode("utf-8")
            ).hexdigest(),
            actor_id="dws-connector",
            declared_source_type="note",
        )
