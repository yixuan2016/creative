# PDKS Core Data Model

PDKS 0.1.0 remains the canonical data standard used by Skill 0.2.0. Skill version and data standard version are intentionally separate.

## Nine record types

| Type | Definition | Key payload focus |
|---|---|---|
| entity | Stable real-world or conceptual referent | entity_type, canonical_name, aliases |
| source_asset | Original source carrier | source_type, origin_system, source_locator, captured_at, media_type, content_hash |
| evidence_segment | Locatable evidence from a source | source_ref, locator, excerpt, modality |
| event | Occurrence that happened | event_type, title, start_at, participants, context_refs, evidence_refs |
| assertion | A statement or claim | assertion_type, content, asserted_by_ref, epistemic_status, evidence_refs |
| knowledge_asset | Reusable knowledge | knowledge_type, title, summary, content, applicability, limitations, derived_from_refs |
| personal_context | Time-qualified context about a person | context_type, subject_ref, value, verification_status, evidence_refs, review_policy |
| action | Future or ongoing work | action_type, title, status, assignee_ref, due_at, dependencies |
| relationship | Qualified relation between records | subject_ref, predicate, object_ref, evidence_refs, status, confidence_level |

## Common envelope
Each record carries:
- `pdks_version`
- `object_id`
- `object_type`
- `created_at`, `updated_at`
- `owner_ref`
- `domains`, optional `primary_domain`
- `provenance`
- `governance`
- `lifecycle`
- optional `field_states`
- `payload`

## Stable identifiers
Use stable IDs from the host system if available. Otherwise generate a local UUID/URN with a declared namespace and preserve it through export/import. Never invent third-party IDs.

## Field states
Use:
- `unknown`
- `not_captured`
- `not_applicable`
- `withheld`
- `unresolved`

Do not use empty strings to hide missing information.

## Extension policy
Do not alter canonical 0.1 fields. Experimental fields must be namespaced and retained under an extension mechanism or sidecar metadata. Propose baseline changes separately.
