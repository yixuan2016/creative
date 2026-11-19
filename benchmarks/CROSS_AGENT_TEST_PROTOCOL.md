# Cross-Agent Host Validation Protocol

## Goal

Verify the same PDKS Skill package can be loaded by more than one Agent host and that outputs preserve equivalent core semantics and governance boundaries.

## Preconditions

- Use the exact same Skill package for all hosts.
- Pin PDKS 0.1.0, JSON Schema 0.1.x, Ontology 0.2.1, Event Taxonomy 0.1.0.
- Disable unrelated memory or external connectors for baseline tests, or document them.
- Use only the synthetic benchmark cases.
- C12 must run without DingTalk, recorder, or persistence tools.

## Run sequence

1. Record host/model details and tool permissions.
2. Install Skill 0.3.3 and confirm referenced assets are readable.
3. Give the Agent only `prompts/<case_id>.md`; never expose evaluator labels in `cases/<case_id>.json`.
4. Run all 12 cases, repeating each three times in independent sessions.
5. Collect the output envelope defined in OUTPUT_CONTRACT.md.
6. Store raw outputs outside the public repository; publish sanitized outputs and hashes only.
7. Run the structural evaluator.
8. Have reviewers score semantic dimensions using EVALUATION_RUBRIC.md.
9. Record failures, remediation and re-runs.

## Evidence for a cross-host claim

Host/model versions, Skill package SHA-256, case-set version/hash, tool capability matrix, output hashes, machine checks, human scores and failure analysis are required. Without these, say "protocol prepared" or "single-host validation"; do not say "cross-agent validation passed".

## Privacy

Do not commit personal transcripts, raw voice recordings, employee names, private chats, tokens or production data. Real pilots require explicit participant authorization and minimized evidence.
