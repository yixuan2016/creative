# PDKS 0.5.1.2 Validation Report

> Stage: transitional Skill development · Experimental / Preview

## 1. Automated regression

| Suite | Tests | Passed | Skipped | Failed |
|---|---:|---:|---:|---:|
| Runtime + DWS Connector | 57 | 57 | 0 | 0 |
| Skill / Setup / release regression | 53 | 52 | 1 | 0 |
| ADS / Ontology prototype | 33 | 32 | 1 | 0 |
| **Total** | **143** | **141** | **2** | **0** |

Two tests were skipped because pySHACL is unavailable in this local environment. CI installs `requirements-dev.txt`, including pySHACL, but GitHub Actions has not yet been run for this release.

## 2. Stage and Ontology

- Transitional-stage validator: 12/12, valid.
- Ontology 0.2.1: valid.
- Runtime ontology terms referenced/declared: 98/98.
- Controlled vocabulary codes: 67 present; all 54 required codes present.
- Event taxonomy codes: 72 present.
- Ontology manifest: 8/8 files verified.
- No PDKS Ontology version change in this release.

## 3. Bootstrap Engine

- `doctor` executed in the current Linux environment: `ready`.
- macOS/Linux shell wrapper syntax and `doctor` execution passed.
- `plan` executed and produced deterministic SHA-256 approval token.
- Unit tests cover plan determinism, current-user path restriction, non-empty directory protection, explicit plan approval, storage-risk acknowledgement, shell-free subprocess calls, atomic staging rollback, and a full local install fixture.
- Full local install fixture completed initialization, launcher creation, SQLite creation and health verification. The fixture supplied a test-only dependency stub to avoid network access; it does not prove PyPI dependency resolution.
- A real PyPI install attempt was blocked because this execution environment has no DNS/network access. Atomic rollback was verified: final target remained absent and no staging directory remained.

## 4. DWS P0 security repair

- `dws-consume` calls preflight before starting the stream.
- Consent, positive authentication, indeterminate reason, token validity, local-state repair/readability, exact profile, and non-empty event schema are checked.
- Tests assert that consumer start is not called if preflight fails.
- Real DWS account / tenant event delivery was not tested; actual CLI output and tenant permissions still require user-environment acceptance.

## 5. Product boundaries

This release installs only an experimental local Runtime. It does not enable data collection, install DWS automatically, perform OAuth login, subscribe to events, import historical data, register a background service, configure cloud backup, or modify Agent-specific Skill directories.

Capture Runtime 0.1.1 does not encrypt SQLite or Vault at rest. User-level directory permissions are not encryption. Do not collect sensitive work or personal data with this preview.

## 6. Cross-agent status

- Codex local: protocol documented; real host installation not executed.
- WorkBuddy desktop: protocol documented; real host installation not executed.
- Claude Code / other Agents: generic capability contract documented; host-specific installation not executed.
- Cloud-only Agents are guidance-only unless an explicit local execution bridge exists.

## 7. Conclusion

PDKS 0.5.1.2 now contains an Agent-neutral installation protocol, an executable local Bootstrap Engine, user confirmation bound to a deterministic plan hash, and DWS subscription preflight fixes. It is an experimental local install prototype, not yet a one-click commercial installer or a production-safe personal data collection service.
