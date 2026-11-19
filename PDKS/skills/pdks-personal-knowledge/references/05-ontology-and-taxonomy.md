# Ontology and Taxonomy

## Five different layers

| Layer | Question | PDKS resource |
|---|---|---|
| Ontology | What concepts exist and how are they related? | OWL 2 / RDF |
| Taxonomy | How are concepts grouped hierarchically? | SKOS |
| Controlled vocabulary | Which stable codes and status values are allowed? | SKOS concepts / enums |
| Data schema | Which fields and data types does a record contain? | JSON Schema |
| Validation | Does the graph/data satisfy constraints? | SHACL + business rules |

## Reused standards
- OWL 2: ontology classes and properties.
- RDF 1.1: graph data model.
- SKOS: taxonomy and controlled concepts.
- PROV-O: provenance and processing responsibility.
- OWL-Time: temporal entities and intervals.
- SHACL: RDF graph validation.
- JSON Schema Draft 2020-12: application record validation.

## PDKS event domains
`work`, `learning`, `thinking`, `life`, `relationship`, `growth`, `finance`, `health`, `other`.

Read the canonical event taxonomy JSON for the full set of 62 event concepts. Use the pinned taxonomy version in every event. If no type fits, use `other.unclassified` and mark the classification for review.

## Core semantic relations
- hasParticipant / participatedIn
- hasEventType
- occurredDuring
- hasContextEntity
- hasEvidence
- extractedFrom
- derivedFrom
- generatedBy
- attributedTo
- assertedBy
- hasEpistemicStatus
- hasOutcome
- realizesAction
- assignedTo
- hasDueTime
- hasSubject
- validDuring
- possibleIdentityMatch
- mergedInto

## Important modeling boundaries
- Event vs Action: occurrence vs intention.
- Source Asset vs Evidence Segment: carrier vs locatable fragment.
- Assertion vs Knowledge Asset: claim vs reusable, qualified knowledge.
- Personal Context vs Entity: time-qualified personal state vs referent.
- Sensitivity vs Access Scope: classification vs authorization.
- Candidate identity match vs confirmed identity: do not use `owl:sameAs` until confirmed.

## Storage architecture
Do not require all business data to be stored as RDF triples. JSON, relational and object storage can remain operational stores. Use mapping to produce RDF/JSON-LD semantic views. Preserve the original PDKS records and stable IDs.
