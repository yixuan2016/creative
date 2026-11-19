#!/usr/bin/env python3
"""Command-line interface for the ontology-first PDKS 0.4 runtime."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

try:
    from .pdks_ontology_runtime import OntologyRuntime, OntologyValidationError
    from .pdks_ontology_sqlite import OntologySQLiteStore
    from .pdks_ontology_governance import build_governance_report, compare_ontology_versions, load_candidate_ontology
except ImportError:
    from pdks_ontology_runtime import OntologyRuntime, OntologyValidationError
    from pdks_ontology_sqlite import OntologySQLiteStore
    from pdks_ontology_governance import build_governance_report, compare_ontology_versions, load_candidate_ontology

def load_records(path: str):
    root=Path(path)
    files=[root] if root.is_file() else sorted(root.rglob("*.json"))
    records=[]
    for f in files:
        try:
            data=json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data,dict) and data.get("object_type"):
            records.append(data)
    return records

def emit(data):
    print(json.dumps(data,ensure_ascii=False,indent=2,default=str))

def main(argv=None):
    ap=argparse.ArgumentParser(description="PDKS Ontology-first Personal Data Runtime 0.4.1")
    sub=ap.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("ontology-info",help="show loaded ontology modules and semantic vocabulary")
    p=sub.add_parser("validate",help="validate PDKS records against JSON Schema, ontology and controlled vocabulary")
    p.add_argument("--records-dir",required=True)
    p.add_argument("--strict-refs",action="store_true")
    p.add_argument("--trusted-consent-ref",action="append",default=[],help="Trusted active consent reference; repeatable")
    p.add_argument("--shacl",action="store_true",help="execute pySHACL validation (fails if pySHACL is unavailable)")
    p=sub.add_parser("ontology-check",help="check ontology term coverage and backward compatibility")
    p.add_argument("--baseline",help="baseline ontology Turtle file; defaults to the bundled 0.1 ontology")
    p=sub.add_parser("ontology-diff",help="compare a baseline ontology with the loaded candidate ontology")
    p.add_argument("--baseline",required=True)
    p=sub.add_parser("init",help="initialize ontology registry and local SQLite tables")
    p.add_argument("--db",required=True)
    p.add_argument("--owner",required=True)
    p=sub.add_parser("import",help="import one owner's PDKS records and materialize RDF triples")
    p.add_argument("--db",required=True); p.add_argument("--owner",required=True); p.add_argument("--records-dir",required=True)
    p.add_argument("--expected-revision",type=int); p.add_argument("--allow-updates",action="store_true")
    p.add_argument("--actor",default="user:owner"); p.add_argument("--strict-refs",action="store_true")
    p.add_argument("--trusted-consent-ref",action="append",default=[],help="Trusted active consent reference; repeatable")
    p=sub.add_parser("list",help="list stored records")
    p.add_argument("--db",required=True); p.add_argument("--owner",required=True); p.add_argument("--object-type")
    p=sub.add_parser("export",help="export the owner's semantic graph")
    p.add_argument("--db",required=True); p.add_argument("--owner",required=True); p.add_argument("--format",choices=["turtle","json-ld"],default="turtle"); p.add_argument("--output",required=True)
    p=sub.add_parser("rebuild",help="rebuild RDF projection from canonical JSON records")
    p.add_argument("--db",required=True); p.add_argument("--owner",required=True)
    p=sub.add_parser("revision",help="show owner's current data revision")
    p.add_argument("--db",required=True); p.add_argument("--owner",required=True)
    p=sub.add_parser("sparql",help="run a SPARQL SELECT/ASK query against one owner's RDF projection")
    p.add_argument("--db",required=True); p.add_argument("--owner",required=True); p.add_argument("--query",required=True)

    args=ap.parse_args(argv)
    runtime=OntologyRuntime()
    if args.cmd=="ontology-info":
        emit({
            "runtime_version":"0.4.1","record_schema":"0.1.x","ontology_version":runtime.ontology_version,
            "ontology_iri":runtime.ontology_iri,"ontology_triples":len(runtime.ontology_graph),
            "vocabulary_triples":len(runtime.vocabulary_graph),"event_taxonomy_triples":len(runtime.taxonomy_graph),
            "shacl_shape_triples":len(runtime.shapes_graph),"event_type_codes":len(runtime.event_codes),
            "controlled_vocabulary_codes":len(runtime.vocab_codes),"pyshacl_available":runtime._pyshacl_available(),
            "canonical_record_is_source_of_truth":True,"rdf_is_rebuildable_projection":True
        })
        return 0
    if args.cmd=="ontology-check":
        report=build_governance_report(runtime,args.baseline)
        emit(report)
        return 0 if report["status"]=="valid" else 2
    if args.cmd=="ontology-diff":
        baseline=__import__("rdflib").Graph().parse(args.baseline,format="turtle")
        candidate=load_candidate_ontology(runtime.ontology_dir)
        report=compare_ontology_versions(baseline,candidate)
        emit(report)
        return 2 if report["status"]=="breaking" else 0
    if args.cmd=="validate":
        records=load_records(args.records_dir)
        groups={}
        for r in records: groups.setdefault(r.get("owner_ref"),[]).append(r)
        trusted=set(args.trusted_consent_ref)
        reports=[]
        shacl_unavailable=False
        for owner, group in groups.items():
            report=runtime.validate_records(group,strict_refs=args.strict_refs,trusted_consent_refs=trusted)
            if args.shacl:
                shacl_report=runtime.validate_shacl(runtime.project_records(group))
                report["shacl"] = shacl_report
                if shacl_report["status"]=="unavailable":
                    shacl_unavailable=True
                elif shacl_report["status"]!="conforms":
                    report["errors"].append(f"SHACL non-conformant for owner {owner}: {shacl_report['results_count']} result(s)")
            reports.append(report)
        errors=[e for x in reports for e in x["errors"]]
        status="invalid" if errors else ("shacl_unavailable" if shacl_unavailable else "valid")
        emit({"status":status,"records":len(records),"owners":len(groups),
              "ontology_version":runtime.ontology_version,"shacl_requested":args.shacl,
              "scenarios":reports,"errors":errors})
        return 3 if shacl_unavailable else (0 if not errors else 2)
    if args.cmd in {"init","import","list","export","rebuild","revision","sparql"}:
        store=OntologySQLiteStore(args.db,runtime)
        if args.cmd=="init":
            emit({"status":"initialized","db":str(Path(args.db).resolve()),"owner":args.owner,
                  "revision":store.revision(args.owner),"ontology_version":runtime.ontology_version,
                  "integrity_check":store.integrity_check()})
        elif args.cmd=="import":
            records=load_records(args.records_dir)
            try:
                result=store.import_records(args.owner,records,expected_revision=args.expected_revision,
                                            allow_updates=args.allow_updates,strict_refs=args.strict_refs,actor_ref=args.actor,
                                            trusted_consent_refs=set(args.trusted_consent_ref))
                emit(result)
            except (OntologyValidationError,ValueError,RuntimeError) as exc:
                emit({"status":"rejected","error":str(exc)})
                return 2
        elif args.cmd=="list":
            emit({"revision":store.revision(args.owner),"records":store.list_objects(args.owner,args.object_type)})
        elif args.cmd=="export":
            graph=store.export_graph(args.owner)
            if args.format=="turtle":
                rendered=graph.serialize(format="turtle")
            else:
                context=json.loads((runtime.ontology_dir/"pdks-jsonld-context-0.2.1.json").read_text(encoding="utf-8"))["@context"]
                rendered=graph.serialize(format="json-ld",context=context,auto_compact=True)
            Path(args.output).parent.mkdir(parents=True,exist_ok=True)
            Path(args.output).write_text(rendered,encoding="utf-8")
            emit({"status":"exported","format":args.format,"triples":len(graph),"output":str(Path(args.output).resolve())})
        elif args.cmd=="rebuild":
            emit(store.rebuild_projection(args.owner))
        elif args.cmd=="revision":
            emit({"owner":args.owner,"revision":store.revision(args.owner),"integrity_check":store.integrity_check()})
        elif args.cmd=="sparql":
            try:
                emit({"owner":args.owner,"rows":store.query_sparql(args.owner,args.query)})
            except Exception as exc:
                emit({"status":"query_error","error":str(exc)})
                return 2
    return 0

if __name__=="__main__":
    raise SystemExit(main())
