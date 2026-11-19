#!/usr/bin/env python3
"""Export a lightweight PDKS record graph JSON view from a directory of records."""
from __future__ import annotations
import argparse, json
from pathlib import Path

REF_KEYS = {
    "source_ref":"referencesSource",
    "entity_ref":"referencesEntity",
    "speaker_ref":"hasSpeaker",
    "subject_ref":"hasSubject",
    "asserted_by_ref":"assertedBy",
    "assignee_ref":"assignedTo",
    "completion_event_ref":"completedBy",
    "location_ref":"hasLocation",
    "supersedes_ref":"supersedes"
}
REF_LIST_KEYS = {
    "source_refs":"referencesSource",
    "evidence_refs":"hasEvidence",
    "context_refs":"hasContext",
    "about_refs":"about",
    "derived_from_refs":"derivedFrom",
    "created_from_refs":"createdFrom",
    "depends_on_refs":"dependsOn"
}

def walk(obj, source_id, edges, path=""):
    if isinstance(obj,dict):
        for k,v in obj.items():
            if k in REF_KEYS and isinstance(v,str):
                edges.append({"from":source_id,"predicate":REF_KEYS[k],"to":v,"field":k})
            elif k in REF_LIST_KEYS and isinstance(v,list):
                for ref in v:
                    if isinstance(ref,str):
                        edges.append({"from":source_id,"predicate":REF_LIST_KEYS[k],"to":ref,"field":k})
            else:
                walk(v,source_id,edges,f"{path}.{k}" if path else k)
    elif isinstance(obj,list):
        for x in obj: walk(x,source_id,edges,path)

def main():
    ap=argparse.ArgumentParser(description="Export a simple graph view from PDKS JSON records.")
    ap.add_argument("records_dir")
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    root=Path(args.records_dir)
    nodes=[]; edges=[]
    for f in sorted(root.rglob("*.json")):
        try: obj=json.loads(f.read_text(encoding="utf-8"))
        except Exception: continue
        if not isinstance(obj,dict) or not obj.get("object_id"): continue
        nodes.append({
            "@id":obj["object_id"],
            "@type":obj.get("object_type"),
            "pdks_version":obj.get("pdks_version"),
            "domains":obj.get("domains",[]),
            "payload":obj.get("payload",{})
        })
        walk(obj,obj["object_id"],edges)
    known={n["@id"] for n in nodes}
    graph={
        "format":"PDKS-Lightweight-Graph",
        "format_version":"0.2.0",
        "pdks_standard_version":"0.1.0",
        "nodes":nodes,
        "edges":edges,
        "unresolved_targets":sorted({e["to"] for e in edges if e["to"] not in known})
    }
    Path(args.output).write_text(json.dumps(graph,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"nodes":len(nodes),"edges":len(edges),"unresolved_targets":len(graph["unresolved_targets"]),"output":args.output},ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
