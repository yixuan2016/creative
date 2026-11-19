# Cross-Agent Host Validation Protocol

## 1. Goal

Verify the same PDKS Skill package can be loaded and used by more than one Agent host, and that outputs preserve the same core semantics and governance boundaries.

## 2. Preconditions

- Use the exact same Skill ZIP / extracted Skill folder for all hosts.
- Pin PDKS standard 0.1.0, JSON Schema 0.1.x, Ontology 0.2.1, Event Taxonomy 0.1.0.
- Disable unrelated memory or external connectors for the baseline test, or document them.
- Do not supply real personal data. The packaged cases are synthetic.
- Ensure the host is not granted tools it should not have for C12.

## 3. Run sequence

For each host:
1. Record host and model details in `host-run-matrix.csv`.
2. Install the Skill using the host's supported method.
3. Confirm the host can read `SKILL.md`, stage-boundary reference, record schema, taxonomy, and ontology references.
4. Run all 12 case prompts exactly as supplied.
5. Repeat each case three times in fresh sessions to measure variability.
6. Give the tested Agent only `prompts/<case_id>.md`; do not expose evaluator metadata in `cases/<case_id>.json`.
7. Ask the host to produce the evaluation output envelope described in `OUTPUT_CONTRACT.md`.
8. Save raw outputs outside the public repository; publish only sanitized outputs and hashes.
9. Run `scripts/evaluate_benchmark.py` against each candidate output.
10. Two reviewers independently score semantic dimensions where feasible.
11. Record failures, root causes, remediation, and re-run results.

## 4. Fairness controls

- Same input prompt and same Skill release.
- Same tool permissions for comparable tests.
- No hidden access to external personal data.
- If host tool capabilities differ, mark them as different test conditions, not as model quality differences.
- Record prompt wrapping or system instructions that differ by host.
- Do not normalize away meaningful differences in privacy or uncertainty handling.

## 5. Evidence required for a valid cross-host claim

A report must include:
- host and model identity/version;
- Skill version and package hash;
- case set version and hash;
- run count and timestamps;
- tool/connector capability matrix;
- raw output hashes and sanitized artifacts;
- machine validation results;
- reviewer rubric scores;
- critical failures and unresolved issues.

Without these records, say "test protocol prepared" or "single-host local validation"; do not say "cross-agent validation passed."

## 6. Privacy and publication

Do not commit personal transcripts, raw voice recordings, employee names, private chats, tokens, or production data. Public benchmark cases remain synthetic. If a real pilot is later conducted, obtain explicit participant authorization and publish only minimized, sanitized evaluation evidence.
