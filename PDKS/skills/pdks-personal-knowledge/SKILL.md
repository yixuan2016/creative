---
name: pdks-personal-knowledge
description: Use PDKS to capture, understand, structure, connect, validate, govern, and migrate a person's work, learning, thinking, life, relationships, knowledge, goals, and actions. Activate for notes, chats, meeting transcripts, voice transcripts, documents, daily logs, personal knowledge bases, personal memory, personal assistant context, or cross-agent data export/import.
compatibility: Works with agents that support the open Agent Skills folder format. Other agents can load this file and its referenced resources manually. Tool access and storage depend on the host agent and user authorization.
metadata:
  standard: PDKS
  standard_version: "0.1.0"
  skill_version: "0.3.4"
  runtime_track: "0.5.0"
  development_stage: "transitional-skill-development"
  maturity: "experimental"
  release_channel: "preview"
  language: "zh-CN"
---

# PDKS Personal Knowledge — Transitional Development Skill

## Mission

**Ontology-first rule:** PDKS Ontology is the semantic contract. JSON Schema describes record shape; SHACL describes graph constraints; controlled vocabularies and Taxonomy provide stable concepts; the database persists canonical records; RDF is a rebuildable semantic projection. Never treat these layers as interchangeable.

Operate as a transitional, product-independent Agent Skill for personal data understanding and knowledge structuring, using the PDKS 0.1 data standard. This is an experimental Skill and local reference implementation, not a complete personal digital foundation platform or production service.

Turn a person's everyday information into trustworthy, connected, time-aware, permission-aware, and portable personal data. Support the full lifecycle:

**Capture → Understand → Structure → Connect → Validate → Preserve → Retrieve → Export / Migrate**

The standard is strict in the background; daily use stays simple in the foreground.

## Current development stage — mandatory boundary

PDKS is currently in **transitional Skill development** (runtime track 0.5.0 / Skill 0.3.4). The deliverable is a portable Agent Skill, machine-readable contracts, and local reference prototypes.

- The Skill can analyze material supplied in the conversation and draft candidate PDKS records.
- Local scripts demonstrate validation, SQLite persistence, RDF projection, and export; they require an executable local environment and are not a hosted service.
- Connected-app access, persistent storage outside the local prototype, and background automation depend on actual host tools and explicit authorization.
- Native DingTalk capture, recorder/device integration, continuous background capture, production identity/consent services, managed encryption/key infrastructure, and multi-device sync are not implemented.
- Personal / enterprise / center Ontology layering is a research proposal only. Do not treat it as a published standard or an implemented data-sharing mechanism.

Always classify a capability as `available_in_skill`, `prototype_local`, `prototype_partial`, `host_dependent`, `not_implemented`, or `future_research`. Never claim that installing this Skill grants tools, permissions, connectors, or persistence. If there is no destination receipt, say that content was prepared rather than saved.

Read `references/11-transition-stage-and-capability-boundaries.md` before making capability claims, and read `references/12-personal-enterprise-center-ontology-extension-proposal.md` only when discussing future cross-scope ontology design. For Personal Capture Runtime integration, read `references/13-personal-capture-runtime.md`. For cross-host validation, use `benchmarks/BENCHMARK_RUNNER_GUIDE.md`, `benchmarks/CROSS_AGENT_TEST_PROTOCOL.md`, `benchmarks/EVALUATION_RUBRIC.md`, and the synthetic prompts under `benchmarks/prompts/`. Evaluator metadata under `benchmarks/cases/` must not be shown to the tested Agent.


Do not make ordinary users learn JSON, event codes, RDF, OWL, SHACL, or database fields. Accept natural language and available source materials. Infer structure automatically. Ask only when ambiguity materially affects identity, meaning, responsibility, deadline, permissions, safety, or an irreversible action.

## Activation conditions

Activate when the user asks to:
- capture or organize personal work, learning, thinking, life, relationship, or growth information;
- turn chats, meetings, voice transcripts, emails, documents, web pages, or daily notes into reusable records;
- extract events, people, projects, statements, decisions, knowledge, personal context, tasks, or commitments;
- build, maintain, or query a personal knowledge base or personal digital foundation;
- validate, normalize, package, export, import, or migrate personal data;
- apply PDKS ontology, taxonomy, schema, provenance, or governance rules.

Do not activate for an unrelated factual question with no personal-data capture, organization, memory, or migration purpose.

## Ontology-first semantic rules

- Use the stable term namespace `urn:pdks:ontology#` from Ontology 0.2.1. The ontology version IRI is `urn:pdks:ontology:0.2.1`; do not invent new predicates or classes in user data.
- Keep PDKS JSON Record Schema 0.1.x as the canonical record envelope during the 0.4 runtime rollout. Ontology 0.2.1 is a semantic upgrade, not a forced rewrite of historical JSON records.
- Map `object_type` to an OWL class. Map event types, domains, epistemic states, context types, sensitivity and access scopes to controlled SKOS concepts.
- Preserve four different times: event occurrence time, source capture time, record creation/update time, and knowledge/context validity time. Use OWL-Time intervals/instants in RDF projections.
- Preserve provenance: record creator, assertion speaker, data owner, source asset, evidence segment, and AI processing agent are different roles.
- Model relationships with direct RDF edges only for a whitelisted predicate. If a relation needs confidence, evidence, status or validity, preserve its `QualifiedRelationship` record as well.
- Keep `Assertion` distinct from `Event`: an assertion is something said or inferred about the world; it does not prove that the described event happened.
- Keep `ActionSpecification` / `Intent` distinct from `AgentActionProposal`: a person's plan is not permission for an agent to execute an external action.
- Do not infer consent from a recording, source file, connector name, or model statement. Device/connector capture requires a consent reference resolved by a trusted authorization service.
- Use `possibleIdentityMatch` for uncertain entity resolution. Do not use `owl:sameAs` unless identity has been explicitly confirmed.
- RDF triples are a versioned, rebuildable projection. Canonical PDKS records and source assets remain authoritative. Store the ontology version used for every projection/export.
- OWL uses an open-world assumption: missing data is not automatically false. Use JSON Schema and SHACL for explicit validation constraints; never present inferred triples as owner-confirmed facts.
- Ordinary users should only see natural-language capture/review. The Agent handles ontology mapping, validation, identifiers and graph maintenance in the background.

Ontology assets are under `assets/ontology/0.2.1/`. Read `references/ontology-first-architecture.md` for the implementation model.

For engineering and release validation:
- Run `python prototype/pdks_ontology_cli.py ontology-check` before changing or publishing Ontology terms.
- Run `validate --shacl` when pySHACL is installed; if the dependency is unavailable, report `unavailable`, never `conforms`.
- Compare all changes against the 0.1 baseline; missing legacy equivalence bridges or newly restrictive domain/range constraints are breaking changes.
- Verify `ontology-manifest.json` after changing any versioned Ontology resource.

## Operating modes

Choose one or more modes based on the user's request. Do not ask the user to choose a mode if intent is clear.

1. **Capture** — understand source material and create candidate records.
2. **Daily review** — summarize events, decisions, learnings, open actions, and unresolved items for a period.
3. **Knowledge synthesis** — consolidate repeated experiences into reusable knowledge, while preserving evidence and uncertainty.
4. **Personal context** — create or update time-qualified context about roles, goals, capabilities, preferences, responsibilities, and current focus.
5. **Ontology alignment** — map records to PDKS concepts, controlled vocabulary, and relationships.
6. **Quality review** — validate structure, references, time, evidence, identity, and governance.
7. **Retrieval** — answer questions from available PDKS records and cite record/source identifiers where possible.
8. **Export** — produce a portable PDKS bundle with manifest and hashes.
9. **Migration** — inspect an export bundle, produce a migration plan, preserve IDs and mappings, and report losses or unsupported features.
10. **Design / extension** — propose changes separately; never silently change the published baseline.

## Seven integrated engines

The engines share one record model and are not separate databases:

- **Capture Engine:** identifies source types, content boundaries, speakers, timestamps, and acquisition context.
- **Event Engine:** identifies what happened, when, where, with whom, and in which context.
- **Knowledge Engine:** extracts assertions, decisions, methods, experiences, cases, principles, lessons, and insights.
- **Personal Context Engine:** models changing personal roles, goals, capabilities, preferences, responsibilities, and current focus.
- **Ontology Engine:** aligns entities, event types, relations, time, and semantic concepts.
- **Governance Engine:** preserves provenance, evidence, confidence, sensitivity, access scope, consent, lifecycle, and correction history.
- **Migration Engine:** packages, validates, exports, imports, maps, and reports portable data.

## Non-negotiable principles

1. **Preserve source material.** Never replace an available original recording, message, document, or transcript with an AI summary. Store a source reference and hash where possible.
2. **Evidence before inference.** Important events, decisions, assertions, and knowledge should link to evidence segments when source material exists.
3. **Event is not Action.** `event` means something happened. `action` means something planned, promised, assigned, or to be done. A completed action may link to a later event.
4. **Assertion is not fact.** Preserve whether a statement is reported, inferred, hypothesized, corroborated, disputed, retracted, or unknown.
5. **Separate roles.** Speaker / person asserting, record creator, source owner, and AI processor are not interchangeable.
6. **Stable identity.** Reuse a known entity ID only when the match is reliable. Similar names do not prove identity.
7. **Time integrity.** Distinguish occurrence time, capture time, record creation time, processing time, and validity period.
8. **Least privilege.** If authorization is unclear, use `owner_only`; never widen access by inference.
9. **Low-friction use.** The agent classifies automatically. Do not ask ordinary users to select codes or fill long forms.
10. **No fabricated metadata.** Never invent IDs from external systems, speakers, timestamps, quotations, source paths, consent, or completion status.
11. **Version everything.** Keep standard, taxonomy, ontology, schema, skill, and export-bundle versions explicit.
12. **Migration must be loss-aware.** Preserve unknown or unsupported fields and report every mapping loss; never silently discard data.

## Canonical data model

PDKS 0.1 defines nine record types:

| `object_type` | Meaning |
|---|---|
| `entity` | Person, organization, project, place, topic, tool, or goal |
| `source_asset` | Original audio, message, email, document, web page, or file |
| `evidence_segment` | A locatable excerpt, message, paragraph, or audio interval |
| `event` | An occurrence that has happened |
| `assertion` | A statement, opinion, hypothesis, intention, decision, question, or estimate |
| `knowledge_asset` | Reusable concept, method, experience, case, procedure, principle, lesson, or insight |
| `personal_context` | Time-qualified role, goal, capability, preference, responsibility, or current focus |
| `action` | Task, plan, commitment, or reminder |
| `relationship` | A qualified relation between two referenced objects |

Every record must conform to `assets/pdks-0.1-record.schema.json`. Do not invent alternative field names or change the PDKS 0.1 payload definitions.

## End-to-end workflow

### A. Inspect and understand the input

1. Identify source type: direct user statement, conversation, chat export, meeting notes, transcript, audio/video, file, email, web page, or existing structured data.
2. Identify whether the content is first-hand, quoted, reported by another person, or inferred by the agent.
3. If a real source file or locator is available, create or reuse a `source_asset`.
4. If no durable source exists, do not fabricate a file. Preserve the user's text as conversation evidence only if the host supports such a reference; otherwise state that the record is based on user-provided text.
5. Do not claim that you have listened to audio, opened a file, or accessed an app unless the host actually provided that content or action.

### B. Extract candidate information

Look for:
- people, organizations, projects, places, topics, tools, and goals (`entity`);
- occurrences that have already happened (`event`);
- directly expressed or inferred statements (`assertion`);
- reusable knowledge candidates (`knowledge_asset`);
- time-qualified personal context candidates (`personal_context`);
- plans, tasks, commitments, and reminders (`action`);
- meaningful relations requiring their own evidence/status/confidence (`relationship`);
- original source material (`source_asset`) and locatable evidence (`evidence_segment`).

Do not force every sentence into every object type. Create only supported records.

### C. Classify and normalize

Use `assets/pdks-event-taxonomy-0.1.json`. Its nine domains are:
`work`, `learning`, `thinking`, `life`, `relationship`, `growth`, `finance`, `health`, `other`.

Set `event_taxonomy_version` to `0.1.0` for event records. If no event code fits, use the taxonomy's `other.unclassified` concept and mark the classification as unresolved / needs review according to the schema. Never invent a code inside a record. Suggest new codes separately as a taxonomy change proposal.

Normalize names, dates, time zones, and aliases without losing the original wording. Keep original text in the source/evidence record.

### D. Resolve entities conservatively

- Reuse existing entities only when evidence supports the match.
- If uncertain, preserve a candidate or unresolved reference; do not merge.
- Do not use `owl:sameAs` until identity is confirmed.
- For uncertain matches, use a candidate relationship / note equivalent to `possibleIdentityMatch`.
- Do not invent a person's legal name, employer, account, external ID, or contact details.

### E. Build the semantic network

Connect:
- event → participants, context entities, evidence, source, outcome;
- assertion → speaker / asserting person, topic, evidence, event;
- knowledge asset → derived-from events, assertions, evidence, applicability and limitations;
- personal context → subject, evidence, confidence, verification status, validity/review policy;
- action → assignee, originating event, due time, dependencies and completion event;
- relationship → subject, predicate, object, evidence, status, confidence.

Use direct payload references where the schema provides them. Use a `relationship` record when the relation itself needs evidence, status, confidence, or lifecycle.

### F. Preserve provenance and epistemic status

Assertion status values:
- `reported`: explicitly expressed in a source;
- `inferred`: inferred by the agent from evidence;
- `hypothesized`: not yet verified;
- `corroborated`: supported by multiple independent sources;
- `disputed`: sources conflict or the statement is challenged;
- `retracted`: explicitly withdrawn or corrected;
- `unknown`: cannot be determined.

Personal context verification values:
- `self_declared`, `confirmed`, `inferred`, `contested`, `expired`.

An inferred personal context must include evidence references. A one-off occurrence is not enough to establish a stable trait. Prefer temporary, time-qualified context over permanent claims.

### G. Apply governance

Every record requires:
- `governance.sensitivity`
- `governance.access_scope`

Sensitivity values:
`personal_private`, `personal_work`, `organization_internal`, `restricted`, `public`.

Access scope values:
`owner_only`, `explicitly_shared`, `organization_authorized`, `public`.

Default to `personal_private` / `owner_only` when the content is private or scope is unclear. For clearly work-related records, `personal_work` may be appropriate, but the access scope still defaults to `owner_only` unless sharing is explicitly authorized. Never assume that work-related content is automatically shareable with an employer or team.

Do not store passwords, credentials, access tokens, or secrets. Do not expose sensitive personal details in summaries unless needed for the user's request.

### H. Validate before presenting or exporting

Run or perform these checks:
1. JSON Schema Draft 2020-12 validation.
2. Required fields, enum values, and date-time format.
3. Event type exists in the pinned taxonomy version.
4. Object IDs are unique in the bundle.
5. References resolve within the bundle or are explicitly marked external/unresolved.
6. Event start is not later than event end.
7. Audio/video evidence locators have valid non-negative ranges.
8. Inferred personal context has evidence.
9. Access scope has not been widened.
10. No plan has been recorded as a completed event.
11. No unsupported or unknown fields are silently dropped during migration.

If scripts or validation libraries are unavailable, do a best-effort review and state that machine validation was not run. Never claim a test passed unless it actually ran.

### I. Present results in a user-friendly way

For ordinary users, present:
1. a short summary of what was captured;
2. important events, decisions, knowledge and actions;
3. any material uncertainty requiring confirmation;
4. whether records were only drafted or actually saved to a connected destination.

Do not expose raw triples, schema internals, or dozens of fields unless the user is a developer or asks for them. Never claim persistent storage unless a connected tool or host confirms the write.

## Daily review workflow

When asked for a daily / weekly review:
1. Retrieve only records available in the current authorized context.
2. Group by date and domain.
3. Separate completed events from open actions.
4. Highlight decisions, unresolved questions, risks, and new knowledge candidates.
5. Show changes in personal context as candidates, not facts, unless confirmed.
6. Include source references or record IDs for important conclusions.
7. Do not invent missing activity or imply that no activity occurred when records are incomplete.

## Knowledge synthesis workflow

1. Find repeated or connected evidence across events and assertions.
2. Distinguish direct facts from interpretations.
3. Draft a `knowledge_asset` with title, summary, content, applicability, limitations, verification status, and `derived_from_refs`.
4. Keep the knowledge asset as `draft` until reviewed or corroborated according to the host's policy.
5. Preserve conflicting evidence and limitations.
6. Do not convert an opinion into organizational policy or universal truth.

## Personal context workflow

1. Create context only when it will materially improve future assistance.
2. Use a narrow context type and concise value.
3. Include subject, verification status, confidence, evidence references, and review policy.
4. Add validity dates when known; do not invent them.
5. Prefer `inferred` + `suggest_update` for AI-derived context.
6. Ask for confirmation before treating a high-impact or sensitive context as stable.
7. Allow correction, expiry, and retraction.

## Retrieval workflow

1. Search only connected / supplied PDKS records and authorized sources.
2. Distinguish “not found in available records” from “does not exist”.
3. Use evidence and provenance to support answers.
4. When sources conflict, report the conflict and dates rather than silently choosing one.
5. Avoid treating an old personal context as current if its validity has expired or is unknown.
6. Do not infer sensitive traits.

## Export and migration workflow

For export:
1. Include all requested records and only authorized source assets.
2. Preserve object IDs, references, timestamps, taxonomy and schema versions, provenance, governance, lifecycle, and unknown extensions.
3. Include schema, taxonomy, ontology, mapping, a manifest, file hashes, and export metadata.
4. Validate the bundle and report counts, unresolved references, and exclusions.
5. Never include credentials or unauthorized source files.

For migration:
1. Inspect the source bundle and verify hashes.
2. Build a source-to-target mapping plan before writing.
3. Preserve original IDs; if target IDs must change, include an explicit ID map.
4. Preserve unsupported fields in an extension / raw payload area where possible.
5. Do not widen access scope; if the target cannot represent a permission, apply the stricter scope and flag it.
6. Report successful, skipped, transformed, and unresolved records separately.
7. Do not claim destination import succeeded unless the destination tool confirms it.

## Host-agent tool contract

This Skill does not itself grant app access, memory, file-system access, recording, scheduling, or database write permissions.

When host tools exist:
- use only authorized connectors and tools;
- obtain user confirmation for consequential writes, sharing, deletion, or external publication when required by the host;
- prefer read-before-write and idempotent writes;
- use stable object IDs to prevent duplicate records;
- return a write receipt or destination reference when available.

When no tools exist:
- provide structured records or a portable bundle as an artifact;
- clearly say that records have been generated but not saved to a persistent store.

## Reference routing

Read the smallest relevant reference:
- `references/00-quickstart.md`
- `references/01-core-model.md`
- `references/02-capture-pipeline.md`
- `references/03-event-and-knowledge.md`
- `references/04-personal-context.md`
- `references/05-ontology-and-taxonomy.md`
- `references/06-trust-privacy-governance.md`
- `references/07-validation-and-quality.md`
- `references/08-migration-protocol.md`
- `references/09-agent-adapter-contract.md`
- `references/10-user-interaction-patterns.md`
- `references/11-transition-stage-and-capability-boundaries.md` (mandatory maturity / capability boundary)
- `references/12-personal-enterprise-center-ontology-extension-proposal.md` (research proposal only)
- `references/ontology-first-architecture.md`

Canonical machine resources:
- `assets/pdks-0.1-record.schema.json`
- `assets/pdks-event-taxonomy-0.1.json`
- `assets/pdks-core-ontology-0.1.ttl`
- `assets/pdks-core-shapes-0.1.ttl`
- `assets/pdks-core-vocabularies-0.1.ttl`
- `assets/pdks-json-to-ontology-mapping-0.1.json` (legacy mapping)
- `assets/ontology/0.2.1/` (current ontology modules, vocabulary, SHACL, JSON-LD context, migration map and SHA-256 manifest)

Scripts:
- `scripts/validate_records.py`
- `scripts/build_bundle.py`
- `scripts/verify_bundle.py`
- `scripts/export_graph.py`
- `scripts/plan_migration.py`
- `scripts/validate_ontology.py`
- `assets/ontology/0.2.1/`
- `scripts/search_records.py`
- `scripts/daily_review.py`
- `scripts/pdks_ontology_runtime.py`
- `scripts/pdks_ontology_sqlite.py`
- `scripts/pdks_ontology_cli.py`
- `scripts/pdks_ontology_governance.py`
- `scripts/build_ontology_manifest.py`
- `scripts/validate_skill_stage.py`

## Completion criteria

A capture task is complete only when:
- supported records have been drafted;
- source and evidence links are preserved where available;
- uncertainty is explicit;
- governance defaults are applied;
- validation status is accurately reported;
- the user knows whether records were saved or only prepared.

A migration task is complete only when:
- source bundle integrity is checked;
- a mapping plan is produced;
- data loss and unresolved references are reported;
- destination success is confirmed by the host, or the task is explicitly marked as a prepared migration package.


## Personal Capture Runtime integration

When a PDKS Runtime endpoint or host adapter is explicitly available, use it as the only persistence boundary. Never write directly to its SQLite database or raw file vault. Submit captured materials and candidate records through the documented adapter, preserve source IDs and consent references, and distinguish `candidate` from owner-approved records. If no Runtime tool/endpoint is available, analyze only the material actually supplied and return a prepared export rather than claiming automatic capture or persistence. Runtime 0.1.0 is a local experimental prototype; read `references/13-personal-capture-runtime.md` for its limitations.


## File-first Vault storage contract (0.5.2 architecture baseline)

Portable knowledge assets target Markdown + YAML Frontmatter; source and evidence records target JSONL; original attachments target SHA-256 content-addressed files. SQLite is a rebuildable index/runtime layer, not the sole knowledge asset store. Use stable `pdks_id` values and relative Markdown links. Obsidian is an optional viewer that can open the PDKS Vault folder directly; do not make Wikilinks or plugin fields the only representation of relationships.

The current Runtime FileFirstVault 0.1.0 is a one-way projection adapter, not yet the authoritative transactional file store. Never claim continuous bidirectional synchronization or full operational database reconstruction. Preserve source provenance and user edits; do not silently overwrite Markdown notes.
