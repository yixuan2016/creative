# Release Notes — PDKS 0.4.1

## Theme: Ontology Quality Gates & Semantic Governance

### Added
- `pdks_ontology_governance.py`: runtime term coverage, vocabulary coverage, migration bridge and semantic compatibility checks.
- `OntologyRuntime.validate_shacl()`: pySHACL execution with controlled vocabulary and taxonomy reference graphs.
- CLI commands: `ontology-check`, `ontology-diff`; `validate --shacl` as a required runtime gate.
- Ontology 0.2.1 immutable release directory with complete legacy class/property equivalence bridges.
- 34 legacy SKOS concept `skos:exactMatch` bridges.
- Enhanced SHACL constraints for owner isolation, taxonomy membership, consent presence, Agent Action Proposal and qualified relationships.
- JSON-LD graph isomorphism regression test.
- Ontology SHA-256 manifest and builder/verifier.
- GitHub Actions ontology CI workflow.

### Compatibility
- PDKS Record Schema remains 0.1.x.
- Ontology 0.2.0 is retained unchanged as an archived release; Runtime now loads Ontology 0.2.1.
- 71/71 historical OWL classes and properties have explicit bridges.
- 34/34 historical controlled concepts have exact-match bridges.

### Local Validation
- 27 tests: 26 passed, 1 skipped because pySHACL is unavailable in the local execution environment.
- Ontology Governance CLI: valid.
- Runtime term coverage: 98/98.
- No breaking semantic changes detected.
- 14 relaxed domain/range constraints flagged for domain-owner review.
- Manifest: 8/8 resource hashes verified.
- Example data: 29 records across 3 owner partitions pass strict references and trusted-consent fixture gates.

### Not claimed
- SHACL runtime conformance has not yet been executed locally because pySHACL could not be installed in the network-restricted environment. The GitHub Actions workflow installs pySHACL and runs the real gate; a successful Actions run is required before claiming SHACL CI passed.
- Formal identity, Consent / Policy Service, encryption, live connectors, multi-device sync and physical deletion propagation remain unimplemented.