# PDKS 0.5.2.1 Validation Report

Date: 2026-11-19  
Stage: transitional_skill_development  
Maturity: experimental / preview

## Automated tests

| Suite | Total | Passed | Skipped | Failed |
|---|---:|---:|---:|---:|
| Skill | 53 | 52 | 1 | 0 |
| Prototype | 33 | 32 | 1 | 0 |
| Runtime + DWS + File Store | 64 | 64 | 0 | 0 |
| **Total** | **150** | **148** | **2** | **0** |

The two skipped tests are pre-existing optional-dependency checks for pySHACL.

## Additional checks

- Python compileall: passed.
- Stage validator: 12/12, status valid.
- Ontology 0.2.1: valid, runtime terms referenced 98 / declared 98.
- Ontology manifest: 8 files valid.
- CLI integration with synthetic data: passed:
  1. initialize runtime owner;
  2. capture synthetic text;
  3. initialize PDKS Vault;
  4. project source and evidence plus original attachment;
  5. verify PDKS-MANIFEST hashes;
  6. rebuild the separate file index; SQLite integrity check `ok`.
- Sample Vault manifest: 6 portable files verified; relative links resolve within the Vault.
- ZIP CRC and per-file manifest hashes are checked at packaging time.

## Scope and limitations

This is not production readiness. FileFirstVault 0.1.0 is a one-way projection adapter. The current CaptureRuntime operational database remains authoritative. The rebuilt SQLite is only a disposable file index; it cannot restore consent, API tokens, DWS cursors, or complete audit/runtime state.

Not implemented: transactional outbox, capture-time file-first writes, bidirectional Obsidian reconciliation, conflict merge UI, static encryption, OS keychain, multi-device sync, native Node.js installer, real DWS tenant delivery, and Codex / WorkBuddy host validation.

Do not use this preview for sensitive personal or enterprise data until encryption and key management are implemented and reviewed.
