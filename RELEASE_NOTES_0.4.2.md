# PDKS 0.4.2 — Transitional Skill Engineering Edition

## Release intent

This is an experimental transitional-stage Skill development release. It advances the Agent Skill package and makes maturity, host capability, and future ontology-layering boundaries explicit. It does not claim production readiness.

## Version matrix

- Runtime development track: 0.4.2
- Agent Skill: 0.3.2
- PDKS Standard: 0.1.0 (unchanged)
- JSON Record Schema: 0.1.x (unchanged)
- Ontology: 0.2.1 (frozen)
- Event Taxonomy: 0.1.0 (unchanged)

## Changes

1. Added mandatory transitional-stage declaration.
2. Added machine-readable stage profile and capability claim policy.
3. Added explicit distinction between Skill-native, local prototype, partial prototype, host-dependent, unimplemented, and future-research capabilities.
4. Added personal / enterprise / center ontology extension proposal without changing stable Ontology terms.
5. Added stage validator and regression tests.
6. Added release document describing stage boundaries and next-stage exit criteria.

## Not included

Native DingTalk or recorder integrations; background capture; production consent, identity, encryption, key-management or cloud-persistence services; enterprise / center ontology runtime; cross-scope data sharing; a final personal digital foundation product.

## Validation

The 0.4.1 baseline was re-run before changes: 27 tests, 26 passed, 1 skipped because pySHACL was not installed locally. The 0.4.2 package adds stage-contract tests. Final local result: 31 tests, 30 passed, 1 skipped for the same optional pySHACL dependency. GitHub Actions results are not claimed until the workflow runs.
