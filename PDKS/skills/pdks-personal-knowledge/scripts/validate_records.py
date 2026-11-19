#!/usr/bin/env python3
"""Validate PDKS JSON records: JSON Schema, taxonomy, IDs, references and semantic guardrails."""
from __future__ import annotations
import argparse, json, sys, zipfile, tempfile
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = HERE / "assets" / "pdks-0.1-record.schema.json"
DEFAULT_TAX = HERE / "assets" / "pdks-event-taxonomy-0.1.json"

REF_KEYS = {
    "source_ref", "entity_ref", "speaker_ref", "subject_ref", "asserted_by_ref",
    "assignee_ref", "completion_event_ref", "location_ref", "owner_ref",
    "processing_activity_ref", "supersedes_ref"
}
REF_LIST_KEYS = {
    "source_refs", "evidence_refs", "context_refs", "about_refs", "derived_from_refs",
    "created_from_refs", "depends_on_refs", "allowed_subject_refs"
}

def safe_extract(zip_path: Path, dest: Path):
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            p = Path(info.filename)
            if p.is_absolute() or ".." in p.parts:
                raise ValueError(f"Unsafe path in ZIP: {info.filename}")
        z.extractall(dest)

def load_input(path: Path):
    temp = None
    if path.is_file() and path.suffix.lower() == ".zip":
        temp = tempfile.TemporaryDirectory()
        safe_extract(path, Path(temp.name))
        root = Path(temp.name)
    else:
        root = path
    return root, temp

def find_assets(root: Path):
    schema = next(iter(root.rglob("pdks-0.1-record.schema.json")), DEFAULT_SCHEMA)
    tax = next(iter(root.rglob("pdks-event-taxonomy-0.1.json")), DEFAULT_TAX)
    return schema, tax

def read_records(root: Path):
    if root.is_file():
        candidates = [root] if root.suffix.lower() == ".json" else []
    else:
        candidates = sorted(root.rglob("*.json"))
    records = []
    for f in candidates:
        try:
            obj = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(obj, dict) and obj.get("object_type") in {
            "entity","source_asset","evidence_segment","event","assertion",
            "knowledge_asset","personal_context","action","relationship"
        }:
            records.append((f, obj))
        elif isinstance(obj, list):
            records.extend((f, x) for x in obj if isinstance(x, dict) and x.get("object_type"))
    return records

def taxonomy_codes(tax):
    return {
        e["code"] for domain in tax.get("domains", [])
        for e in domain.get("events", [])
    }

def parse_time(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

def collect_refs(obj, path=""):
    found = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{path}.{k}" if path else k
            if k in REF_KEYS and isinstance(v, str):
                found.append((here, v))
            elif k in REF_LIST_KEYS and isinstance(v, list):
                found.extend((f"{here}[{i}]", x) for i, x in enumerate(v) if isinstance(x, str))
            else:
                found.extend(collect_refs(v, here))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            found.extend(collect_refs(v, f"{path}[{i}]"))
    return found

def validate(root: Path, strict_refs=False):
    try:
        import jsonschema
    except ImportError:
        return 2, ["Missing dependency: install with `python -m pip install jsonschema`"], {}
    schema_path, tax_path = find_assets(root)
    if not schema_path.exists() or not tax_path.exists():
        return 2, ["Could not find canonical PDKS schema or taxonomy assets."], {}
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    tax = json.loads(tax_path.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    codes = taxonomy_codes(tax)
    records = read_records(root)
    errors, warnings = [], []
    ids = {}
    for file, rec in records:
        rid = rec.get("object_id")
        if not rid:
            errors.append(f"{file}: missing object_id")
        elif rid in ids:
            errors.append(f"{file}: duplicate object_id {rid}; also in {ids[rid]}")
        else:
            ids[rid] = str(file)
        for err in validator.iter_errors(rec):
            loc = ".".join(str(x) for x in err.absolute_path) or "<root>"
            errors.append(f"{file}:{loc}: {err.message}")
        payload = rec.get("payload", {})
        typ = rec.get("object_type")
        if typ == "event":
            code = payload.get("event_type")
            if code and code not in codes:
                errors.append(f"{file}: event_type not in taxonomy: {code}")
            try:
                start, end = parse_time(payload.get("start_at")), parse_time(payload.get("end_at"))
                if start and end and end < start:
                    errors.append(f"{file}: event end_at precedes start_at")
            except Exception as ex:
                warnings.append(f"{file}: could not compare event times: {ex}")
        if typ == "personal_context":
            if payload.get("verification_status") == "inferred" and not payload.get("evidence_refs"):
                errors.append(f"{file}: inferred personal_context requires evidence_refs")
        if typ == "evidence_segment":
            loc = payload.get("locator", {})
            start, end = loc.get("start_ms"), loc.get("end_ms")
            if start is not None and start < 0:
                errors.append(f"{file}: locator.start_ms must be non-negative")
            if start is not None and end is not None and end < start:
                errors.append(f"{file}: locator.end_ms precedes start_ms")
        if rec.get("governance", {}).get("access_scope") in {"public","organization_authorized"}:
            warnings.append(f"{file}: broad access scope; ensure explicit authorization exists")

    known = set(ids)
    for file, rec in records:
        for loc, ref in collect_refs(rec):
            # Agent/processor identifiers are provenance actors, not PDKS record IDs.
            if ref.startswith("urn:pdks:agent:"):
                continue
            if ref not in known:
                msg = f"{file}:{loc}: reference not included in this bundle: {ref}"
                (errors if strict_refs else warnings).append(msg)

    summary = {
        "records": len(records),
        "unique_ids": len(ids),
        "taxonomy_codes": len(codes),
        "errors": len(errors),
        "warnings": len(warnings),
        "status": "invalid" if errors else ("valid_with_warnings" if warnings else "valid")
    }
    return (1 if errors else 0), errors + [f"WARNING: {w}" for w in warnings], summary

def main():
    ap = argparse.ArgumentParser(description="Validate PDKS 0.1 records and semantic guardrails.")
    ap.add_argument("path", help="JSON file, directory of records, or PDKS ZIP bundle")
    ap.add_argument("--strict-refs", action="store_true", help="Treat references absent from the input bundle as errors")
    ap.add_argument("--report", help="Optional JSON report output path")
    args = ap.parse_args()
    root, temp = load_input(Path(args.path))
    try:
        code, messages, summary = validate(root, args.strict_refs)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        for m in messages:
            print(("- " if not m.startswith("WARNING:") else "! ") + m)
        if args.report:
            Path(args.report).write_text(json.dumps({"summary":summary,"messages":messages},ensure_ascii=False,indent=2),encoding="utf-8")
        return code
    finally:
        if temp:
            temp.cleanup()

if __name__ == "__main__":
    raise SystemExit(main())
