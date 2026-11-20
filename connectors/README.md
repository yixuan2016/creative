# PDKS Connectors

Connector integrations are optional and separately authorized.

Current preview:
- DingTalk DWS official CLI adapter: `runtime/pdks_capture_runtime/connectors/dws/`
- Real tenant delivery has not been verified.
- Historical pagination/backfill is not implemented.

Every connector must declare source identity, supported events, permission scopes, retention behavior, provenance, error handling, and revocation behavior. Never collect credentials in chat or silently widen source scopes.
