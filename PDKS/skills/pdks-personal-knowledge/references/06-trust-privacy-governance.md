# Trust, Privacy and Governance

## Governance dimensions
Sensitivity and access scope are independent:
- sensitivity: what kind of information is this?
- access scope: who is allowed to access it?

Sensitivity:
`personal_private`, `personal_work`, `organization_internal`, `restricted`, `public`.

Access scope:
`owner_only`, `explicitly_shared`, `organization_authorized`, `public`.

## Default
If unclear, use the narrowest scope, normally `owner_only`. Work-related information may be marked `personal_work` but must not automatically be shared with the organization.

## Consent
Record the relevant consent / authorization reference when a source or destination requires it. Never infer consent from mere availability of a connector or file.

## Data minimization
Capture only information relevant to the user's purpose. Avoid storing passwords, tokens, credentials, unnecessary third-party personal details, or sensitive traits.

## Provenance
Retain:
- original source reference;
- source creator/author/speaker when known;
- record creator;
- processing agent/model/version when available;
- processing time and transformations where available;
- evidence locators and content hashes.

## Lifecycle
Use lifecycle states supported by the schema:
`active`, `archived`, `superseded`, `retracted`, `deleted_tombstone`, `unresolved`.

Never silently overwrite material corrections. Use versioning and supersedes references where possible.

## User rights and corrections
If the user says a record is wrong:
1. identify the affected record and source;
2. correct only the supported fields;
3. preserve a revision trail where available;
4. mark disputed/retracted claims as appropriate;
5. do not repeat a retracted inference as current context.

## Third-party data
Do not expose a third party's private information in user-facing summaries unless needed. Keep access scope and lawful basis aligned with host policy and applicable organizational rules.
