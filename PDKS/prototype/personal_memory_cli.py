"""Command-line interface for the local PDKS -> ADS personal runtime prototype."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pdks_ads_adapter import project_bundle
from personal_memory_sqlite import SQLiteBackedPersonalMemoryEngine, SQLitePersonalMemoryStore


def _read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, value: Any) -> None:
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_records(directory: str | Path) -> list[dict[str, Any]]:
    root = Path(directory)
    if not root.is_dir():
        raise ValueError(f"records directory does not exist: {root}")
    records = []
    for path in sorted(root.rglob("*.json")):
        try:
            value = _read_json(path)
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if isinstance(value, dict) and value.get("object_type") and value.get("object_id"):
            records.append(value)
        elif isinstance(value, list):
            records.extend(x for x in value if isinstance(x, dict) and x.get("object_type") and x.get("object_id"))
    if not records:
        raise ValueError("No PDKS records found in the directory.")
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local-first PDKS / ADS-WORK-09 personal data runtime prototype")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Initialize a local SQLite personal vault")
    init.add_argument("--db", required=True)
    init.add_argument("--owner", required=True)

    project = sub.add_parser("project-pdks", help="Build an ADS projection from a directory of PDKS JSON records")
    project.add_argument("--records-dir", required=True)
    project.add_argument("--owner", required=True)
    project.add_argument("--output", required=True)
    project.add_argument("--authorization-ref", action="append", default=[], help="Validated active authorization reference; repeat as needed")
    project.add_argument("--schema", help="PDKS JSON Schema path; defaults to the bundled PDKS 0.1 schema")
    project.add_argument("--taxonomy", help="PDKS event taxonomy path; defaults to the bundled taxonomy")
    project.add_argument("--skip-pdks-validation", action="store_true", help="Skip PDKS schema/taxonomy validation for synthetic test fixtures only")

    apply = sub.add_parser("apply-projection", help="Atomically persist a prepared PDKS projection")
    apply.add_argument("--db", required=True)
    apply.add_argument("--owner", required=True)
    apply.add_argument("--projection", required=True)
    apply.add_argument("--owner-confirmed", action="store_true", help="Explicitly confirm that the owner reviewed any active/confirmed memory records in this projection")

    context = sub.add_parser("context", help="Build a filtered personal operating context")
    context.add_argument("--db", required=True)
    context.add_argument("--owner", required=True)
    context.add_argument("--purpose", required=True)
    context.add_argument("--include-candidates", action="store_true")
    context.add_argument("--include-sensitive", action="store_true")

    audit = sub.add_parser("audit", help="Read metadata-only append-only audit entries")
    audit.add_argument("--db", required=True)
    audit.add_argument("--owner", required=True)
    audit.add_argument("--limit", type=int, default=100)

    backup = sub.add_parser("backup", help="Create a consistent SQLite backup")
    backup.add_argument("--db", required=True)
    backup.add_argument("--output", required=True)

    integrity = sub.add_parser("integrity-check", help="Run SQLite integrity_check")
    integrity.add_argument("--db", required=True)

    snapshot = sub.add_parser("snapshot", help="Export a portable JSON state snapshot")
    snapshot.add_argument("--db", required=True)
    snapshot.add_argument("--owner", required=True)
    snapshot.add_argument("--output", required=True)

    args = parser.parse_args(argv)

    if args.command == "project-pdks":
        if args.skip_pdks_validation:
            schema_path = taxonomy_path = None
        else:
            skill_assets = Path(__file__).resolve().parents[1] / "skills" / "pdks-personal-knowledge" / "assets"
            schema_path = Path(args.schema).expanduser() if args.schema else skill_assets / "pdks-0.1-record.schema.json"
            taxonomy_path = Path(args.taxonomy).expanduser() if args.taxonomy else skill_assets / "pdks-event-taxonomy-0.1.json"
            if not schema_path.exists() or not taxonomy_path.exists():
                raise FileNotFoundError("PDKS schema/taxonomy not found. Pass --schema and --taxonomy, or use --skip-pdks-validation only for synthetic fixtures.")
        result = project_bundle(
            _load_records(args.records_dir), owner_ref=args.owner,
            valid_authorization_refs=args.authorization_ref,
            schema_path=schema_path, taxonomy_path=taxonomy_path,
        )
        _write_json(args.output, result)
        print(json.dumps({
            "output": str(Path(args.output).resolve()),
            "events": len(result["event_ledger"]),
            "memories": len(result["memory_items"]),
            "intents": len(result["intent_objects"]),
            "blocked": len(result["blocked"]),
            "agent_action_proposals": 0,
            "enterprise_projection": None,
        }, ensure_ascii=False, indent=2))
        return 0

    if args.command == "integrity-check":
        store = SQLitePersonalMemoryStore(args.db)
        result = store.integrity_check()
        print(json.dumps({"integrity_check": result, "ok": result == "ok"}, ensure_ascii=False, indent=2))
        return 0 if result == "ok" else 1

    if args.command == "backup":
        store = SQLitePersonalMemoryStore(args.db)
        target = store.backup_to(args.output)
        print(json.dumps({"backup": str(target), "integrity_check": SQLitePersonalMemoryStore(target).integrity_check()}, ensure_ascii=False, indent=2))
        return 0

    engine = SQLiteBackedPersonalMemoryEngine(args.owner, args.db)
    if args.command == "init":
        print(json.dumps({"status": "ready", "owner_ref": args.owner, "store_revision": engine._revision, "database": str(Path(args.db).expanduser().resolve())}, ensure_ascii=False, indent=2))
    elif args.command == "apply-projection":
        projection = _read_json(args.projection)
        actor_ref = args.owner if args.owner_confirmed else "agent:pdks-ads-bridge"
        result = engine.apply_pdks_projection(projection, actor_ref=actor_ref)
        print(json.dumps({"status": "saved", "store_revision": engine._revision, "counts": result}, ensure_ascii=False, indent=2))
    elif args.command == "context":
        print(json.dumps(engine.build_operating_context(purpose=args.purpose, include_candidates=args.include_candidates, include_sensitive=args.include_sensitive), ensure_ascii=False, indent=2))
    elif args.command == "audit":
        print(json.dumps(engine.audit_log(limit=args.limit), ensure_ascii=False, indent=2))
    elif args.command == "snapshot":
        _write_json(args.output, engine.export_snapshot())
        print(json.dumps({"status": "exported", "output": str(Path(args.output).resolve()), "store_revision": engine._revision}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
