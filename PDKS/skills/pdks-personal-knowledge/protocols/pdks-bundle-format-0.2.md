# PDKS Export Bundle Format 0.2

## Purpose
Defines a portable archive layout for exchanging PDKS 0.1 records. The bundle format version is independent from the underlying record standard version.

## Required root files
- `manifest.json`
- `records/` containing one JSON file per record
- `standards/pdks-0.1-record.schema.json`
- `standards/pdks-event-taxonomy-0.1.json`

Recommended:
- ontology, SHACL and mapping resources under `standards/`
- `source-assets/` for authorized originals
- `reports/validation-report.json`
- `mappings/id-map.json`

## Manifest shape
```json
{
  "bundle_format": "PDKS-Export-Bundle",
  "bundle_version": "0.2.0",
  "pdks_standard_version": "0.1.0",
  "exported_at": "2026-11-19T12:00:00+08:00",
  "exported_by": "agent-or-system-id",
  "record_counts": {"event": 1},
  "files": [
    {"path": "records/event/example.json", "size_bytes": 100, "sha256": "..."}
  ],
  "external_references": [],
  "excluded_sources": [],
  "notes": []
}
```

## Security requirements
- Reject absolute paths and `..` traversal paths.
- Verify SHA-256 before import.
- Do not include credentials, tokens, or unauthorized source files.
- Preserve original IDs and governance.
- Do not widen access scope during import.
