# PDKS 0.5.3 Preview

## Highlights
- Node-native Bootstrap initializes a portable File-first Vault without requiring Python.
- Ontology 0.2.1 assets are bundled and verified by SHA-256.
- Native CLI supports doctor, plan, apply and verify workflows.
- Initialization requires explicit approval and is designed to be idempotent.
- Existing user Markdown is preserved; unsafe path overlaps and symlink escapes are refused.

## Boundaries
- Capture Runtime remains optional and Python-based.
- No source connection, historical import, background service, or cloud sync is enabled by initialization.
- Local Vault is not encrypted at rest.
- MCP host compatibility and real DWS tenant delivery remain unverified.
- Experimental preview only; not production-ready.
