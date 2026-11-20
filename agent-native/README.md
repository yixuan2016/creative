# PDKS Agent-native Bootstrap 0.2.0

> PDKS track: `0.5.3` · Stage: `transitional_skill_development` · Maturity: Experimental / Preview

The local MCP Bridge exposes a Node-native File-first initialization path. Creating the initial PDKS Vault does not require Python. The optional Capture Runtime remains a separate Python-based component.

## What it does
- Read-only MCP tools for environment diagnosis, deterministic plan generation, Vault status and verification.
- Mutating `pdks_native_apply` protected by exact plan SHA-256, explicit confirmation phrase and acknowledgement that local storage is not encrypted at rest.
- Creates a portable Markdown Vault, starter templates and copies frozen Ontology 0.2.1 assets.
- Preserves user-edited Markdown on reinitialization and refuses unmanaged non-empty directories.
- Optional MCP Apps setup panel; text-only MCP tools remain the fallback.
- CLI remains available for developers and troubleshooting.

## Requirements
- Node.js 22.12+ and npm.
- npm registry access to install MCP SDK / MCP Apps dependencies and build optional UI.
- Python is not required for native Vault initialization; Python 3.10+ is required only for the separately enabled Capture Runtime.
- No administrator privileges are required.

## Install
macOS/Linux: `./setup/install-agent-bridge.sh --confirm "INSTALL PDKS AGENT BRIDGE"`  
Windows PowerShell: `.\setup\install-agent-bridge.ps1 -Confirm "INSTALL PDKS AGENT BRIDGE"`

## Native workflow
`pdks_native_doctor` → `pdks_native_plan` → explicit user approval → `pdks_native_apply` → `pdks_native_verify`.

Apply requires review of exact paths and plan, matching plan SHA-256, confirmation phrase `CONFIRM INITIALIZE PDKS`, and acknowledgement of unencrypted local storage.

## Boundaries
Initialization does not connect data sources, collect data, import history, start background services, modify Agent settings, or enable cloud sync. No static encryption, OS Keychain, remote relay, multi-device sync or Node-native capture Runtime is included. Real MCP host compatibility and DWS tenant delivery remain unverified. Use synthetic or non-sensitive data only.
