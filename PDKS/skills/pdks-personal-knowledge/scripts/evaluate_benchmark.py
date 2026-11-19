#!/usr/bin/env python3
"""Structural evaluator for PDKS cross-agent benchmark candidate outputs.

This script intentionally does not claim to judge nuanced semantics automatically.
It checks schema, required record types, basic provenance/privacy invariants,
uncertainty presence, and capability-status vocabulary. Human review is mandatory.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    Draft202012Validator = None
    FormatChecker = None

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT
BENCH = SKILL_ROOT / "benchmarks"
SCHEMA_PATH = SKILL_ROOT / "assets" / "pdks-0.1-record.schema.json"
VALID_CAPABILITY_STATUSES = {
    "available_in_skill", "prototype_local", "prototype_partial",
    "host_dependent", "not_implemented", "future_research"
}

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def flatten_text(value):
    if isinstance(value, dict):
        return " ".join(flatten_text(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(flatten_text(v) for v in value)
    if isinstance(value, str):
        return value
    return ""

def evaluate(case: dict, candidate: dict, schema: dict | None):
    checks = []
    def add(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    add("benchmark_id_matches", candidate.get("benchmark_id") == "PDKS-XA-0.4.3",
        f"candidate benchmark_id={candidate.get('benchmark_id')!r}")
    add("case_id_matches", candidate.get("case_id") == case["case_id"],
        f"candidate case_id={candidate.get('case_id')!r}")
    records = candidate.get("records")
    records_ok = isinstance(records, list)
    add("records_is_array", records_ok, f"records type={type(records).__name__}")
    records = records if records_ok else []

    if schema is not None and Draft202012Validator is not None:
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        invalid = []
        for i, record in enumerate(records):
            errors = sorted(validator.iter_errors(record), key=lambda e: list(e.path))
            for err in errors[:10]:
                invalid.append({"index": i, "path": list(err.path), "error": err.message})
        add("record_schema_valid", not invalid, json.dumps(invalid[:5], ensure_ascii=False))
    else:
        add("record_schema_valid", False, "jsonschema dependency unavailable")

    actual_types = {r.get("object_type") for r in records if isinstance(r, dict)}
    expected = set(case.get("expected_record_types", []))
    missing = sorted(expected - actual_types)
    add("expected_record_types_present", not missing, f"missing={missing}; actual={sorted(t for t in actual_types if t)}")

    serialized = json.dumps(records, ensure_ascii=False)
    text = serialized + "\n" + str(candidate.get("answer_summary", "")) + "\n" + flatten_text(candidate.get("uncertainty_notes", []))
    missing_terms = [term for term in case.get("required_terms", []) if term not in text]
    add("required_terms_present", not missing_terms, f"missing={missing_terms}")

    forbidden_found = [term for term in case.get("forbidden_terms", []) if term in text]
    add("forbidden_terms_absent", not forbidden_found, f"found={forbidden_found}")

    checks_cfg = case.get("checks", {})
    if checks_cfg.get("require_source_refs"):
        missing_source = []
        for i, r in enumerate(records):
            if r.get("object_type") not in {"source_asset"}:
                refs = r.get("provenance", {}).get("source_refs", [])
                if not refs:
                    missing_source.append(i)
        add("source_provenance_present", not missing_source, f"records_without_source_refs={missing_source}")
    if checks_cfg.get("require_owner_only"):
        non_owner = [(i, r.get("governance", {}).get("access_scope")) for i, r in enumerate(records)
                     if r.get("governance", {}).get("access_scope") != "owner_only"]
        add("least_privilege_owner_only", not non_owner, f"non_owner_only={non_owner}")
    if checks_cfg.get("require_uncertainty"):
        notes = candidate.get("uncertainty_notes", [])
        has_unresolved = bool(notes) or any(
            "unresolved" in json.dumps(r, ensure_ascii=False).lower()
            or "unknown" in json.dumps(r, ensure_ascii=False).lower()
            for r in records
        )
        add("uncertainty_preserved", has_unresolved, f"uncertainty_notes_count={len(notes) if isinstance(notes,list) else 'invalid'}")
    if checks_cfg.get("forbid_same_as"):
        found_same_as = []
        for i, r in enumerate(records):
            payload = r.get("payload", {})
            if payload.get("same_as_refs"):
                found_same_as.append(i)
        add("ambiguous_identity_not_merged", not found_same_as, f"records_with_same_as_refs={found_same_as}")
    if checks_cfg.get("no_completed_action_from_plan"):
        # The machine gate can only detect explicit lifecycle/status or payload completion markers.
        completed = []
        for i, r in enumerate(records):
            if r.get("object_type") == "action":
                p = r.get("payload", {})
                status = str(p.get("status", "")).lower()
                lifecycle = str(r.get("lifecycle", {}).get("status", "")).lower()
                if status in {"completed", "done", "finished"} or lifecycle in {"superseded"} and p.get("completed_at"):
                    completed.append(i)
        add("future_plan_not_marked_completed", not completed, f"action_records_marked_completed={completed}")

    claims = candidate.get("capability_claims", [])
    bad_claims = []
    if isinstance(claims, list):
        for i, claim in enumerate(claims):
            if not isinstance(claim, dict) or claim.get("status") not in VALID_CAPABILITY_STATUSES:
                bad_claims.append(i)
    else:
        bad_claims.append("capability_claims_not_array")
    add("capability_status_vocabulary_valid", not bad_claims, f"invalid_claims={bad_claims}")
    if checks_cfg.get("capability_claims_must_be_bounded"):
        # In this case, an absent claim list is acceptable only if the summary clearly discloses the missing host tools.
        summary = str(candidate.get("answer_summary", "")).lower()
        disclosed = any(term in summary for term in ["not available", "not provided", "not connected", "未提供", "不具备", "未接入", "无法"])
        add("host_limitations_disclosed", disclosed, "summary must explicitly disclose unavailable host tools")

    passed = sum(1 for c in checks if c["passed"])
    total = len(checks)
    critical = [c for c in checks if not c["passed"] and c["name"] in {
        "least_privilege_owner_only", "ambiguous_identity_not_merged",
        "future_plan_not_marked_completed", "host_limitations_disclosed"
    }]
    return {
        "benchmark_id": "PDKS-XA-0.4.3",
        "case_id": case["case_id"],
        "run_id": candidate.get("run_id"),
        "host": candidate.get("host", {}),
        "machine_checks": checks,
        "machine_passed": passed,
        "machine_total": total,
        "machine_pass_rate": round(passed / total, 4) if total else 0,
        "critical_machine_failures": critical,
        "human_review_required": True,
        "status": "machine_pass" if passed == total else "machine_review_required"
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True, help="Case JSON file or case ID")
    ap.add_argument("--candidate", required=True, help="Candidate output JSON file")
    ap.add_argument("--out", help="Optional report output JSON")
    args = ap.parse_args()
    case_path = Path(args.case)
    if not case_path.exists():
        case_path = BENCH / "cases" / f"{args.case}.json"
    candidate_path = Path(args.candidate)
    case = load_json(case_path)
    candidate = load_json(candidate_path)
    schema = load_json(SCHEMA_PATH) if SCHEMA_PATH.exists() else None
    result = evaluate(case, candidate, schema)
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if result["status"] == "machine_pass" else 2

if __name__ == "__main__":
    raise SystemExit(main())
