#!/usr/bin/env python3
"""Build a portable PDKS ZIP export bundle from a directory of record JSON files."""
from __future__ import annotations
import argparse, json, hashlib, zipfile, shutil
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parents[1]
ASSETS = HERE / "assets"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def main():
    ap=argparse.ArgumentParser(description="Build PDKS portable export bundle.")
    ap.add_argument("--records", required=True, help="Directory containing PDKS JSON records")
    ap.add_argument("--output", required=True, help="Output ZIP path")
    ap.add_argument("--exported-by", default="pdks-agent-skill-0.2.0")
    ap.add_argument("--source-assets", help="Optional directory of authorized original source files to include")
    ap.add_argument("--include-standards", action="store_true", default=True)
    args=ap.parse_args()
    records_dir=Path(args.records).resolve()
    out=Path(args.output).resolve()
    if not records_dir.is_dir():
        raise SystemExit("records directory does not exist")
    files=[]
    counts={}
    for f in sorted(records_dir.rglob("*.json")):
        try:
            obj=json.loads(f.read_text(encoding="utf-8"))
        except Exception as ex:
            raise SystemExit(f"Invalid JSON: {f}: {ex}")
        if not isinstance(obj,dict) or "object_type" not in obj or "object_id" not in obj:
            continue
        typ=obj["object_type"]
        counts[typ]=counts.get(typ,0)+1
        files.append((f,Path("records")/typ/f.name,obj))
    if not files:
        raise SystemExit("No PDKS records found")
    manifest_files=[]
    external_refs=set()
    known_ids={obj.get("object_id") for _,_,obj in files}
    ref_keys={"source_ref","entity_ref","speaker_ref","subject_ref","asserted_by_ref","assignee_ref","completion_event_ref","location_ref","owner_ref","processing_activity_ref","supersedes_ref"}
    ref_list_keys={"source_refs","evidence_refs","context_refs","about_refs","derived_from_refs","created_from_refs","depends_on_refs","allowed_subject_refs"}
    def scan_refs(value):
        if isinstance(value,dict):
            for key,val in value.items():
                if key in ref_keys and isinstance(val,str):
                    if val not in known_ids and not val.startswith("urn:pdks:agent:"):
                        external_refs.add(val)
                elif key in ref_list_keys and isinstance(val,list):
                    for ref in val:
                        if isinstance(ref,str) and ref not in known_ids and not ref.startswith("urn:pdks:agent:"):
                            external_refs.add(ref)
                else:
                    scan_refs(val)
        elif isinstance(value,list):
            for item in value:
                scan_refs(item)
    for _,_,obj in files:
        scan_refs(obj)
    with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
        for src, arc, obj in files:
            data=src.read_bytes()
            z.writestr(str(arc).replace("\\","/"),data)
            manifest_files.append({"path":str(arc).replace("\\","/"),"size_bytes":len(data),"sha256":sha(data)})
        standard_files = [
            "pdks-0.1-record.schema.json",
            "pdks-event-taxonomy-0.1.json",
            "pdks-core-ontology-0.1.ttl",
            "pdks-core-shapes-0.1.ttl",
            "pdks-core-vocabularies-0.1.ttl",
            "pdks-json-to-ontology-mapping-0.1.json"
        ]
        if args.include_standards:
            for name in standard_files:
                p=ASSETS/name
                if p.exists():
                    data=p.read_bytes()
                    arc=Path("standards")/name
                    z.writestr(str(arc),data)
                    manifest_files.append({"path":str(arc),"size_bytes":len(data),"sha256":sha(data)})
        source_assets_included=0
        if args.source_assets:
            source_root=Path(args.source_assets).resolve()
            if not source_root.is_dir():
                raise SystemExit("source-assets directory does not exist")
            for source_file in sorted(source_root.rglob("*")):
                if not source_file.is_file():
                    continue
                data=source_file.read_bytes()
                rel=source_file.relative_to(source_root)
                arc=Path("source-assets")/rel
                z.writestr(arc.as_posix(),data)
                manifest_files.append({"path":arc.as_posix(),"size_bytes":len(data),"sha256":sha(data)})
                source_assets_included += 1
        manifest={
            "bundle_format":"PDKS-Export-Bundle",
            "bundle_version":"0.2.0",
            "pdks_standard_version":"0.1.0",
            "skill_version":"0.2.0",
            "exported_at":datetime.now(timezone.utc).isoformat(),
            "exported_by":args.exported_by,
            "record_counts":counts,
            "total_records":len(files),
            "files":manifest_files,
            "external_references":sorted(external_refs),
            "source_assets_included":source_assets_included,
            "excluded_sources":[],
            "notes":[
                "Source files are not included unless explicitly packaged by the caller.",
                "This bundle is an export artifact; it does not imply import into a destination system."
            ]
        }
        z.writestr("manifest.json",json.dumps(manifest,ensure_ascii=False,indent=2).encode("utf-8"))
    print(json.dumps({"output":str(out),"records":len(files),"counts":counts,"files":len(manifest_files)+1},ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
