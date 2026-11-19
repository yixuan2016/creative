#!/usr/bin/env python3
"""Create a non-destructive migration plan from a PDKS export bundle."""
from __future__ import annotations
import argparse, json, zipfile, hashlib
from pathlib import PurePosixPath
from collections import Counter

def main():
    ap=argparse.ArgumentParser(description="Inspect a PDKS bundle and create a target-neutral migration plan.")
    ap.add_argument("bundle")
    ap.add_argument("--output",required=True)
    ap.add_argument("--target-name",default="unspecified-target")
    ap.add_argument("--supported-object-types",nargs="*",default=[
        "entity","source_asset","evidence_segment","event","assertion",
        "knowledge_asset","personal_context","action","relationship"
    ])
    args=ap.parse_args()
    with zipfile.ZipFile(args.bundle) as z:
        names=set(z.namelist())
        if "manifest.json" not in names:
            raise SystemExit("manifest.json missing")
        manifest=json.loads(z.read("manifest.json").decode("utf-8"))
        integrity_errors=[]
        for item in manifest.get("files",[]):
            name=item.get("path")
            if name not in names:
                integrity_errors.append(f"missing file: {name}")
                continue
            data=z.read(name)
            if len(data)!=item.get("size_bytes"):
                integrity_errors.append(f"size mismatch: {name}")
            if hashlib.sha256(data).hexdigest()!=item.get("sha256"):
                integrity_errors.append(f"sha256 mismatch: {name}")
        if integrity_errors:
            raise SystemExit("Bundle integrity check failed: " + "; ".join(integrity_errors))
        for name in names:
            p=PurePosixPath(name)
            if p.is_absolute() or ".." in p.parts:
                raise SystemExit(f"Unsafe archive path: {name}")
        records=[]
        for name in sorted(n for n in names if n.startswith("records/") and n.endswith(".json")):
            obj=json.loads(z.read(name).decode("utf-8"))
            records.append((name,obj))
    counts=Counter(obj.get("object_type","unknown") for _,obj in records)
    supported=set(args.supported_object_types)
    unsupported={k:v for k,v in counts.items() if k not in supported}
    id_map={obj.get("object_id"):None for _,obj in records if obj.get("object_id")}
    plan={
        "plan_type":"PDKS-Migration-Plan",
        "plan_version":"0.2.0",
        "source_bundle_version":manifest.get("bundle_version"),
        "pdks_standard_version":manifest.get("pdks_standard_version"),
        "target_name":args.target_name,
        "status":"prepared_not_imported",
        "bundle_integrity":"passed",
        "record_count":len(records),
        "record_counts":dict(counts),
        "supported_object_types":sorted(supported),
        "unsupported_object_types":unsupported,
        "steps":[
            {"step":1,"action":"verify_bundle_integrity","status":"required"},
            {"step":2,"action":"confirm_target_schema_and_field_mapping","status":"required"},
            {"step":3,"action":"preserve_or_map_object_ids","status":"required","id_map_template":id_map},
            {"step":4,"action":"map_permissions_without_widening_access","status":"required"},
            {"step":5,"action":"import_entities_and_source_assets","status":"pending"},
            {"step":6,"action":"import_evidence_and_events","status":"pending"},
            {"step":7,"action":"import_assertions_knowledge_context_actions_relationships","status":"pending"},
            {"step":8,"action":"validate_references_and_record_import_receipts","status":"pending"}
        ],
        "external_references":manifest.get("external_references",[]),
        "warnings":[
            "This is a target-neutral plan, not an import operation.",
            "A real destination adapter and explicit authorization are required to write data.",
            "If the target cannot preserve a field or permission, record the loss and apply the stricter access scope."
        ]
    }
    if unsupported:
        plan["warnings"].append("Some record object types are not listed as supported by the target profile.")
    with open(args.output,"w",encoding="utf-8") as f:
        json.dump(plan,f,ensure_ascii=False,indent=2)
    print(json.dumps({
        "status":plan["status"],
        "target":args.target_name,
        "records":len(records),
        "unsupported_types":unsupported,
        "output":args.output
    },ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
