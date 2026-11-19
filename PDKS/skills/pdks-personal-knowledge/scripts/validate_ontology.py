#!/usr/bin/env python3
"""Run PDKS Ontology 0.2.1 syntax, term coverage, compatibility and optional SHACL checks."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
ASSETS=HERE/"assets"
ONTOLOGY_DIR=ASSETS/"ontology"/"0.2.1"


def main():
    ap=argparse.ArgumentParser(description="Validate PDKS Ontology 0.2.1 and semantic governance rules.")
    ap.add_argument("--data",help="Optional RDF/Turtle data graph to validate against SHACL")
    ap.add_argument("--require-shacl",action="store_true",help="Fail if pySHACL is unavailable")
    args=ap.parse_args()
    try:
        import rdflib
        from pdks_ontology_runtime import OntologyRuntime
        from pdks_ontology_governance import build_governance_report
    except ImportError as exc:
        print(f"Install optional ontology dependencies: pip install -r requirements-ontology.txt ({exc})",file=sys.stderr)
        return 2

    files=sorted(ASSETS.glob("*.ttl"))+sorted(ONTOLOGY_DIR.glob("*.ttl"))
    parse_results=[]
    merged=rdflib.Graph()
    for file in files:
        graph=rdflib.Graph().parse(file,format="turtle")
        parse_results.append({"file":str(file.relative_to(ASSETS)),"triples":len(graph)})
        if "shapes" not in file.name:
            for triple in graph: merged.add(triple)

    runtime=OntologyRuntime(ASSETS)
    governance=build_governance_report(runtime)
    report={
        "turtle_syntax":"passed",
        "ontology_version":runtime.ontology_version,
        "files":parse_results,
        "triples_total":sum(item["triples"] for item in parse_results),
        "governance":governance,
        "shacl":"not_run",
    }
    if args.data:
        data_graph=rdflib.Graph().parse(args.data,format="turtle")
        shacl=runtime.validate_shacl(data_graph)
        report["shacl"]=shacl
        if shacl["status"]=="unavailable" and args.require_shacl:
            print(json.dumps(report,ensure_ascii=False,indent=2));return 3
        if shacl["status"]=="non_conformant":
            print(json.dumps(report,ensure_ascii=False,indent=2));return 2
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if governance["status"]=="valid" else 2

if __name__=="__main__":
    raise SystemExit(main())
