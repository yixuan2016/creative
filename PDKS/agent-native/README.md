# PDKS Agent-native Bootstrap 0.2.0

> PDKS track: `0.5.3` · Stage: `transitional_skill_development` · Maturity: Experimental / Preview

The local MCP Bridge now exposes a **Node-native File-first initialization path**. Creating the initial PDKS Vault does not require Python. The optional Capture Runtime remains a separate Python-based component.

## What it does

- Exposes read-only MCP tools for native environment diagnosis, deterministic plan generation, Vault status and verification.
- Exposes `pdks_native_apply`, a mutating tool protected by an exact plan SHA-256, an explicit confirmation phrase and acknowledgement that local storage is not encrypted at rest.
- Creates a portable Markdown Vault, starter templates and copies the frozen Ontology 0.2.1 assets.
- Preserves user-edited Markdown on reinitialization and refuses to overwrite unmanaged non-empty directories.
- Provides an optional MCP Apps setup panel; text-only MCP tools remain the fallback.
- Keeps the CLI for developers and troubleshooting.
- Keeps the legacy Python Runtime installer workflow separate (`pdks_bootstrap_*`).

## Requirements

- Node.js 22.12+ and npm.
- npm registry access when installing MCP SDK / MCP Apps dependencies and building the optional UI.
- Python 3.10+ is **not required** for native Vault initialization; it is required only if the user separately enables the current Python Capture Runtime.
- No administrator privileges are required or requested.

## Build the local Agent Bridge

macOS / Linux:

```bash
./setup/install-agent-bridge.sh       # read-only plan only
./setup/install-agent-bridge.sh --confirm "INSTALL PDKS AGENT BRIDGE"
```

Windows PowerShell:

```powershell
.\setup\install-agent-bridge.ps1 -Confirm "INSTALL PDKS AGENT BRIDGE"
```

This installs npm dependencies under `agent-native/` and builds the MCP Apps UI. It does not edit Agent configuration or start collection.

## MCP tools

| Tool | Mutation | Purpose |
|---|---:|---|
| `pdks_native_doctor` | No | Node version, path safety, target state and Ontology asset checks |
| `pdks_native_plan` | No | Deterministic File-first initialization plan + SHA-256 |
| `pdks_native_apply` | Yes | Create local configuration, Vault folders, Markdown templates and Ontology assets after exact approval |
| `pdks_native_verify` | No | Verify manifest, Ontology hashes and Vault structure |
| `pdks_setup_wizard` | No | Optional MCP Apps setup UI |
| `pdks_vault_status` | No | Read Vault manifest metadata only |
| `pdks_agent_config_preview` | No | Print generic/host config snippet; never edits Agent config |
| `pdks_doctor` / `pdks_bootstrap_plan` / `pdks_bootstrap_apply` | Legacy Runtime | Optional Python Capture Runtime setup, separate approval |

## CLI

```bash
node ./bin/pdks-agent.js native-doctor
node ./bin/pdks-agent.js native-plan
# after the exact plan has been reviewed and approved:
node ./bin/pdks-agent.js native-apply --approve-plan <EXACT_PLAN_SHA256> --confirm "CONFIRM INITIALIZE PDKS" --acknowledge-unencrypted-storage
node ./bin/pdks-agent.js native-verify
```

Legacy Python Runtime commands remain available as a separate workflow.

## Approval policy

`pdks_native_apply` requires:

1. The user has reviewed the exact plan and both target paths.
2. The Agent supplies the same `plan_sha256` returned by the plan tool.
3. The user explicitly enters `CONFIRM INITIALIZE PDKS` or confirms via the host's equivalent confirmation control.
4. The user explicitly acknowledges that local Vault files are not encrypted at rest.

No data source is connected, no data is collected, and no background service or cloud sync is enabled by native initialization.

## Limitations

- MCP SDK installation/build and real MCP Inspector tests must be completed in a network-enabled environment.
- MCP Apps rendering depends on host support; text-only tools remain available.
- No host-specific configuration is written automatically.
- The Python Capture Runtime remains optional and separate.
- No static encryption, OS Keychain, remote relay, cloud sync, multi-device sync or Node-native capture Runtime is included.
- No real DingTalk DWS tenant delivery has been verified.

Use synthetic or non-sensitive test data only.
