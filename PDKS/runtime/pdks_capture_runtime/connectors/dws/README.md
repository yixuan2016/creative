# PDKS DWS Connector 0.1.0

Experimental read-only connector for the official DingTalk Workspace CLI (`dws`). It remains part of transitional Skill development.

## Components

- `cli.py`: safe subprocess wrapper, read-only auth status, event catalog/schema and approved command-schema discovery.
- `stream.py`: DWS event consume process, NDJSON parser, ready-marker handling, graceful stop.
- `connector.py`: PDKS consent/profile preflight and DWS event → Source Asset mapping.
- `catalog.py`: reviewed 33-key public personal event catalog and event filter compatibility rules.

## Safety

- No shell invocation; no arbitrary DWS command strings.
- No DWS business write commands are exposed.
- Each capture requires an active PDKS DWS/work consent.
- Profile is explicit and must match the read-only auth snapshot when returned by DWS.
- DWS tokens remain inside DWS; PDKS does not read its Keychain or token files.
- Calendar and minutes stable identifiers use `biz_id` when present.
- Real tenant event delivery must be verified separately. Public event catalog visibility does not imply tenant enablement.

See `../../../../docs/19-PDKS_0.5.1_DWS官方CLI接入适配器设计与参考实现.md`.


## Strict preflight (0.5.1.2)

The CLI now calls `validate_preflight(event_keys)` before `DWSConsumer.start()`. It fails closed unless PDKS Consent is active, DWS reports `authenticated: true`, the auth status is determinate, token validity is not false, local auth state does not require repair or report unreadable, the active profile exactly matches the selected profile, and every requested event schema is non-empty. A failed preflight never starts a DWS subscription. This still requires real-tenant event-delivery validation.
