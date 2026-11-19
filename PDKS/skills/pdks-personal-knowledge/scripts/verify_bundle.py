#!/usr/bin/env python3
"""Verify PDKS ZIP bundle paths, manifest entries, sizes and SHA-256 hashes."""
from __future__ import annotations
import argparse, json, hashlib, zipfile
from pathlib import PurePosixPath

def main():
    ap=argparse.ArgumentParser(description="Verify PDKS bundle integrity.")
    ap.add_argument("bundle")
    args=ap.parse_args()
    bundle=args.bundle
    with zipfile.ZipFile(bundle) as z:
        names=set(z.namelist())
        for name in names:
            p=PurePosixPath(name)
            if p.is_absolute() or ".." in p.parts:
                raise SystemExit(f"Unsafe archive path: {name}")
        if "manifest.json" not in names:
            raise SystemExit("manifest.json missing")
        manifest=json.loads(z.read("manifest.json").decode("utf-8"))
        failures=[]
        for item in manifest.get("files",[]):
            name=item["path"]
            if name not in names:
                failures.append(f"missing: {name}")
                continue
            data=z.read(name)
            if len(data)!=item["size_bytes"]:
                failures.append(f"size mismatch: {name}")
            if hashlib.sha256(data).hexdigest()!=item["sha256"]:
                failures.append(f"sha256 mismatch: {name}")
        print(json.dumps({
            "bundle_format":manifest.get("bundle_format"),
            "bundle_version":manifest.get("bundle_version"),
            "pdks_standard_version":manifest.get("pdks_standard_version"),
            "manifest_files":len(manifest.get("files",[])),
            "archive_entries":len(names),
            "integrity":"failed" if failures else "passed",
            "failures":failures
        },ensure_ascii=False,indent=2))
        return 1 if failures else 0

if __name__=="__main__":
    raise SystemExit(main())
