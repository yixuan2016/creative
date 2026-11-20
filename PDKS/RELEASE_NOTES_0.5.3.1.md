# PDKS 0.5.3.1 — Mirror Safety Enhancement

- Added safe local full-release mirror tool.
- Added dry-run / apply / explicit push workflow.
- Added ZIP CRC and per-file SHA-256 validation.
- Rejects path traversal, Windows path separators, symlinks and oversized archives.
- Excludes personal Vault data, credentials, dependency caches and build output.
- Added 8 safety unit tests and GitHub Actions test workflow.

This is a tooling patch in the transitional Skill development stage, not a production Personal AI Life OS release.
