# PDKS — Personal Data Knowledge System

**Release:** 0.5.3 Node-native Agent Bootstrap Preview  
**Stage:** `transitional_skill_development`  
**Maturity:** Experimental / Preview  
**Ontology baseline:** 0.2.1 (frozen)

PDKS is a transition-stage personal data and knowledge system. This release makes initialization Agent-native and local-first while retaining the established ontology, Skills, capture runtime, connectors, storage adapters, examples, tests and architecture research.

## Repository contents

- `releases/PDKS_0.5.3_完整综合工程包.zip` — complete source package, including the full directory tree, Markdown/HTML/DOCX documentation, source code, Ontology, examples, tests and reports.
- `docs/` — current implementation specifications and user guides.
- `reports/` — validation report and known integration gaps.
- `STAGE.md` — current maturity and version matrix.
- `ROADMAP.md` — release evolution and next milestones.
- `RELEASE_NOTES_0.5.3-preview.md` — preview release notes.

The ZIP expands to a `PDKS/` directory containing `agent-native/`, `runtime/`, `skills/`, `setup/`, `docs/`, `examples/`, `prototype/`, `tests/`, `reports/`, and `.github/`.

## First use

Use a local-capable Agent with local execution enabled. Read `skills/pdks-setup/SKILL.md`, then follow the explicit sequence:

`pdks_native_doctor` → `pdks_native_plan` → review the exact plan → explicit user approval → `pdks_native_apply` → `pdks_native_verify`.

A cloud-only Agent cannot access local files unless a local bridge is explicitly configured.

## Safety and maturity

- Vault initialization does not connect data sources, start collection, import history, install a background service or enable cloud sync.
- Initial Vault initialization does not require Python. The optional Capture Runtime remains Python-based and separate.
- Local Vault files are not encrypted at rest in this preview. Do not use sensitive personal or enterprise data.
- npm build, MCP Inspector, real DWS tenant delivery and host-by-host compatibility have not been verified.
- This is not a production-ready Personal AI Life OS.
