# PDKS 0.4.0 Ontology-first Validation Report

## Passed
- Automated tests: **20/20 passed**.
- Example records: **29**, across 3 scenario owners; JSON Schema, controlled vocabulary and strict internal references passed.
- Authorization gate: trusted active consent references accepted; missing trusted references for device capture rejected. Sample consent references are synthetic test fixtures only.
- Ontology assets: **9 Turtle files / 2,187 triples** parsed successfully.
- Runtime ontology graph: 607 triples; vocabulary graph: 437; event taxonomy: 421; SHACL shapes: 105.
- Event Taxonomy: 72 event type codes; controlled vocabulary: 67 codes.
- Runtime term coverage: 98/98 referenced PDKS terms are declared in the loaded ontology.
- SQLite import, restart persistence, idempotency, optimistic concurrency, owner partitioning, record versioning, Turtle export, JSON-LD roundtrip, SPARQL and projection rebuild passed.
- Ontology-aware tables coexist with the existing ADS-WORK-09 SQLite store in the same database file.

## Not run / not claimed
- pySHACL is not installed in this build environment. SHACL files passed Turtle syntax parsing, but SHACL runtime conformance was **not run**.
- No database encryption, key management, owner authentication or formal Consent / Policy Service.
- No live DingTalk / voice / mail / calendar connector, multi-device sync or physical deletion propagation.
- SPARQL is executed over a one-owner in-memory RDF graph; this is a local reference implementation, not a production graph database.
