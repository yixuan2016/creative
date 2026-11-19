#!/usr/bin/env python3
"""Build or verify a deterministic SHA-256 manifest for PDKS Ontology 0.2.1."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ONTOLOGY_DIR = HERE / "assets" / "ontology" / "0.2.1"
FILES = [
    "pdks-core-ontology-0.2.ttl",
    "pdks-governance-ontology-0.2.ttl",
    "pdks-agent-runtime-ontology-0.2.ttl",
    "pdks-core-vocabularies-0.2.ttl",
    "pdks-core-shapes-0.2.ttl",
    "pdks-jsonld-context-0.2.1.json",
    "pdks-json-to-ontology-mapping-0.2.1.json",
    "pdks-ontology-migration-0.1-to-0.2.1.json",
]

def build():
    entries=[]
    for name in FILES:
        path=ONTOLOGY_DIR/name
        if not path.exists():
            raise SystemExit(f"missing ontology release file: {name}")
        data=path.read_bytes()
        entries.append({"path":name,"size_bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
    return {
        "ontology_version":"0.2.1",
        "ontology_iri":"urn:pdks:ontology:0.2.1",
        "stable_term_namespace":"urn:pdks:ontology#",
        "vocabulary_namespace":"urn:pdks:vocabulary:0.2#",
        "event_taxonomy_namespace":"urn:pdks:taxonomy:event:0.1#",
        "record_schema_compatibility":"0.1.x",
        "files_count":len(entries),
        "files":entries,
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--check",action="store_true",help="verify existing manifest without rewriting it")
    args=parser.parse_args()
    path=ONTOLOGY_DIR/"ontology-manifest.json"
    expected=build()
    if args.check:
        if not path.exists():
            print(json.dumps({"status":"missing","manifest":str(path)}));return 2
        actual=json.loads(path.read_text(encoding="utf-8"))
        ok=actual==expected
        print(json.dumps({"status":"valid" if ok else "mismatch","files":len(expected["files"])}))
        return 0 if ok else 2
    path.write_text(json.dumps(expected,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":"built","ontology_version":expected["ontology_version"],"files":len(expected["files"])}))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
