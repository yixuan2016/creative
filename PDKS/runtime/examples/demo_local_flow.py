from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import uuid

from pdks_capture_runtime.service import CaptureRuntime

def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

def main():
    with TemporaryDirectory(prefix="pdks-demo-") as td:
        base=Path(td)
        owner="urn:pdks:owner:demo"
        runtime=CaptureRuntime(base/"pdks.sqlite3",base/"vault")
        runtime.create_owner(owner)

        captured=runtime.capture_text(
            owner,
            "2026年11月19日，项目组召开内部会议，讨论个人采集入口。会议决定先验证手机端低门槛采集。",
            source_kind="manual",
            origin_system="demo-script",
            source_locator="demo://meeting/001",
            domain="work",
            sensitivity="personal_work"
        )

        record={
            "pdks_version":"0.1.0",
            "object_id":"urn:pdks:event:"+str(uuid.uuid4()),
            "object_type":"event",
            "created_at":utc_now(),
            "updated_at":utc_now(),
            "owner_ref":owner,
            "domains":["work"],
            "provenance":{
                "created_by":"urn:pdks:agent:demo",
                "source_refs":[captured["source_id"]]
            },
            "governance":{
                "sensitivity":"personal_work",
                "access_scope":"owner_only"
            },
            "lifecycle":{"status":"active","version":1},
            "payload":{
                "event_type":"work.meeting.internal_meeting",
                "event_taxonomy_version":"0.1.0",
                "description":"项目组讨论个人采集入口，并决定先验证手机端低门槛采集。",
                "start_at":"2026-11-19T00:00:00+08:00",
                "time_precision":"date_only"
            }
        }

        proposal=runtime.propose_records(owner,[record],[captured["source_id"]],"demo-agent")
        approval=runtime.approve_record(owner,record["object_id"],"demo-owner")
        export_path=base/"demo-export.zip"
        export=runtime.export_bundle(owner,export_path)
        verified=runtime.verify_bundle(export_path)

        print(json.dumps({
            "capture":captured,
            "proposal":proposal,
            "approval":approval,
            "export":{k:v for k,v in export.items() if k!="path"},
            "bundle_verified":verified["valid"],
            "demo_data_only":True
        },ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
