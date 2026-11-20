#!/usr/bin/env python3
"""Safely mirror a PDKS release ZIP into a local creative/PDKS checkout.

Default is a no-write dry run. --apply copies verified files and stages PDKS.
--push is an additional explicit opt-in; it commits and pushes main.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, stat, subprocess, tempfile, zipfile
from pathlib import Path, PurePosixPath

EXCLUDED_PARTS = {".git", ".venv", "venv", "node_modules", "dist", "build",
                  "__pycache__", ".pytest_cache", ".mypy_cache", "data",
                  "backup", "raw-captures", "_audit_install"}
EXCLUDED_NAMES = {".env", ".env.local", ".env.production", "credentials.json", "secrets.json"}
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
MAX_ENTRIES = 10000

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def safe_relative_path(name: str) -> bool:
    # Reject Windows separators as well as POSIX traversal before extraction.
    if not name or "\\" in name or "\x00" in name or ":" in name:
        return False
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "PDKS":
        return False
    if any(part in EXCLUDED_PARTS for part in path.parts) or path.name in EXCLUDED_NAMES:
        return False
    return True

def run(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, help="PDKS release ZIP")
    parser.add_argument("--repo", required=True, help="Local creative Git checkout")
    parser.add_argument("--expected-sha256", help="Optional independently supplied archive SHA-256")
    parser.add_argument("--apply", action="store_true", help="Copy files and stage PDKS")
    parser.add_argument("--push", action="store_true", help="Commit and push main after --apply")
    args = parser.parse_args()
    archive = Path(args.archive).expanduser().resolve()
    repo = Path(args.repo).expanduser().resolve()
    destination = repo / "PDKS"
    if not archive.is_file():
        parser.error(f"Archive not found: {archive}")
    if not (repo / ".git").exists():
        parser.error(f"Not a Git checkout: {repo}")
    if args.push and not args.apply:
        parser.error("--push requires --apply")
    if archive.stat().st_size > MAX_ARCHIVE_BYTES:
        parser.error(f"Archive exceeds {MAX_ARCHIVE_BYTES} byte safety limit")
    archive_hash = sha256_file(archive)
    if args.expected_sha256 and archive_hash.lower() != args.expected_sha256.lower():
        parser.error(f"Archive SHA-256 mismatch: {archive_hash}")

    with tempfile.TemporaryDirectory(prefix="pdks-mirror-") as temp_dir:
        temp = Path(temp_dir)
        with zipfile.ZipFile(archive) as zipped:
            infos = zipped.infolist()
            if len(infos) > MAX_ENTRIES:
                parser.error(f"Archive contains too many entries: {len(infos)}")
            bad = zipped.testzip()
            if bad:
                parser.error(f"ZIP CRC failure: {bad}")
            selected = []
            for info in infos:
                if not safe_relative_path(info.filename):
                    continue
                mode = (info.external_attr >> 16) & 0xFFFF
                if stat.S_ISLNK(mode):
                    parser.error(f"Symlinks are not accepted: {info.filename}")
                if info.file_size > MAX_ARCHIVE_BYTES:
                    parser.error(f"Entry too large: {info.filename}")
                selected.append(info)
            if not any(i.filename == "PDKS/MANIFEST.json" for i in selected):
                parser.error("Missing PDKS/MANIFEST.json")
            for info in selected:
                target = (temp / info.filename).resolve()
                if temp.resolve() not in target.parents and target != temp.resolve():
                    parser.error(f"Unsafe archive path: {info.filename}")
            zipped.extractall(temp, members=selected)

        source = temp / "PDKS"
        try:
            manifest = json.loads((source / "MANIFEST.json").read_text(encoding="utf-8"))
        except Exception as exc:
            parser.error(f"Cannot parse MANIFEST.json: {exc}")
        failures = []
        for entry in manifest.get("files", []):
            rel = entry.get("path", "")
            if not safe_relative_path("PDKS/" + rel):
                failures.append(f"unsafe-manifest-path:{rel}")
                continue
            item = source / Path(*PurePosixPath(rel).parts)
            if not item.is_file():
                failures.append(f"missing:{rel}")
            elif item.stat().st_size != entry.get("size_bytes"):
                failures.append(f"size:{rel}")
            elif sha256_file(item) != entry.get("sha256"):
                failures.append(f"sha256:{rel}")
        if failures:
            parser.error("Manifest verification failed: " + "; ".join(failures[:20]))

        files = [p for p in source.rglob("*")
                 if p.is_file() and safe_relative_path("PDKS/" + p.relative_to(source).as_posix())]
        print(f"Archive SHA-256: {archive_hash}")
        print(f"Manifest files verified: {len(manifest.get('files', []))}")
        print(f"Files selected: {len(files)}")
        print(f"Target: {destination}")
        print("Mode: APPLY" if args.apply else "Mode: DRY RUN")
        if not args.apply:
            print("No files changed. Re-run with --apply after reviewing this plan.")
            return 0

        destination.mkdir(parents=True, exist_ok=True)
        for item in files:
            target = destination / item.relative_to(source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)
        mirror_info = {
            "source_archive": archive.name,
            "source_archive_sha256": archive_hash,
            "manifest_files_verified": len(manifest.get("files", [])),
            "files_copied": len(files),
            "development_stage": "transitional_skill_development",
            "maturity": "experimental_preview",
            "personal_vault_data_uploaded": False,
        }
        (destination / "GITHUB_MIRROR_MANIFEST.json").write_text(
            json.dumps(mirror_info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        run(["git", "add", "PDKS"], repo)
        run(["git", "status", "--short"], repo)
        if args.push:
            run(["git", "commit", "-m", "Mirror complete PDKS 0.5.3.1 preview release"], repo)
            run(["git", "push", "origin", "main"], repo)
            print("Pushed to origin/main.")
        else:
            print("Files staged locally. Review git diff --cached before committing.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
