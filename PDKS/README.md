# PDKS — Personal Data Knowledge System

**Current release:** 0.5.3 Node-native Agent Bootstrap Preview  
**Stage:** `transitional_skill_development`  
**Maturity:** Experimental / Preview

PDKS is the personal data and knowledge substrate being developed as a transitional foundation toward a future Personal AI Life OS. It is not yet the final Personal AI Life OS.

## Architecture
- Standards: Record Schema 0.1.x, Event Taxonomy 0.1.0, Ontology 0.2.1.
- Agent-native: Node Bridge, MCP tools and optional MCP Apps.
- Bootstrap: initializes local File-first Vault without Python.
- Capture: optional Python Runtime, separately installed and authorized.
- Storage: Markdown, JSON/JSONL, attachments; SQLite remains in optional Runtime.
- Connectors: DWS preview, real tenant validation outstanding.

## Standards and governance documents

- [PDKS-STD-001 — Personal Data & Knowledge Sedimentation Standard V1.0](standards/PDKS-STD-001-个人数据与知识沉淀总体标准-V1.0.md)
- [PDKS Agent Skills Technical Specification V1.0](skills/PDKS-SKILL-SPEC-001-Agent-Skills技术规范-V1.0.md)
- [PDKS Agent Skills Acceptance Matrix V1.0](skills/PDKS-SKILL-ACCEPTANCE-001-Agent-Skills验收矩阵-V1.0.md)

These documents are review drafts. They define target requirements and do not imply that every listed capability has been implemented or accepted.

## First use
`pdks_native_doctor` → `pdks_native_plan` → explicit user approval → `pdks_native_apply` → `pdks_native_verify`.

Initialization does not connect sources, start collection, import history, install background services or enable cloud sync.

## Safety
Vault files are not encrypted at rest. Use synthetic/non-sensitive data only. A cloud-only Agent cannot access local files without a configured local bridge.

## Project map
`standards/`, `skills/`, `agent-native/`, `installer/`, `runtime/`, `connectors/`, `storage/`, `docs/`, `examples/`, `tests/`, `reports/`, `releases/`, `tools/`.
