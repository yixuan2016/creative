# PDKS 0.4.1 Ontology Governance Validation Report

- Ontology Governance CLI: **valid**
- Runtime term coverage: **98 / 98**
- Required controlled vocabulary values: **54 / 54**
- Event Taxonomy: **72** event-type concepts
- Legacy OWL class/property bridges: **71 / 71**
- Legacy SKOS concept exact-match bridges: **34 / 34**
- Semantic compatibility: **0 breaking changes**; **14 relaxed domain/range constraints** require ontology-owner review.
- Ontology Manifest: **8 / 8** SHA-256 checks passed.
- Example data: **29 records**, **3 owner partitions**, strict references and synthetic trusted-consent fixtures passed.
- JSON-LD round-trip: RDF graph isomorphism test passed.
- Automated tests: **27 total; 26 passed; 1 skipped** because pySHACL is unavailable in the local network-restricted environment.

## SHACL status

The SHACL runtime API and CLI `validate --shacl` are implemented. When pySHACL is unavailable, the runtime returns `unavailable` and the CLI exits non-zero. The package's GitHub Actions workflow installs pySHACL and executes the actual SHACL gate. A successful Actions run is required before reporting SHACL CI as passed.

## Not implemented / not claimed

Formal Consent / Policy Service integration, Owner authentication, database encryption, live connectors, multi-device synchronization, physical deletion propagation and production graph database are not implemented.