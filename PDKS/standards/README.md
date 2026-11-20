# PDKS Standards and Ontology

This folder is the canonical location for PDKS machine-readable standards and normative documents.

## Normative document

- [PDKS-STD-001 — Personal Data & Knowledge Sedimentation Standard V1.0](PDKS-STD-001-个人数据与知识沉淀总体标准-V1.0.md) — review draft covering acquisition, source integration, record structure, event semantics, knowledge taxonomy, extraction, quality, storage, governance and lifecycle.

## Frozen compatibility baseline for the 0.5.3 preview

- Record Schema: 0.1.x
- Event Taxonomy: 0.1.0
- Ontology: 0.2.1
- Stable term namespace: `urn:pdks:ontology#`
- Ontology version IRI: `urn:pdks:ontology:0.2.1`

JSON Schema defines the record envelope; OWL/RDF defines semantic classes and properties; SHACL defines graph constraints; SKOS vocabularies and event taxonomy define controlled concepts. These layers are complementary, not interchangeable.

Canonical machine assets are currently bundled in the PDKS release package. Do not change frozen terms without a versioned migration and governance review. The V1.0 overall standard does not silently alter the current machine-readable baseline.
