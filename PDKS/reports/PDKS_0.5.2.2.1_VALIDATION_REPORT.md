# PDKS 0.5.2.2.1 Validation Report

Date: 2026-11-19  
Stage: `transitional_skill_development`  
Maturity: Experimental / Preview  
PDKS track: `0.5.2.2`  
Agent Bridge: `0.1.1`

## Automated tests

| Suite | Total | Passed | Skipped | Failed |
|---|---:|---:|---:|---:|
| Python project tests | 47 | 46 | 1 | 0 |
| Ontology prototype tests | 33 | 32 | 1 | 0 |
| Capture Runtime + DWS + File Store | 64 | 64 | 0 | 0 |
| Node Agent Bridge | 9 | 9 | 0 | 0 |
| **Total** | **153** | **151** | **2** | **0** |

The two skipped tests are existing optional-dependency checks.

## Additional checks

- Node.js version: `22.16.0`; required minimum `22.12.0`.
- Python version: `3.13.5`; required minimum `3.10`.
- Node syntax checks: CLI, MCP server, Bootstrap core and MCP Apps UI source passed.
- Node CLI `doctor`: `ready`, 9/9 environment checks passed in this development environment.
- Node CLI `plan`: generated a deterministic plan with PyPI network dependency explicitly listed; no install was applied.
- Stage validator: `transitional_skill_development`, 12/12 checks passed.
- Ontology 0.2.1: valid; runtime terms 98/98, controlled vocabulary 67 codes, event taxonomy 72 codes.
- Ontology manifest: 8/8 files verified.
- File Store Runtime tests: 7 tests passed as part of the 64 Runtime suite.
- Path security: symlink escape detection and install/Vault overlap rejection covered by two new Node regression tests.
- Apply approval: exact plan hash, exact confirmation phrase and unencrypted-storage acknowledgement required by tests.
- CLI doctor and plan are read-only; no install was applied during validation.

## MCP integration status

The MCP server and MCP Apps UI source are present. npm package installation, Vite build, MCP Inspector handshake and real Agent-host tests were not run in this environment. Therefore the bridge is source-validated but not protocol- or host-certified. The interactive panel is optional; conversational MCP tools remain the fallback design.

## Security and maturity limitations

- Python 3.10+ is still required by the current Bootstrap Engine; a managed Python runtime is not included.
- Local SQLite and Vault are not encrypted at rest. Do not use sensitive personal or enterprise data.
- No OS Keychain, automatic Agent config modification, DWS OAuth, source subscriptions, historical import, background service, cloud backup/sync, remote Relay or multi-device synchronization.
- The installation confirmation does not authorize data collection or third-party data-source connection.
- Host-specific compatibility for Claude, Cursor, Codex, WorkBuddy and other Agents is not certified.

## Conclusion

The Agent Bridge 0.1.1 adds tested symlink-aware home-path validation and rejects identical or nested install/Vault targets. This hardens the local Bootstrap safety boundary while keeping PDKS standards, Ontology and Record Schema unchanged. This remains an experimental transition-stage engineering release, not a production-ready Personal Assistant OS.
