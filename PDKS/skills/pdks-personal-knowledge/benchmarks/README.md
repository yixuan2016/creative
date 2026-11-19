# PDKS Cross-Agent Benchmark 0.1.0

This benchmark is part of the **transitional Skill development** track. It is a test harness, not a production certification.

## Contents
- `prompts/`: agent-facing prompts only. Do not expose evaluator labels to the tested Agent.
- `cases/`: evaluator-side acceptance criteria and critical failures.
- `fixtures/`: evaluator smoke-test inputs.
- `benchmark-manifest.json`: version and run requirements.
- `CROSS_AGENT_TEST_PROTOCOL.md`: host setup and execution process.
- `BENCHMARK_RUNNER_GUIDE.md`: exact run isolation and prompt handling.
- `OUTPUT_CONTRACT.md`: candidate result JSON envelope.
- `EVALUATION_RUBRIC.md`: human scoring rubric and critical-failure rules.
- `host-run-matrix.csv`: host capability metadata.
- `run-results-template.csv`: 72 planned run slots (2 hosts × 12 cases × 3 repeats).
- `review-scorecard-template.csv`: per-run human scorecard.

## Important status
The 12 synthetic cases and protocol are prepared. Actual cross-host runs have not yet been executed. Do not claim cross-agent validation passed until outputs from at least two real hosts are collected, machine-checked, and human-reviewed.
