#!/usr/bin/env python3
"""Create a date-scoped structural review of local PDKS records."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser(description="Create a structural daily review from PDKS JSON records.")
    ap.add_argument("records_dir")
    ap.add_argument("--date",required=True,help="Local calendar date YYYY-MM-DD")
    ap.add_argument("--output")
    args=ap.parse_args()
    root=Path(args.records_dir)
    events=[]; assertions=[]; knowledge=[]; actions=[]
    for f in sorted(root.rglob("*.json")):
        try: obj=json.loads(f.read_text(encoding="utf-8"))
        except Exception: continue
        if not isinstance(obj,dict) or not obj.get("object_type"): continue
        typ=obj["object_type"]; p=obj.get("payload",{})
        if typ=="event" and str(p.get("start_at","")).startswith(args.date):
            events.append({"object_id":obj.get("object_id"),"title":p.get("title"),"event_type":p.get("event_type"),"start_at":p.get("start_at"),"end_at":p.get("end_at"),"evidence_refs":p.get("evidence_refs",[])})
        elif typ=="assertion" and str(p.get("assertion_at","")).startswith(args.date):
            assertions.append({"object_id":obj.get("object_id"),"assertion_type":p.get("assertion_type"),"content":p.get("content"),"epistemic_status":p.get("epistemic_status"),"evidence_refs":p.get("evidence_refs",[])})
        elif typ=="knowledge_asset" and str(obj.get("created_at","")).startswith(args.date):
            knowledge.append({"object_id":obj.get("object_id"),"title":p.get("title"),"summary":p.get("summary"),"verification_status":p.get("verification_status")})
        elif typ=="action" and p.get("status") not in {"completed","cancelled","done"}:
            actions.append({"object_id":obj.get("object_id"),"title":p.get("title"),"status":p.get("status"),"due_at":p.get("due_at"),"assignee_ref":p.get("assignee_ref")})
    report={
        "report_type":"PDKS-Daily-Review-Structure",
        "report_version":"0.2.0",
        "date":args.date,
        "events":events,
        "assertions":assertions,
        "knowledge_candidates":knowledge,
        "open_actions":actions,
        "counts":{"events":len(events),"assertions":len(assertions),"knowledge_candidates":len(knowledge),"open_actions":len(actions)},
        "limitations":["This is a structural extraction from supplied records, not an assessment of completeness.","Absence from this dataset does not prove that no activity occurred."]
    }
    rendered=json.dumps(report,ensure_ascii=False,indent=2)
    if args.output: Path(args.output).write_text(rendered,encoding="utf-8")
    print(rendered)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
