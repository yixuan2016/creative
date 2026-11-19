# PDKS Ontology-first Architecture 0.2.1 / Runtime 0.4.1

## The four-layer contract

| Layer | Authority | What it answers | Example |
|---|---|---|---|
| Ontology (OWL/RDFS) | Meaning | What is a Person, Event, Assertion, Intent, Evidence or relation? | `pdks:Event` |
| Controlled vocabulary / Taxonomy (SKOS) | Standard values | Which event type, domain, epistemic status or sensitivity value is used? | `work.meeting.internal_meeting` |
| Record Schema (JSON Schema) | Shape | Which fields and data types must a JSON record contain? | `object_type`, `owner_ref`, `payload` |
| Graph Shapes (SHACL) | Graph constraints | Which semantic relationships must exist or be unique? | Event has exactly one event type |
| Runtime / Database | Persistence and operation | How are records stored, versioned, queried, audited and migrated? | SQLite + RDF projection |

The layers cooperate but are not substitutes for each other.

## Canonical data vs semantic projection

1. The original PDKS JSON record is the canonical, portable record.
2. The source asset (audio, document, message export) remains in file/object storage under its own retention and access controls.
3. RDF triples are projected from canonical records using a versioned mapping.
4. The RDF projection can be deleted and rebuilt without losing the canonical records.
5. Every projection is tagged with an ontology version. Do not silently mix projections from different ontology versions.

## Stable identifiers and namespace

- Ontology version IRI: `urn:pdks:ontology:0.2.1`
- Stable term namespace: `urn:pdks:ontology#`
- Controlled vocabulary namespace: `urn:pdks:vocabulary:0.2#`
- Event taxonomy namespace remains `urn:pdks:taxonomy:event:0.1#` during this release.
- Owner graph name is derived from a one-way hash of owner_ref; raw owner identifiers are not embedded in graph names.

The 0.2.1 ontology includes `owl:equivalentClass` and `owl:equivalentProperty` bridges from the old `urn:pdks:ontology:0.1#` namespace. Historical records are not rewritten just to update an ontology.

## Core conceptual distinctions

- **Event**: something that happened or is reported to have happened.
- **Assertion**: a person or system expressed a statement. It may be an opinion, hypothesis, intention or reported observation; it is not automatically a fact.
- **EvidenceSegment**: a locatable portion of a source asset.
- **KnowledgeAsset**: a reusable method, insight, lesson, principle or case derived from evidence and experience.
- **PersonalContextStatement**: a time-qualified statement about a person's role, capability, goal, responsibility, preference or current focus.
- **ActionSpecification / Intent**: a person's plan, task or commitment.
- **AgentActionProposal**: an agent-proposed external or state-changing operation. It requires a separate approval and policy gate.
- **QualifiedRelationship**: a relation that needs its own confidence, evidence, status or validity period.

## Temporal semantics

Do not collapse:
- event occurrence (`pdks:occurredDuring`, OWL-Time Interval);
- source capture (`pdks:capturedAt`);
- record creation/update (`dcterms:created`, `dcterms:modified`);
- assertion expression (`pdks:assertionAt`);
- due time (`pdks:hasDueTime`);
- knowledge/context validity (`pdks:validDuring`).

Original timezone offsets and time precision must be retained in the canonical record.

## Provenance semantics

Do not conflate:
- `owner_ref`: who owns the personal data partition;
- `provenance.created_by`: which user/agent created this record;
- `payload.asserted_by_ref`: who said or asserted the statement;
- `provenance.processing_activity_ref`: which processing activity generated the derived object;
- `payload.source_refs` / evidence refs: where the content came from.

Use PROV-O for derivation and attribution where semantically correct; use PDKS-specific predicates for source references and assertion semantics.

## Governance semantics

Ontology describes governance facts; it does not enforce authorization by itself. The runtime must enforce:
- owner partitioning;
- access scope and sensitivity filters;
- trusted consent resolution for device/connector capture;
- purpose limitation and retention;
- revocation propagation;
- deletion propagation across source assets, derived records and backups;
- approval before external Agent actions.

A `consent_ref` string is not proof of consent until a trusted authorization service validates it.

## Runtime storage design

SQLite remains the local transactional source for canonical JSON records. The ontology-aware extension stores:
- canonical records and immutable record versions;
- active ontology registry and manifest hash;
- owner-scoped RDF triples as a materialized projection;
- owner revision and metadata-only audit events.

The RDF projection is owner-partitioned. Cross-owner queries are not allowed by the local store API. Binary source files are stored separately; SQLite stores their references, hashes and locators.

## Validation sequence

1. JSON Schema: envelope and field types.
2. Ontology profile: class mapping, controlled vocabulary, temporal and provenance rules.
3. Reference validation: PDKS object references resolve within the import bundle or an approved external identity registry.
4. SHACL: graph-level constraints, when pySHACL is installed.
5. Runtime policy: owner, consent, purpose, access and action approval.

OWL entailment is not a substitute for explicit validation. The open-world assumption means missing triples do not imply a negative fact.

## 0.1 → 0.2 migration

- Keep PDKS JSON Schema 0.1.x unchanged in this release.
- Re-project records to the stable `urn:pdks:ontology#` term namespace.
- Retain legacy term equivalence bridges.
- Preserve object IDs, source assets, evidence, record versions and lifecycle state.
- Write the active ontology version into each stored projection and export manifest.
- Rebuild RDF triples from canonical JSON when ontology mapping changes.


## Ontology quality gates (0.4.1)

- Run the runtime term coverage check before changing PDKS predicates or classes.
- Every 0.1 OWL class/property must have an explicit `owl:equivalentClass` / `owl:equivalentProperty` bridge.
- Every historical controlled vocabulary concept must be bridged by stable notation and `skos:exactMatch`.
- Compare `rdfs:domain` / `rdfs:range` changes; new restrictions are breaking, relaxations require semantic-owner review.
- Run pySHACL against each owner-scoped RDF projection. A missing pySHACL dependency is `unavailable`, not a passing result.
- JSON-LD round-trip must preserve RDF graph isomorphism.
- Verify the Ontology SHA-256 manifest before release.
