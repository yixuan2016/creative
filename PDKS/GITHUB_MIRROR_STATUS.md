# PDKS 0.5.3 GitHub Mirror Status

Last updated: 2026-11-20  
Repository: https://github.com/yixuan2016/creative/tree/main/PDKS  
Development stage: `transitional_skill_development`  
Maturity: Experimental / Preview

## Important distinction
The GitHub directory is an actively populated project home, but it does **not yet mirror every file** from the complete local release archive. Do not treat the GitHub tree as a complete source mirror yet.

## Local release archive
- File: `PDKS_0.5.3_完整综合工程包.zip`
- Size: 1,821,997 bytes
- ZIP entries: 374
- SHA-256: `ad44f84d4be5749492c89d2fc3a91a0ae88ba3e75ddda96208cd1e4884b4cbc4`
- The archive contains the full project source, Skills, ontology assets, runtime, docs, examples, tests and reports.
- It has not been uploaded as a GitHub Release asset.

## Current GitHub contents
Project entrypoint, stage declaration, roadmap, release notes, validation report, documentation index, Agent Bridge package metadata and README, PDKS Setup Skill, and component directory entrypoints for standards, Skills, runtime, connectors, installer, storage, tests, examples and releases.

## Remaining synchronization work
The full Personal Knowledge Skill and its references/scripts/benchmarks/assets; Ontology 0.2.1 TTL, JSON-LD, mapping, migration and SHACL assets; complete Node Agent Bridge source and MCP Apps UI; Python Capture Runtime and DWS connector; all architecture/user docs in Markdown/HTML/DOCX; examples, test fixtures, automated suites and historical release manifests still need file-by-file mirroring.

## Validation and safety
The local archive passed ZIP CRC and per-file manifest hash verification. This does not mean the GitHub mirror is complete. The 0.5.3 report records 160 passed, 2 skipped and 0 failed automated tests; npm build, MCP Inspector, host-by-host validation and real DWS tenant integration remain unexecuted.

Vault files are not encrypted at rest. Use synthetic or non-sensitive data only.
