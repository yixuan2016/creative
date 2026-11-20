# PDKS Full GitHub Mirror Runbook

1. Clone `https://github.com/yixuan2016/creative.git`; ensure the worktree is clean.
2. Use Python 3.10+ and the PDKS 0.5.3.1 ZIP.
3. Dry run:
```bash
python PDKS/tools/sync-release.py --archive "/path/to/PDKS_0.5.3.1_完整综合工程包.zip" --repo "/path/to/creative"
```
4. After user approval, apply:
```bash
python PDKS/tools/sync-release.py --archive "/path/to/PDKS_0.5.3.1_完整综合工程包.zip" --repo "/path/to/creative" --apply
git diff --cached --stat
git diff --cached --name-status
```
5. After separate user approval, push:
```bash
python PDKS/tools/sync-release.py --archive "/path/to/PDKS_0.5.3.1_完整综合工程包.zip" --repo "/path/to/creative" --apply --push
```

The script checks ZIP CRC, manifest sizes and SHA-256; rejects path traversal, Windows separators, symlinks and oversized archives; excludes credentials, personal data, backups, caches and build output. It never force-pushes or accesses a personal Vault. This is an experimental transition-stage release; the Vault is not encrypted at rest.
