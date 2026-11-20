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
- ZIP CRC and every manifest file hash verified locally.

## GitHub status
The project entrypoints, mirror tooling, tests, workflow and Agent execution prompt are committed. The full release source tree has **not yet** been expanded file-by-file in GitHub. Do not report a full source mirror until the local synchronization workflow has run and the GitHub tree has been compared with the manifest.

## Full mirror procedure
1. Clone `https://github.com/yixuan2016/creative.git`.
2. Place the release ZIP on the same machine.
3. Follow `docs/AGENT_MIRROR_EXECUTION_PROMPT.md` with Codex or WorkBuddy, or run `tools/sync-release.py`.
4. Run dry-run first; then `--apply` only after user approval.
5. Inspect the staged diff; obtain a separate approval before commit/push.
6. Verify the actual GitHub tree and all manifest hashes after push.

## Validation
- 8 safety unit tests passed.
- Dry-run and apply integration tests passed in a temporary Git repository; only `PDKS/` was staged.
- ZIP CRC and 378 manifest-file hashes passed.
- npm build, MCP Inspector, host-by-host Agent validation, cross-platform installation and live DWS tenant integration remain unexecuted.
- Vault files are not encrypted at rest. Use synthetic or non-sensitive data only.
