# PDKS Bundle and Migration Protocol

## Bundle structure

A portable export should contain:

```text
pdks-export/
├── manifest.json
├── records/
│   ├── entity/
│   ├── source_asset/
│   ├── evidence_segment/
│   ├── event/
│   ├── assertion/
│   ├── knowledge_asset/
│   ├── personal_context/
│   ├── action/
│   └── relationship/
├── source-assets/              # only authorized files; optional
├── standards/
│   ├── pdks-0.1-record.schema.json
│   ├── pdks-event-taxonomy-0.1.json
│   ├── pdks-core-ontology-0.1.ttl
│   ├── pdks-core-shapes-0.1.ttl
│   └── pdks-json-to-ontology-mapping-0.1.json
├── mappings/
│   └── id-map.json             # if IDs must be translated
└── reports/
    ├── validation-report.json
    └── migration-report.json
```

## Manifest requirements
- bundle format and version;
- PDKS standard version;
- export timestamp and exporting agent;
- record counts by type;
- file paths, sizes, SHA-256 hashes;
- included / excluded source asset summary;
- external/unresolved references;
- governance note and limitations.

## Import sequence
1. Verify ZIP integrity and manifest hashes.
2. Validate schema and taxonomy versions.
3. Load entities and source assets first.
4. Load evidence segments.
5. Load events and assertions.
6. Load knowledge and personal context.
7. Load actions and relationships.
8. Resolve references and ID map.
9. Apply target permissions conservatively.
10. Produce an import report.

## Loss-aware mapping
For each target field, classify:
- exact: directly preserved;
- transformed: mapped with documented conversion;
- unsupported: retained in raw extension or sidecar;
- omitted: excluded with reason and user authorization if needed;
- unresolved: cannot be mapped safely.

## No false success
A migration plan is not an import. A generated bundle is not a persistent database write. Only report import success after the destination confirms it.
