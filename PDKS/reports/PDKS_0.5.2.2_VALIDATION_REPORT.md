# PDKS 0.5.2.2 Validation Report

Date: 2026-11-19  
Stage: `transitional_skill_development`  
Maturity: Experimental / Preview

## Automated test summary

| Suite | Total | Passed | Skipped | Failed |
|---|---:|---:|---:|---:|
| Python project tests | 47 | 46 | 1 | 0 |
| Ontology prototype tests | 33 | 32 | 1 | 0 |
| Capture Runtime tests | 64 | 64 | 0 | 0 |
| Node Agent Bridge tests | 6 | 6 | 0 | 0 |
| **Total** | **151** | **149** | **2** | **0** |

The two skipped tests are existing optional-dependency checks. No test failures were observed.

## Additional checks

- Python compileall: passed.
- Node syntax checks for CLI, core, MCP server and MCP Apps UI source: passed.
- Stage validator: `transitional_skill_development`, 12/12 checks passed.
- Ontology 0.2.1: valid; runtime terms referenced 98 / declared 98; 67 controlled vocabulary codes; 72 event taxonomy codes.
- Ontology manifest: 8 declared files verified.
- Node CLI doctor: status `ready`, 9 / 9 checks passed in this development environment (Node 22.16.0, Python 3.13.5).
- Node CLI plan: produced a plan with SHA-256 `15c2c2c81cb9a15fac9b15ed2bbd64fa5ff2e0c101012460fe9c5473be1c79e6` for the current sandbox defaults. This is a test plan only; no install was applied.
- Node CLI config preview: valid JSON; generated a local MCP STDIO snippet without editing Agent settings.
- Vault initialization helper: initialized a temporary File-first Vault, copied Ontology 0.2.1 assets, created safe defaults, and preserved pre-existing user-edited config/ontology files on a second initialization.
- Apply safety gates: rejected mismatched plan hashes, wrong confirmation phrases and missing unencrypted-storage acknowledgement before filesystem mutation.
- Agent Bridge install script plan mode exited with the documented confirmation-required status and did not create `node_modules/` or modify Agent settings.

## MCP integration status

The server and MCP Apps UI source use the official MCP TypeScript SDK v2 and MCP Apps extension packages. npm registry access timed out in this build environment, so package installation, UI build, MCP Inspector protocol tests and real host tests were not run. The MCP server is source-complete but not runtime-certified in this package build.

## Scope and security limitations

The Node.js Agent Bridge delegates to the existing Python Bootstrap Engine 0.2.0; Python 3.10+ remains required. The full apply operation was not executed because it provisions a virtual environment and installs the pinned `jsonschema` dependency from PyPI. Host configuration is preview-only; no Agent config files are changed. The MCP Apps UI is optional and depends on host support; regular MCP tools are the fallback.

Not implemented: managed Python runtime, Node-native Capture Runtime, automatic host configuration modification, at-rest encryption, OS Keychain, DWS OAuth, source subscriptions, historical import, background service, cloud backup/sync, remote Relay and multi-device synchronization.

Do not use this preview for sensitive personal or enterprise data until encryption and key management are implemented and reviewed.
