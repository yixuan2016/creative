from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from .errors import CapabilityUnavailableError, ConsentRequiredError

@dataclass
class SourceEnvelope:
    source_kind: str
    source_id: str
    locator: str
    payload: bytes
    filename: str
    capture_method: str
    consent_ref: str | None
    metadata: dict[str, Any]

class SourceAdapter(ABC):
    """Host-neutral adapter contract. Adapters never bypass the runtime policy engine."""
    source_kind: str
    capability_level: str

    @abstractmethod
    def discover(self, scope: dict[str, Any]) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def fetch(self, source_id: str, consent_ref: str) -> SourceEnvelope:
        raise NotImplementedError

class ManualUploadAdapter(SourceAdapter):
    source_kind = "manual"
    capability_level = "L0-L1"
    def discover(self, scope):
        return []
    def fetch(self, source_id, consent_ref=None):
        raise CapabilityUnavailableError("Manual uploads are pushed by the user; there is no remote fetch operation.")

class ConnectorAdapter(SourceAdapter):
    """Abstract contract for DingTalk/WeChat/email/calendar/cloud-doc adapters.

    No provider connector is implemented in Runtime 0.1.0. A future adapter must
    verify a trusted active consent grant before reading any source.
    """
    capability_level = "L2-L3"
    def __init__(self, source_kind: str, provider_client=None):
        self.source_kind=source_kind
        self.provider_client=provider_client
    def discover(self, scope):
        raise CapabilityUnavailableError(f"No {self.source_kind} connector is installed.")
    def fetch(self, source_id, consent_ref):
        if not consent_ref:
            raise ConsentRequiredError("Connector fetch requires a trusted consent reference.")
        raise CapabilityUnavailableError(f"No {self.source_kind} connector is installed.")

class DeviceCaptureAdapter(SourceAdapter):
    """Reserved adapter contract for microphone/camera/location/desktop/wearable sources."""
    capability_level = "L4"
    def __init__(self, source_kind: str):
        self.source_kind=source_kind
    def discover(self, scope):
        raise CapabilityUnavailableError(f"Device capture adapter '{self.source_kind}' is not implemented.")
    def fetch(self, source_id, consent_ref):
        if not consent_ref:
            raise ConsentRequiredError("Device capture requires explicit consent.")
        raise CapabilityUnavailableError(f"Device capture adapter '{self.source_kind}' is not implemented.")
