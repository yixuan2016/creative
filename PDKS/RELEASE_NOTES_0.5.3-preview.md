# PDKS 0.5.3 Preview — Node-native Agent Bootstrap

Stage: `transitional_skill_development`  
Maturity: Experimental Preview

## Added

- Node-native File-first Bootstrap 0.2.0 using Node built-in modules.
- `pdks_native_doctor`, `pdks_native_plan`, `pdks_native_apply`, `pdks_native_verify` MCP tools.
- Interactive MCP Apps setup panel switched to the Node-native Vault initialization flow.
- Python is no longer required to create the initial Obsidian-compatible Vault.
- User-scoped application config and standard File-first Vault folders.
- Copy of frozen Ontology 0.2.1 assets and SHA-256 manifest validation.
- Idempotent re-initialization that preserves user-edited Markdown.
- Refusal of symlink escapes, overlapping paths and non-empty unmanaged target directories.
- Setup Skill 0.3.0 and ordinary-user guide.

## Preserved

- Existing Python Capture Runtime 0.1.1 as an optional, separately installed component.
- DWS connector 0.1.0, File Store Adapter 0.1.0, Personal Knowledge Skill 0.3.4.
- Ontology 0.2.1, Record Schema 0.1.x and Event Taxonomy 0.1.0 remain frozen.
- Existing CLI and legacy Python Runtime workflow remain available.

## Validation

- Agent Bridge Node tests: 18 passed, 0 failed.
- Python suites and ontology checks are tracked in `reports/PDKS_0.5.3_VALIDATION_REPORT.md`.
- Real MCP SDK install/build, MCP Apps host rendering and named Agent host validation are not executed in the current offline environment.

## Limitations

- The MCP Server still requires Node.js 22.12+ and npm dependencies.
- Capture Runtime still requires Python 3.10+.
- No managed Node distribution or signed native installer is included.
- No automatic Agent config mutation.
- No local-at-rest encryption, OS keychain, remote sync, or multi-device conflict resolution.
- No real DWS tenant capture verification.

Do not use this preview for sensitive personal data.