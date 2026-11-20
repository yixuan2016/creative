# PDKS — Personal Data Knowledge System

> **0.5.3 · Node-native Agent Bootstrap Preview**  
> Development stage: `transitional_skill_development` · Maturity: Experimental / Preview

PDKS is the personal data and knowledge substrate being developed as a transitional foundation toward a future Personal AI Life OS. It is designed around a user-controlled, local-first, File-first Vault, a governed personal ontology, and agent-native setup and access.

## Positioning

PDKS is not yet the final Personal AI Life OS. It is an engineering transition stage for validating the durable data layer, ontology contracts, agent interoperability, and safe initialization workflow.

## Current architecture

- **Standards:** frozen PDKS 0.1.x record contract and Ontology 0.2.1 baseline.
- **Agent-native layer:** agent bridge, MCP server / tools, and MCP Apps preview.
- **Bootstrap:** Node-native initialization creates the Vault and copies ontology assets without requiring Python.
- **Capture:** Python Capture Runtime remains optional and separate.
- **Storage:** File-first local Vault with explicit export/projection boundaries.
- **Connectors:** DWS connector remains a preview; live tenant delivery is not verified.

## Safe first-use sequence

`pdks_native_doctor` → `pdks_native_plan` → explicit user approval → `pdks_native_apply` → `pdks_native_verify`.

Initialization does **not** connect data sources, start capture, import historical data, install background services, or enable cloud sync.

## Release status

See [stage](STAGE.md), [roadmap](ROADMAP.md), [release notes](RELEASE_NOTES_0.5.3-preview.md), and [validation report](reports/PDKS_0.5.3_VALIDATION_REPORT.md).

## Safety

The local Vault is not encrypted at rest. Do not use this preview with sensitive personal or enterprise data. Review every proposed filesystem operation before approval. Cloud-only Agents cannot access local files without an explicitly configured local bridge.

## Directory map

- `standards/` — ontology, schemas, field dictionary, taxonomy and contracts
- `skills/` — setup and personal knowledge Skills
- `agent-native/` — Agent Bridge, MCP tools and MCP Apps
- `runtime/` — optional capture runtime and storage adapters
- `connectors/` — source integrations and DWS preview
- `docs/` — architecture, implementation and user guides
- `examples/` — example records and projections
- `tests/` — automated checks
- `reports/` — validation and audit reports
- `releases/` — release manifests and packages

This directory is the canonical project home in `yixuan2016/creative`.
