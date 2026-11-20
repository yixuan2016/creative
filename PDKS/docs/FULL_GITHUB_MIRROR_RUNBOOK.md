# PDKS Full GitHub Mirror Runbook

## Preconditions
- A local clone of `https://github.com/yixuan2016/creative.git`.
- The PDKS 0.5.3.1 ZIP.
- Python 3.10+ and Git; Git authentication already configured.

## 1. Dry run
```bash
python PDKS/tools/sync-release.py --archive "/path/to/PDKS_0.5.3.1_完整综合工程包.zip" --repo "/path/to/creative"
```
No files are written. The script checks ZIP CRC, safe paths, symlinks, manifest sizes and SHA-256.

## 2. Apply and inspect
```bash
python PDKS/tools/sync-release.py --archive "/path/to/PDKS_0.5.3.1_完整综合工程包.zip" --repo "/path/to/creative" --apply
git diff --cached --stat
git diff --cached --name-status
```

## 3. Push only after reviewing
```bash
python PDKS/tools/sync-release.py --archive "/path/to/PDKS_0.5.3.1_完整综合工程包.zip" --repo "/path/to/creative" --apply --push
```

## Safety
Writes only under `creative/PDKS/`; does not read or upload a personal Vault; excludes credentials, .env, personal runtime data, backups, dependency caches and build outputs; rejects path traversal, Windows separators and symlinks; never force-pushes. The PDKS Vault is not encrypted at rest. This remains an experimental transition-stage release.
