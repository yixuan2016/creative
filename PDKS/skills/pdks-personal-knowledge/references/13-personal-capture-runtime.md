# Personal Capture Runtime — Transitional Integration Contract

## Stage boundary

PDKS 0.5.0 introduces a local reference implementation of a Personal Capture Runtime. It remains experimental and does not turn the Skill into a production personal digital foundation platform or Personal Assistant OS.

- Skill 0.3.4 remains portable instructions and semantic contracts.
- Runtime 0.1.0 is a separate local software prototype.
- PDKS standard 0.1.0, record schema 0.1.x, Ontology 0.2.1 and Event Taxonomy 0.1.0 remain unchanged.
- The reference API binds to loopback only. Remote multi-device/cloud access, production auth, encryption, provider connectors and background device capture are not implemented.

## Core rule

Agents must use a Runtime adapter/API when one is explicitly available. Agents must not claim a record was persisted unless a Runtime receipt confirms it. Agents must never access the SQLite file or raw vault directly.

## Source and capture methods

Supported source kinds are declared in `runtime/pdks_capture_runtime/source-registry.json`. A registry entry is not proof that a provider connector exists.

Capture methods:
- `manual_upload`: owner explicitly supplies content; no connector grant is inferred.
- `api_import`: programmatic import; requires a trusted active consent grant.
- `system_sync`: connector synchronization; requires a trusted active consent grant.
- `device_capture`: microphone/camera/location/desktop/wearable capture; requires a trusted active consent grant and a separate device adapter.

Automatic capture is deny-by-default. Consent must match owner, source kind, purpose `personal_knowledge_capture`, action `capture`, and data domain.

## Agent workflow

1. Receive user material or use a genuinely authorized source adapter.
2. Send material to Runtime as a capture.
3. Read the capture receipt and extracted text/evidence.
4. Draft PDKS records using the canonical schema and Ontology 0.2.1.
5. Include the source asset ID in `provenance.source_refs`.
6. Submit records as candidates; do not approve them.
7. Tell the user what was captured, what could not be extracted, and what needs review.
8. Owner approval is a separate action.

## Governance

- `owner_only` is the only accepted access scope in the 0.5.0 local prototype.
- Connector/device captures require a consent reference that is resolved by Runtime; a model-generated reference is not valid.
- Consent revocation blocks future capture but does not automatically delete existing data.
- Source deletion purges local raw bytes, extracted text, evidence and dependent record bodies; it cannot erase prior backups, OS snapshots or external copies.
- Do not infer permission to capture another person's private conversations, bystanders, employer-controlled data or restricted information.

## Runtime capabilities

Current local prototype:
- manual text and file capture;
- text extraction for TXT, Markdown, CSV, JSON, HTML, EML, ICS and DOCX;
- local content hashing and duplicate detection;
- source/evidence provenance;
- local consent registry and per-Agent bearer tokens;
- candidate record validation against pinned PDKS 0.1.x JSON Schema;
- owner review, local export and local source deletion;
- loopback HTTP API.

Not implemented:
- native DingTalk/WeChat/WeCom/Slack/email/calendar/cloud-drive connectors;
- live transcription, OCR, PDF extraction, video understanding;
- microphone/camera/location/desktop/wearable capture;
- remote/TLS service, per-agent production identity, managed secrets, encryption/KMS;
- background scheduling, multi-device sync, cloud storage, production deletion propagation;
- automatic import/migration into another runtime.

## User interaction

Do not expose database fields, JSON, RDF, OWL, SHACL or token details to ordinary users. Explain in natural language. Ask for consent only when a new source or capture method requires it. Ask for clarification only when domain, sensitivity, ownership, identity or intended action materially changes handling.
