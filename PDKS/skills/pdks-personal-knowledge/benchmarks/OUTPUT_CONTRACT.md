# Benchmark Candidate Output Contract

A host Agent should return one UTF-8 JSON file per case/run, with this envelope:

```json
{
  "benchmark_id": "PDKS-XA-0.4.3",
  "case_id": "C01-meeting-event-decision-action",
  "run_id": "hostA-C01-001",
  "host": {
    "name": "record actual host",
    "version": "record actual version",
    "model": "record actual model/version",
    "skill_version": "0.3.3",
    "skill_package_sha256": "actual package SHA-256",
    "tool_profile": ["only tools actually available"]
  },
  "records": [],
  "answer_summary": "brief natural-language explanation",
  "uncertainty_notes": [],
  "capability_claims": [
    {
      "capability": "connector or action",
      "status": "host_dependent",
      "evidence": "what tool or execution receipt supports this status"
    }
  ]
}
```

Rules:
- `records` contains canonical PDKS 0.1.x records, not an invented parallel schema.
- `uncertainty_notes` explicitly list unresolved speakers, dates, identity, source conflict, or low-confidence inference.
- `capability_claims.status` must be one of: `available_in_skill`, `prototype_local`, `prototype_partial`, `host_dependent`, `not_implemented`, `future_research`.
- Do not put raw personal source material in public output files.
- The evaluator is a structural gate. Human review remains required for semantic correctness, helpfulness, and nuanced safety.
