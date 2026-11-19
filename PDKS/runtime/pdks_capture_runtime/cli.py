from __future__ import annotations
import argparse
import json
from pathlib import Path
from .service import CaptureRuntime
from .api import serve
from .models import API_SCOPES
from .connectors.dws import DWSCLI, DWSConsumer, DWSConnector, resolve_event_key
from .file_store import FileFirstVault

DEFAULT_SCOPES="capture:read,capture:write,records:read,records:propose"

def start_dws_consumer_after_preflight(connector, consumer, event_keys):
    """Run all consent/auth/profile/schema checks before creating a DWS subscription."""
    preflight = connector.validate_preflight(event_keys)
    consumer.start()
    return preflight


def runtime_from(args):
    return CaptureRuntime(args.db,args.vault,args.schema)

def main():
    ap=argparse.ArgumentParser(prog="pdks-runtime",description="PDKS Personal Capture Runtime 0.1.1 (experimental)")
    ap.add_argument("--db",default="./data/pdks-capture.sqlite3")
    ap.add_argument("--vault",default="./data/pdks-vault")
    ap.add_argument("--schema",default=None)
    sub=ap.add_subparsers(dest="command",required=True)
    p=sub.add_parser("init"); p.add_argument("--owner",required=True)
    p=sub.add_parser("token-create"); p.add_argument("--owner",required=True); p.add_argument("--agent-id",required=True); p.add_argument("--scopes",default=DEFAULT_SCOPES)
    p=sub.add_parser("token-revoke"); p.add_argument("--owner",required=True); p.add_argument("--agent-id",required=True)
    p=sub.add_parser("consent-create"); p.add_argument("--owner",required=True); p.add_argument("--source-kind",required=True)
    p.add_argument("--domain",required=True); p.add_argument("--expires-at"); p.add_argument("--note",default="")
    p=sub.add_parser("consent-revoke"); p.add_argument("--owner",required=True); p.add_argument("--consent-ref",required=True)
    p=sub.add_parser("approve-record"); p.add_argument("--owner",required=True); p.add_argument("--record-id",required=True)
    p=sub.add_parser("serve"); p.add_argument("--host",default="127.0.0.1"); p.add_argument("--port",type=int,default=8765)
    p=sub.add_parser("capture-text"); p.add_argument("--owner",required=True); p.add_argument("--text",required=True)
    p.add_argument("--source-kind",default="manual"); p.add_argument("--domain",default="other")
    p.add_argument("--origin-system",default="manual_entry"); p.add_argument("--sensitivity",default="personal_private")
    p=sub.add_parser("capture-file"); p.add_argument("--owner",required=True); p.add_argument("--file",required=True)
    p.add_argument("--source-kind",default="manual"); p.add_argument("--domain",default="other")
    p.add_argument("--sensitivity",default="personal_private"); p.add_argument("--consent-ref")
    p=sub.add_parser("list-captures"); p.add_argument("--owner",required=True)
    p=sub.add_parser("export"); p.add_argument("--owner",required=True); p.add_argument("--output",required=True)
    p.add_argument("--include-candidates",action="store_true"); p.add_argument("--include-raw-sources",action="store_true")
    p=sub.add_parser("delete-source"); p.add_argument("--owner",required=True); p.add_argument("--source-id",required=True)
    p=sub.add_parser("verify-bundle"); p.add_argument("--file",required=True)

    p=sub.add_parser("vault-init", help="Initialize a portable File-first PDKS Vault")
    p.add_argument("--file-vault",default="./PDKS-Vault")
    p=sub.add_parser("vault-sync", help="Project current Runtime knowledge/source records into a portable PDKS Vault")
    p.add_argument("--owner",required=True); p.add_argument("--file-vault",default="./PDKS-Vault")
    p.add_argument("--include-candidates",action="store_true")
    p.add_argument("--include-raw-sources",action="store_true")
    p=sub.add_parser("vault-verify", help="Verify portable PDKS Vault manifest and file hashes")
    p.add_argument("--file-vault",default="./PDKS-Vault")
    p=sub.add_parser("vault-rebuild-index", help="Rebuild the disposable SQLite file index from Markdown/JSONL/assets")
    p.add_argument("--file-vault",default="./PDKS-Vault")

    p=sub.add_parser("dws-doctor", help="Check official DWS CLI version and read-only login status")
    p.add_argument("--dws-bin",default="dws"); p.add_argument("--profile")
    p=sub.add_parser("dws-event-catalog", help="Read the official DWS personal event catalog")
    p.add_argument("--dws-bin",default="dws"); p.add_argument("--profile"); p.add_argument("--category")
    p=sub.add_parser("dws-event-schema", help="Read the official schema for a supported personal event")
    p.add_argument("--dws-bin",default="dws"); p.add_argument("--profile"); p.add_argument("--event-key",required=True)
    p=sub.add_parser("dws-command-schema", help="Discover a reviewed read-only DWS command schema for future backfill")
    p.add_argument("--dws-bin",default="dws"); p.add_argument("--profile"); p.add_argument("--command-path",required=True)
    p=sub.add_parser("dws-consume", help="Capture DWS personal stream events into the local PDKS Runtime")
    p.add_argument("--owner",required=True); p.add_argument("--consent-ref",required=True)
    p.add_argument("--profile",required=True); p.add_argument("--dws-bin",default="dws")
    p.add_argument("--event-key",action="append",required=True)
    p.add_argument("--user"); p.add_argument("--open-dingtalk-id"); p.add_argument("--group")
    p.add_argument("--role-types",help="Comma-separated Todo roles: creator,executor,participant")
    p.add_argument("--calendar-ids",help="Comma-separated calendar IDs; use primary for the main calendar")
    p.add_argument("--change-types",help="Comma-separated eventCreated,eventUpdated,eventCancelled")
    p.add_argument("--duration",help="Optional bounded run, e.g. 10m; omit for continuous capture")
    p.add_argument("--max-events",type=int); p.add_argument("--sensitivity",default="personal_work")
    p=sub.add_parser("dws-minutes-summary", help="Explicitly fetch and capture one DWS AI minutes summary")
    p.add_argument("--owner",required=True); p.add_argument("--consent-ref",required=True)
    p.add_argument("--profile",required=True); p.add_argument("--task-uuid",required=True)
    p.add_argument("--dws-bin",default="dws"); p.add_argument("--sensitivity",default="personal_work")
    args=ap.parse_args()
    if args.command=="verify-bundle":
        rt=runtime_from(args); result=rt.verify_bundle(args.file)
    elif args.command=="vault-init":
        result=FileFirstVault(args.file_vault).initialize()
    elif args.command=="vault-sync":
        rt=runtime_from(args)
        result=FileFirstVault(args.file_vault).sync_from_runtime(
            rt,args.owner,args.include_candidates,args.include_raw_sources)
    elif args.command=="vault-verify":
        result=FileFirstVault(args.file_vault).verify_manifest()
    elif args.command=="vault-rebuild-index":
        result=FileFirstVault(args.file_vault).rebuild_index()
    elif args.command=="dws-doctor":
        cli=DWSCLI(binary=args.dws_bin,profile=args.profile)
        result={"cli":cli.version(),"auth_status":cli.auth_status(),
                "note":"Auth status uses DWS read-only snapshot; it does not refresh credentials or prove event delivery is enabled."}
    elif args.command=="dws-event-catalog":
        result=DWSCLI(binary=args.dws_bin,profile=args.profile).event_catalog(args.category)
    elif args.command=="dws-event-schema":
        result=DWSCLI(binary=args.dws_bin,profile=args.profile).event_schema(args.event_key)
    elif args.command=="dws-command-schema":
        result=DWSCLI(binary=args.dws_bin,profile=args.profile).command_schema(args.command_path)
    elif args.command=="dws-consume":
        rt=runtime_from(args)
        cli=DWSCLI(binary=args.dws_bin,profile=args.profile)
        connector=DWSConnector(rt,args.owner,args.consent_ref,args.profile,
                               sensitivity=args.sensitivity,cli=cli)
        consumer=DWSConsumer(
            cli,args.event_key,user=args.user,open_dingtalk_id=args.open_dingtalk_id,
            group=args.group,role_types=[x.strip() for x in args.role_types.split(",") if x.strip()] if args.role_types else None,
            calendar_ids=[x.strip() for x in args.calendar_ids.split(",") if x.strip()] if args.calendar_ids else None,
            change_types=[x.strip() for x in args.change_types.split(",") if x.strip()] if args.change_types else None,
            duration=args.duration,max_events=args.max_events,
        )
        try:
            preflight = start_dws_consumer_after_preflight(connector, consumer, args.event_key)
            ready=consumer.wait_ready()
            print(json.dumps({"status":"listening","ready":ready,"event_keys":args.event_key,"profile":args.profile,"preflight":preflight},ensure_ascii=False),flush=True)
            accepted=duplicates=0
            for event in consumer.iter_events():
                event_key=resolve_event_key(event,args.event_key)
                captured=connector.ingest_event(event_key,event)
                if captured.get("duplicate"):
                    duplicates+=1
                else:
                    accepted+=1
                print(json.dumps({"status":"captured","event_key":event_key,"capture":captured},ensure_ascii=False),flush=True)
            if consumer.process is not None and consumer.process.returncode not in (None,0):
                raise RuntimeError(f"DWS consumer exited with code {consumer.process.returncode}")
            result={"status":"completed","accepted":accepted,"duplicates":duplicates,
                    "subscribe_ids":consumer.subscribe_ids}
        except KeyboardInterrupt:
            result={"status":"stopping","reason":"keyboard_interrupt"}
        finally:
            stopped=consumer.stop()
        if result.get("status") == "completed" and stopped.get("returncode") not in (None, 0):
            raise RuntimeError(f"DWS consumer exited with code {stopped.get('returncode')}")
        result={**result,"consumer_stop":stopped}
    elif args.command=="dws-minutes-summary":
        rt=runtime_from(args)
        cli=DWSCLI(binary=args.dws_bin,profile=args.profile)
        connector=DWSConnector(rt,args.owner,args.consent_ref,args.profile,sensitivity=args.sensitivity,cli=cli)
        connector.validate_preflight([])
        result=connector.enrich_minutes_summary(args.task_uuid)
    else:
        rt=runtime_from(args)
        if args.command=="init": result=rt.create_owner(args.owner)
        elif args.command=="token-create":
            scopes=[x.strip() for x in args.scopes.split(",") if x.strip()]
            result=rt.issue_token(args.owner,args.agent_id,scopes)
        elif args.command=="token-revoke": result=rt.revoke_token(args.owner,args.agent_id)
        elif args.command=="consent-create":
            result=rt.create_consent(args.owner,args.source_kind,["personal_knowledge_capture"],["read"],[args.domain],["capture"],args.expires_at,args.note)
        elif args.command=="consent-revoke": result=rt.revoke_consent(args.owner,args.consent_ref)
        elif args.command=="approve-record": result=rt.approve_record(args.owner,args.record_id)
        elif args.command=="serve": return serve(rt,args.host,args.port)
        elif args.command=="capture-text": result=rt.capture_text(args.owner,args.text,args.source_kind,args.origin_system,domain=args.domain,sensitivity=args.sensitivity)
        elif args.command=="capture-file":
            p=Path(args.file); result=rt.capture_file(args.owner,p.name,p.read_bytes(),source_kind=args.source_kind,domain=args.domain,sensitivity=args.sensitivity,consent_ref=args.consent_ref)
        elif args.command=="list-captures": result={"items":rt.list_captures(args.owner)}
        elif args.command=="export": result=rt.export_bundle(args.owner,args.output,args.include_candidates,args.include_raw_sources)
        elif args.command=="delete-source": result=rt.delete_source(args.owner,args.source_id)
        else: raise SystemExit("Unknown command")
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
