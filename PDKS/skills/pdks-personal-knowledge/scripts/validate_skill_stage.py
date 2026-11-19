#!/usr/bin/env python3
"""Validate PDKS transitional Skill stage declarations and release boundaries."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_MD = ROOT / "SKILL.md"
PROFILE = ROOT / "protocols" / "pdks-development-stage-profile-0.1.json"
REQUIRED_REFERENCES = [
    "references/11-transition-stage-and-capability-boundaries.md",
    "references/12-personal-enterprise-center-ontology-extension-proposal.md",
    "references/13-personal-capture-runtime.md",
]
BENCHMARK_ROOT = ROOT / "benchmarks"

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args()
    skill = SKILL_MD.read_text(encoding="utf-8")
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    checks = {
        "skill_version_0_3_4": 'skill_version: "0.3.4"' in skill,
        "runtime_track_0_5_0": 'runtime_track: "0.5.0"' in skill,
        "transitional_stage_declared": "transitional-skill-development" in skill,
        "experimental_maturity_declared": 'maturity: "experimental"' in skill,
        "stage_profile_matches": profile.get("release", {}).get("skill_version") == "0.3.4"
            and profile.get("release", {}).get("runtime_track") == "0.5.0",
        "ontology_baseline_frozen": profile.get("frozen_baselines", {}).get("ontology") == "0.2.1",
        "ontology_layering_proposal_only": profile.get("ontology_layering", {}).get("status") == "research_proposal_only",
        "production_not_claimed": "not a complete personal digital foundation platform" in skill,
        "required_stage_references_present": all((ROOT / p).is_file() for p in REQUIRED_REFERENCES),
        "cross_host_benchmark_prepared_not_claimed": (BENCHMARK_ROOT / "CROSS_AGENT_TEST_PROTOCOL.md").is_file() and json.loads((BENCHMARK_ROOT / "benchmark-manifest.json").read_text(encoding="utf-8")).get("synthetic_cases") == 12,
        "capture_runtime_reference_present": (ROOT.parents[1] / "runtime" / "pdks_capture_runtime" / "service.py").is_file(),
        "capture_runtime_stage_is_experimental": profile.get("capture_runtime", {}).get("status") == "experimental_local_reference_implementation",
    }
    report = {
        "validator": "pdks-skill-stage-check",
        "stage": profile.get("development_stage"),
        "maturity": profile.get("maturity"),
        "checks": checks,
        "passed": sum(checks.values()),
        "total": len(checks),
        "status": "valid" if all(checks.values()) else "invalid",
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"PDKS stage check: {report['status']} ({report['passed']}/{report['total']})")
        for key, value in checks.items():
            print(f"{'PASS' if value else 'FAIL'} {key}")
    return 0 if all(checks.values()) else 1

if __name__ == "__main__":
    raise SystemExit(main())
