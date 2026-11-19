# PDKS 0.4.1 Ontology Governance Validation Report

## Executed locally

- Ontology Governance CLI: **valid**.
- Runtime term coverage: **98 / 98**.
- Required runtime controlled vocabulary values: **54 / 54**.
- Event Taxonomy: **72** event-type concepts.
- Legacy 0.1 OWL class/property bridges: **71 / 71**.
- Legacy 0.1 SKOS concept exact-match bridges: **34 / 34**.
- Semantic compatibility: **0 breaking changes**; **14 relaxed domain/range constraints** require ontology-owner review.
- Ontology Manifest: **8 / 8** files verified by SHA-256.
- Example data: **29 records**, **3 owner partitions**, strict internal references and trusted synthetic consent fixtures passed.
- JSON-LD round-trip: RDF graph isomorphism test passed.
- Automated tests: **27 total; 26 passed; 1 skipped** because pySHACL is not installed in this network-restricted local environment.

## SHACL execution status

`OntologyRuntime.validate_shacl()` and the CLI `validate --shacl` path are implemented. When pySHACL is unavailable, the runtime returns `unavailable`; the CLI exits non-zero. This is deliberately not counted as a pass.

The GitHub Actions workflow `.github/workflows/pdks-ontology-ci.yml` installs `requirements-dev.txt` (including pySHACL), validates all three owner-scoped sample graphs with SHACL Advanced/SPARQL constraints, and runs the complete unit test suite. A successful Actions run is required before reporting SHACL CI as passed.

## Compatibility review items

The semantic diff reports 14 relaxed domain/range constraints inherited from the 0.1 -> 0.2 semantic redesign. They are not treated as breaking because they broaden, rather than narrow, the applicable resource range. They remain explicit review items and should be approved or documented by the Ontology owner before a production semantic contract is frozen.

## Not implemented / not claimed

- Formal Consent / Policy Service integration; sample consent refs are synthetic fixtures only.
- Owner authentication, database encryption and key management.
- Live DingTalk, recorder, mail or calendar connectors.
- Multi-device synchronization and physical deletion propagation.
- Production graph database; SPARQL remains owner-scoped and in-memory.
- SHACL runtime pass in this local environment.
