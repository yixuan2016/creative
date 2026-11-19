# Multi-Agent Adapter Contract

## Design decision

PDKS Runtime is the shared personal data service. Agents are replaceable clients. No Agent connects directly to SQLite or the raw vault.

```text
ChatGPT adapter ─┐
Claude adapter ──┼── HTTPS / MCP / local tool bridge ── PDKS Runtime API ── SQLite + file vault
Codex adapter ───┤
Cursor adapter ──┘
```

The REST/OpenAPI contract is the canonical transport contract in Runtime 0.1.1. A host may expose it as native tools, an MCP server, an OpenAPI connector, or a local client. These are adapter implementations, not new data standards.

## Minimal tool mapping

| Agent tool | Runtime operation | Required scope |
|---|---|---|
| `pdks_capture_text` | `POST /v1/captures/text` | `capture:write` |
| `pdks_capture_file` | `POST /v1/captures/file` | `capture:write` |
| `pdks_list_captures` | `GET /v1/captures` | `capture:read` |
| `pdks_read_capture` | `GET /v1/captures/{id}` | `capture:read` |
| `pdks_propose_records` | `POST /v1/records/propose` | `records:propose` |
| `pdks_list_records` | `GET /v1/records` | `records:read` |
| `pdks_approve_record` | `POST /v1/records/{id}/approve` | `records:approve` |
| `pdks_create_consent` | `POST /v1/consents` | `consent:manage` |
| `pdks_revoke_consent` | `POST /v1/consents/{id}/revoke` | `consent:manage` |
| `pdks_delete_source` | `DELETE /v1/sources/{id}` | `data:delete` |
| `pdks_export` | `POST /v1/export` | `data:export` |

## Credential model

- Issue a different token for each Agent host.
- Bind every token to one owner and one Agent ID.
- Grant only required scopes.
- Store tokens in the host's secret manager; never in Skill text, prompts, repository files, or source records.
- Revoke a token when an Agent integration is removed.
- Owner approval, consent management, deletion and export scopes should not be granted to general-purpose Agent tokens by default.

## Host compatibility status

Runtime 0.1.1 supplies a loopback-only HTTP API and a standard-library Python client. It does not ship tested native ChatGPT, Claude, Cursor or Codex connectors, nor a production MCP server. Each host requires a small adapter and a supported secure route to the user's runtime. Cloud-hosted Agents cannot reach a user's `127.0.0.1` directly.

## Required behavior

1. Discover the actual host tools before calling them.
2. Never invent connector availability or persistence.
3. Submit PDKS candidate records with source IDs.
4. Never mark records owner-confirmed without the owner action.
5. Show the capture receipt and unresolved questions in ordinary language.
6. Keep source consent and PDKS governance references intact.


## Source connector boundary

DWS is a source-system CLI adapter, not an Agent host adapter. The DWS Connector writes normalized source captures into the Runtime; Agent hosts still use the same Runtime API and per-Agent tokens. See `../pdks_capture_runtime/connectors/dws/README.md` for the DWS-specific boundary.
