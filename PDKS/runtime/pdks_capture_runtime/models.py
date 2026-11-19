from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import json

SOURCE_KINDS = {
    "manual", "dingtalk", "wechat", "wecom", "slack", "email", "calendar",
    "cloud_docs", "browser", "task_system", "crm", "erp", "microphone",
    "desktop_activity", "camera", "location", "wearable", "health",
    "finance", "other"
}
CAPTURE_METHODS = {"manual_upload", "device_capture", "system_sync", "api_import"}
SENSITIVITY = {"personal_private", "personal_work", "organization_internal", "restricted", "public"}
DOMAINS = {"work", "learning", "thinking", "life", "relationship", "growth", "finance", "health", "other"}
CONSENT_REQUIRED_METHODS = {"device_capture", "system_sync", "api_import"}
API_SCOPES = {
    "capture:read", "capture:write", "records:read", "records:propose",
    "records:approve", "consent:manage", "data:export", "data:delete"
}

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None

def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def loads(value: str | None, default=None):
    if value is None:
        return default
    return json.loads(value)

@dataclass(frozen=True)
class Principal:
    owner_ref: str
    agent_id: str
    scopes: frozenset[str]

@dataclass
class ExtractionResult:
    text: str | None
    status: str
    media_type: str
    warnings: list[str]
