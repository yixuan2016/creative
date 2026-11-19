# Benchmark Candidate Output Contract

Each host returns one UTF-8 JSON file per case/run:

```json
{
  "benchmark_id": "PDKS-XA-0.4.3",
  "case_id": "C01-meeting-event-decision-action",
  "run_id": "hostA-C01-001",
  "host": {
    "name": "actual host",
    "version": "actual version",
    "model": "actual model/version",
    "skill_version": "0.3.3",
    "skill_package_sha256": "actual package SHA-256",
    "tool_profile": ["only tools actually available"]
  },
  "records": [],
  "answer_summary": "brief natural-language explanation",
  "uncertainty_notes": [],
  "capability_claims": []
}
```

Rules:
- `records` contains canonical PDKS 0.1.x records.
- `uncertainty_notes` lists unresolved speaker, date, identity, source conflict or low-confidence inference.
- Capability statuses must use the PDKS vocabulary: available_in_skill, prototype_local, prototype_partial, host_dependent, not_implemented, future_research.
- No raw personal source material in public outputs.
- Machine pass is not a semantic pass; human review is mandatory.
