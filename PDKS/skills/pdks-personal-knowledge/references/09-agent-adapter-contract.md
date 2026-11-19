# Agent Adapter Contract

## Purpose
The Skill is portable instructions plus machine-readable resources. A host agent adapter supplies tools for source access, persistence, retrieval, identity resolution, and user authorization.

## Capability levels

| Level | Host capability | PDKS behavior |
|---|---|---|
| L0 | Prompt/context only | Analyze supplied text; draft records; no persistent write |
| L1 | File read/write | Read source files; create JSON records and export bundles |
| L2 | Connected apps / connectors | Retrieve authorized messages, documents, mail or calendar records |
| L3 | Persistent database / memory | Store, update, query and version PDKS records |
| L4 | Background automation / capture | Run authorized recurring capture, event processing and sync |
| L5 | Full migration adapters | Import/export with ID mapping, permissions and receipts |

Do not claim a higher capability level than the host actually provides.

## Adapter operations

A host integration may expose equivalent operations:
- `list_sources(scope, since, until)`
- `read_source(source_id)`
- `write_record(record, idempotency_key)`
- `read_records(query)`
- `resolve_entity(candidate, context)`
- `check_permission(source_or_destination, action)`
- `export_bundle(query, destination)`
- `import_bundle(bundle, mapping, permissions)`
- `record_receipt(operation, result)`

These are conceptual contracts, not assumed tool names. Discover actual host tools and use their documented schemas. Never invent tool calls.

## Idempotency
- Use `object_id` as the stable identity.
- Use source ID + locator + content hash as a candidate deduplication key.
- Update an existing record only after confirming it is the same record.
- Keep a revision trail for material changes.

## Authorization
- Read only sources the user has connected / authorized.
- Do not connect a new app or widen scope without explicit user action.
- Confirm consequential writes, external sharing, deletion or publication when host policy requires it.

## Receipts
When writing, return destination ID, timestamp, operation status and warnings if the host provides them. If no receipt exists, say "prepared" rather than "saved".
