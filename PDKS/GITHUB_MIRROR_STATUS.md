# PDKS 0.5.3 GitHub Mirror Status

Last updated: 2026-11-20  
Repository: https://github.com/yixuan2016/creative/tree/main/PDKS  
Development stage: `transitional_skill_development`  
Maturity: Experimental / Preview

## Current state
The GitHub project home and component entrypoints are committed. The full 0.5.3 archive has **not** yet been expanded file-by-file into this repository. Do not treat this directory as a complete source mirror.

## Canonical local archive
- File: `PDKS_0.5.3_完整综合工程包.zip`
- Size: 1,821,997 bytes
- ZIP entries: 374
- SHA-256: `ad44f84d4be5749492c89d2fc3a91a0ae88ba3e75ddda96208cd1e4884b4cbc4`
- The archive is locally CRC-checked and its embedded per-file SHA-256 inventory was verified.
- The archive has not been uploaded as a GitHub Release asset.

## What is already committed
Project entrypoint, stage declaration, roadmap, release notes, validation report, docs index, Agent Bridge package metadata/README, PDKS Setup Skill, and module entrypoints for standards, runtime, connectors, installer, storage, tests, examples and releases.

## Remaining full-mirror scope
- Personal Knowledge Skill references, scripts, benchmarks and ontology assets.
- Ontology 0.2.1 TTL, JSON-LD context, mappings, migration maps, SHACL and manifest.
- Full Node Agent Bridge source, MCP server and MCP Apps UI.
- Python Capture Runtime, DWS connector and File-first adapter.
- Architecture/user documentation in Markdown, HTML and DOCX.
- Examples, fixtures, automated tests and historical release artifacts.

## Safe local synchronization
Use `tools/sync-release.py` from a local clone of this repository. It verifies the archive SHA-256, ZIP integrity, path traversal safety and embedded file hashes before copying into `PDKS/`. It defaults to a dry run. Use `--apply` to stage files and `--push` only after reviewing the Git diff. It never reads or uploads a personal Vault, credentials, .env files, node_modules, build output or runtime data.

## Validation and safety
The local archive validation is not equivalent to a GitHub mirror validation. npm build, MCP Inspector, host-by-host compatibility and real DWS tenant integration remain unexecuted. The Vault is not encrypted at rest; use synthetic or non-sensitive data only.
