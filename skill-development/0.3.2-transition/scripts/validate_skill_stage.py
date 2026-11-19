#!/usr/bin/env python3
"""Validate PDKS transitional Skill stage declarations and release boundaries."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "pdks-development-stage-profile-0.1.json"
REFS = [
    ROOT / "references/11-transition-stage-and-capability-boundaries.md",
    ROOT / "references/12-personal-enterprise-center-ontology-extension-proposal.md"
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    checks = {
        "runtime_track_0_4_2": profile.get("release", {}).get("runtime_track") == "0.4.2",
        "skill_version_0_3_2": profile.get("release", {}).get("skill_version") == "0.3.2",
        "transitional_stage": profile.get("development_stage") == "transitional_skill_development",
        "experimental_maturity": profile.get("maturity") == "experimental",
        "ontology_frozen": profile.get("frozen_baselines", {}).get("ontology") == "0.2.1",
        "layering_proposal_only": profile.get("ontology_layering", {}).get("status") == "research_proposal_only",
        "no_published_core_change": profile.get("ontology_layering", {}).get("may_change_published_core") is False,
        "references_present": all(p.is_file() for p in REFS)
    }
    report = {"status":"valid" if all(checks.values()) else "invalid","stage":profile.get("development_stage"),"maturity":profile.get("maturity"),"checks":checks,"passed":sum(checks.values()),"total":len(checks)}
    print(json.dumps(report,ensure_ascii=False,indent=2) if args.json else f"PDKS stage check: {report['status']} ({report['passed']}/{report['total']})")
    return 0 if all(checks.values()) else 1

if __name__ == "__main__":
    raise SystemExit(main())
