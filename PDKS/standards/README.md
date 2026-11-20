# Standards and Ontology

This folder is the canonical location for PDKS machine-readable standards.

Frozen compatibility baseline for the 0.5.3 preview:
- Record Schema: 0.1.x
- Event Taxonomy: 0.1.0
- Ontology: 0.2.1
- Stable term namespace: `urn:pdks:ontology#`
- Ontology version IRI: `urn:pdks:ontology:0.2.1`

JSON Schema defines the record envelope; OWL/RDF defines semantic classes and properties; SHACL defines graph constraints; SKOS vocabularies and event taxonomy define controlled concepts. These layers are complementary, not interchangeable.

Canonical machine assets are currently bundled in `skills/pdks-personal-knowledge/assets/`. They are being mirrored here as the project evolves. Do not change frozen terms without a versioned migration and governance review.
