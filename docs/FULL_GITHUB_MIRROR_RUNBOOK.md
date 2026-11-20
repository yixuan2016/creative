# PDKS Full GitHub Mirror Runbook

## Why this step is needed
The GitHub connector can commit text blobs and trees, but the complete release is a ZIP archive containing hundreds of source and binary/document artifacts. This runbook uses the user's local Git checkout to expand the verified archive and push the complete tree without moving the archive through chat or exposing credentials.

## Preconditions
- A local clone of `https://github.com/yixuan2016/creative.git`.
- The verified `PDKS_0.5.3_完整综合工程包.zip`.
- Python 3.10+ and Git installed.
- User has already authenticated Git with their preferred credential manager.

## 1. Dry run
From the local creative clone:

```bash
python PDKS/tools/sync-release.py --archive "/path/to/PDKS_0.5.3_完整综合工程包.zip" --repo "/path/to/creative"
```

The script verifies the fixed archive SHA-256, ZIP CRC, archive paths and every file in the embedded MANIFEST. It prints the number of files and makes no changes.

## 2. Apply locally
After reviewing the dry-run result:

```bash
python PDKS/tools/sync-release.py --archive "/path/to/PDKS_0.5.3_完整综合工程包.zip" --repo "/path/to/creative" --apply
```

Inspect the staged diff:

```bash
git diff --cached --stat
git diff --cached --name-status
```

## 3. Push
Only after the staged diff is reviewed:

```bash
python PDKS/tools/sync-release.py --archive "/path/to/PDKS_0.5.3_完整综合工程包.zip" --repo "/path/to/creative" --apply --push
```

## Safety
- Only writes under `creative/PDKS/`.
- Does not read or upload personal Vault contents.
- Excludes .env/credential files, node_modules, build caches, runtime data and backup directories.
- Never force-pushes.
- Git credentials remain in the user's local Git credential manager.
- The current release is Experimental Preview and not production-ready.
