# PDKS GitHub Mirror Status

Last updated: 2026-11-20  
Repository: https://github.com/yixuan2016/creative/tree/main/PDKS  
Stage: `transitional_skill_development` · Maturity: Experimental / Preview

## Canonical release archive
- Version: PDKS 0.5.3.1 (mirror tooling and path-safety enhancement)
- File: `PDKS_0.5.3.1_完整综合工程包.zip`
- Size: 1,828,128 bytes
- SHA-256: `56e2245bf8d39028406ecc6b6cdb38dba0a7e8fdc9eec5e9bed212cea82da7bf`
- ZIP entries: 379; manifest-listed files: 377.
- ZIP CRC and every manifest file hash verified.

## What this GitHub folder means
The project entrypoints and mirror tooling are committed. The full release source tree is still not expanded file-by-file in GitHub. Do not claim a complete GitHub source mirror until the local sync workflow is run and the resulting GitHub tree is compared against the manifest.

## Full mirror procedure
1. Clone `https://github.com/yixuan2016/creative.git`.
2. Put the release ZIP on the same machine.
3. Run `python PDKS/tools/sync-release.py --archive <zip> --repo <creative-clone>` (dry-run).
4. Run again with `--apply`, then inspect `git diff --cached --stat` and `git diff --cached --name-status`.
5. Only after review, run with `--apply --push`.

The script rejects traversal, Windows path separators, symlinks, oversized archives and unsafe paths; checks ZIP CRC and per-file manifest hashes; and excludes credentials, personal data folders, build output and dependency caches.

## Validation
- 8 safety unit tests passed.
- Dry-run and apply integration tests passed in a temporary Git repository; only `PDKS/` was staged.
- Archive CRC and 377 manifest-file hashes passed.
- npm build, MCP Inspector, host-by-host Agent validation, cross-platform install and live DWS tenant integration remain unexecuted.
- Vault files are not encrypted at rest. Use synthetic or non-sensitive data only.
