#!/usr/bin/env python3
"""Keyword search over a local directory of PDKS JSON records (not semantic/vector search)."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def flatten(value):
    if isinstance(value,dict):
        return " ".join(str(k)+" "+flatten(v) for k,v in value.items())
    if isinstance(value,list):
        return " ".join(flatten(x) for x in value)
    return str(value)

def main():
    ap=argparse.ArgumentParser(description="Search local PDKS JSON records by keyword.")
    ap.add_argument("records_dir")
    ap.add_argument("query")
    ap.add_argument("--object-type",choices=["entity","source_asset","evidence_segment","event","assertion","knowledge_asset","personal_context","action","relationship"])
    ap.add_argument("--domain")
    ap.add_argument("--limit",type=int,default=20)
    ap.add_argument("--output")
    args=ap.parse_args()
    root=Path(args.records_dir)
    terms=[x.casefold() for x in args.query.split() if x.strip()]
    results=[]
    for f in sorted(root.rglob("*.json")):
        try: obj=json.loads(f.read_text(encoding="utf-8"))
        except Exception: continue
        if not isinstance(obj,dict) or not obj.get("object_type"): continue
        if args.object_type and obj.get("object_type")!=args.object_type: continue
        if args.domain and args.domain not in obj.get("domains",[]): continue
        text=flatten(obj).casefold()
        if terms and not all(term in text for term in terms): continue
        payload=obj.get("payload",{})
        title=payload.get("title") or payload.get("canonical_name") or payload.get("content") or obj.get("object_id")
        results.append({
            "object_id":obj.get("object_id"),
            "object_type":obj.get("object_type"),
            "title":str(title)[:180],
            "domains":obj.get("domains",[]),
            "path":str(f),
            "created_at":obj.get("created_at")
        })
    results=results[:max(args.limit,0)]
    out={"query":args.query,"count":len(results),"search_type":"keyword","results":results}
    rendered=json.dumps(out,ensure_ascii=False,indent=2)
    if args.output: Path(args.output).write_text(rendered,encoding="utf-8")
    print(rendered)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
