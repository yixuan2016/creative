# PDKS GitHub Mirror Status

Last updated: 2026-11-20  
Repository: https://github.com/yixuan2016/creative/tree/main/PDKS  
Stage: `transitional_skill_development` · Maturity: Experimental / Preview

## Canonical release archive
- Version: PDKS 0.5.3.1 (mirror tooling and path-safety enhancement)
- File: `PDKS_0.5.3.1_完整综合工程包.zip`
- Size: 1,829,965 bytes
- SHA-256: `1a67e8f296b81e8aeb381c43afeaf7aa64a3141a3bf15391f4d0fe47d186b4ea`
- ZIP entries: 380; manifest-listed files: 378.
- ZIP CRC and all manifest hashes verified locally.

## GitHub status
Project entrypoints, mirror tooling, tests, workflow and Agent execution prompt are committed. The full source tree has not yet been expanded file-by-file in GitHub. Do not claim full mirror completion until local sync and remote manifest verification are done.

## Procedure
Use `docs/AGENT_MIRROR_EXECUTION_PROMPT.md` with Codex/WorkBuddy or follow `docs/FULL_GITHUB_MIRROR_RUNBOOK.md`. Dry-run first, apply after approval, inspect staged diff, obtain separate approval before push, then verify the remote tree and manifest.

## Validation
8 safety tests passed. Dry-run/apply integration tests passed in a temporary Git repository; only PDKS was staged. npm build, MCP Inspector, host compatibility, cross-platform install and live DWS integration remain unexecuted. Vault is not encrypted at rest; use synthetic or non-sensitive data only.
