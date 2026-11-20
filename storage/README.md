# PDKS Storage

File-first user-owned Vault:
- Markdown + YAML Frontmatter: readable knowledge assets.
- JSON/JSONL: source, evidence and machine-exchange records.
- Content-hash addressed files: original attachments.
- SQLite: rebuildable index / optional Runtime operational store in current preview.

The current File Store Adapter 0.1.0 is a one-way Runtime-to-Vault projection. It is not the authoritative transactional file store and does not provide bidirectional sync. Vault files are not encrypted at rest in this preview.
