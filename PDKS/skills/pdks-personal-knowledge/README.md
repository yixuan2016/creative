# PDKS Personal Knowledge — Transitional Agent Skill 0.3.4

**Runtime track:** 0.5.0  
**Maturity:** Experimental / Preview  
**Current stage:** Transitional Skill development  
**PDKS standard:** 0.1.0  
**Record Schema:** 0.1.x  
**Ontology baseline:** 0.2.1 (frozen)

## What this package is

A portable Agent Skill and machine-readable semantic contract for turning user-provided work and life materials into traceable PDKS records. It can optionally integrate with a separate PDKS Personal Capture Runtime when a host adapter is actually configured.

## What it is not

It is not a recorder, DingTalk connector, always-on agent, cloud memory service, production data platform, or Personal Assistant OS. Installing the Skill does not grant access to connected apps, device sensors, persistent storage, or background execution.

## Runtime separation

- Skill 0.3.4: portable instructions and semantic rules.
- Capture Runtime 0.1.0: separate local reference software in the full PDKS 0.5.0 engineering package.
- Host Adapter: host-specific tool bridge; not automatically installed by the Skill.

## Install

Copy the complete `pdks-personal-knowledge` folder into the Agent host's supported Skills directory and reload the host. For hosts without Agent Skills folder support, provide `SKILL.md` and referenced resources as project instructions or knowledge files.

## References

- `references/11-transition-stage-and-capability-boundaries.md`
- `references/13-personal-capture-runtime.md`
- `references/ontology-first-architecture.md`
- `benchmarks/CROSS_AGENT_TEST_PROTOCOL.md`
- `benchmarks/EVALUATION_RUBRIC.md`

PDKS standard, record schema, Ontology and Event Taxonomy remain frozen in this release.
