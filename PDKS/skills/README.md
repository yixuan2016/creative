# PDKS Agent Skills

## Technical and acceptance specifications

- [PDKS Agent Skills Technical Specification V1.0](PDKS-SKILL-SPEC-001-Agent-Skills技术规范-V1.0.md) — Skill package structure, tool contracts, permission tiers, execution modes, host compatibility and release governance.
- [PDKS Agent Skills Acceptance Matrix V1.0](PDKS-SKILL-ACCEPTANCE-001-Agent-Skills验收矩阵-V1.0.md) — common acceptance gates, skill maturity, security requirements and test evidence.

Both documents are review drafts. Skill maturity must be tracked per capability and backed by tests; a planned Skill must not be described as implemented.

## Current Skills

- `pdks-setup/`: Agent-native environment diagnosis, plan, approval, initialization and verification.
- `pdks-personal-knowledge/`: referenced by the release standards as the broader personal-knowledge workflow; verify the exact release bundle, version and test evidence before treating it as present in the GitHub source mirror.

Skills do not grant host permissions, connectors, filesystem access or persistent storage by themselves. Read each Skill's stage and capability boundary before claiming an operation is available.
