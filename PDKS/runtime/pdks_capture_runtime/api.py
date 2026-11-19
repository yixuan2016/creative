from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs, unquote
import base64
import json
import re

from .errors import (
    AuthorizationError, ConsentRequiredError, ConflictError,
    NotFoundError, PayloadTooLargeError, ValidationError
)
from .models import Principal
from .service import CaptureRuntime, MAX_CAPTURE_BYTES

MAX_REQUEST_BYTES = 15 * 1024 * 1024

def make_handler(runtime: CaptureRuntime):
    class Handler(BaseHTTPRequestHandler):
        server_version = "PDKS-Capture-Runtime/0.1.1"
        def log_message(self, fmt, *args):
            # Avoid logging request bodies, bearer tokens, filenames or personal content.
            super().log_message(fmt, *args)

        def _send(self, status, payload):
            raw=json.dumps(payload,ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type","application/json; charset=utf-8")
            self.send_header("Content-Length",str(len(raw)))
            self.send_header("Cache-Control","no-store")
            self.end_headers()
            self.wfile.write(raw)

        def _body(self):
            length=int(self.headers.get("Content-Length","0"))
            if length > MAX_REQUEST_BYTES: raise PayloadTooLargeError("Request body too large")
            raw=self.rfile.read(length)
            try: return json.loads(raw.decode("utf-8")) if raw else {}
            except Exception as exc: raise ValidationError("Request body must be valid JSON") from exc

        def _principal(self, scope):
            auth=self.headers.get("Authorization","")
            if not auth.startswith("Bearer "): raise AuthorizationError("Bearer token required")
            principal=runtime.authenticate(auth[7:].strip())
            runtime._require_scope(principal,scope)
            return principal

        def _handle(self):
            parsed=urlparse(self.path)
            path=unquote(parsed.path)
            query=parse_qs(parsed.query)
            if self.command=="GET" and path=="/health":
                return self._send(200,{"status":"ok","runtime_version":"0.1.1","stage":"transitional_skill_development"})
            if self.command=="GET" and path=="/v1/captures":
                p=self._principal("capture:read")
                return self._send(200,{"items":runtime.list_captures(p.owner_ref)})
            if self.command=="POST" and path=="/v1/captures/text":
                p=self._principal("capture:write"); body=self._body()
                text=body.get("text")
                if text is None: raise ValidationError("text is required")
                allowed={"source_kind","origin_system","source_locator","domain","sensitivity",
                         "capture_method","consent_ref","occurred_at","idempotency_key","declared_source_type"}
                metadata={k:v for k,v in body.items() if k in allowed}
                result=runtime.capture_from_principal(p,{"text":text,**metadata})
                return self._send(201,result)
            if self.command=="POST" and path=="/v1/captures/file":
                p=self._principal("capture:write"); body=self._body()
                name=body.get("filename","upload.bin")
                encoded=body.get("content_base64")
                if not encoded: raise ValidationError("content_base64 is required")
                try: data=base64.b64decode(encoded,validate=True)
                except Exception as exc: raise ValidationError("content_base64 is invalid") from exc
                allowed={"source_kind","origin_system","source_locator","domain","sensitivity",
                         "capture_method","consent_ref","occurred_at","idempotency_key","declared_source_type"}
                metadata={k:v for k,v in body.items() if k in allowed}
                result=runtime.capture_file(p.owner_ref,name,data,actor_id=p.agent_id,**metadata)
                return self._send(201,result)
            if self.command=="GET" and path.startswith("/v1/captures/"):
                p=self._principal("capture:read")
                cid=path[len("/v1/captures/"):]
                return self._send(200,runtime.get_capture_for_principal(p,cid))
            if self.command=="POST" and path=="/v1/records/propose":
                p=self._principal("records:propose")
                return self._send(201,runtime.propose_for_principal(p,self._body()))
            if self.command=="GET" and path=="/v1/records":
                p=self._principal("records:read")
                state=query.get("review_state",["accepted"])[0]
                return self._send(200,{"items":runtime.list_records(p.owner_ref,state)})
            if self.command=="GET" and path.startswith("/v1/records/"):
                p=self._principal("records:read")
                rid=path[len("/v1/records/"):]
                return self._send(200,runtime.get_record_for_principal(p,rid))
            if self.command=="POST" and path.startswith("/v1/records/") and path.endswith("/approve"):
                p=self._principal("records:approve")
                rid=path[len("/v1/records/"):-len("/approve")].rstrip("/")
                return self._send(200,runtime.approve_for_principal(p,rid))
            if self.command=="POST" and path=="/v1/consents":
                p=self._principal("consent:manage")
                body=self._body()
                allowed={"source_kind","purposes","scopes","data_categories","actions","expires_at","note"}
                payload={k:v for k,v in body.items() if k in allowed}
                return self._send(201,runtime.create_consent_from_principal(p,payload))
            if self.command=="POST" and path.startswith("/v1/consents/") and path.endswith("/revoke"):
                p=self._principal("consent:manage")
                cref=path[len("/v1/consents/"):-len("/revoke")].rstrip("/")
                return self._send(200,runtime.revoke_consent(p.owner_ref,cref,p.agent_id))
            if self.command=="DELETE" and path.startswith("/v1/sources/"):
                p=self._principal("data:delete")
                sid=path[len("/v1/sources/"):]
                return self._send(200,runtime.delete_source(p.owner_ref,sid,p.agent_id))
            if self.command=="POST" and path=="/v1/export":
                p=self._principal("data:export"); body=self._body()
                output_name=body.get("output_name","pdks-export.zip")
                if not isinstance(output_name,str) or not output_name or output_name in {".",".."} or "/" in output_name or "\\\\" in output_name:
                    raise ValidationError("output_name must be a simple filename")
                export_dir=runtime.vault_dir.parent/"exports"
                output_path=export_dir/output_name
                return self._send(200,runtime.export_bundle(p.owner_ref,output_path,
                    bool(body.get("include_candidates",False)),bool(body.get("include_raw_sources",False))))
            return self._send(404,{"error":"not_found","message":"Unknown endpoint"})

        def _dispatch(self):
            try: self._handle()
            except ConsentRequiredError as exc: self._send(403,{"error":"consent_required","message":str(exc)})
            except AuthorizationError as exc: self._send(403,{"error":"authorization_error","message":str(exc)})
            except NotFoundError as exc: self._send(404,{"error":"not_found","message":str(exc)})
            except ConflictError as exc: self._send(409,{"error":"conflict","message":str(exc)})
            except PayloadTooLargeError as exc: self._send(413,{"error":"payload_too_large","message":str(exc)})
            except ValidationError as exc: self._send(422,{"error":"validation_error","message":str(exc)})
            except Exception as exc: self._send(500,{"error":"internal_error","message":str(exc)})

        do_GET=_dispatch
        do_POST=_dispatch
        do_DELETE=_dispatch
    return Handler

def serve(runtime: CaptureRuntime, host="127.0.0.1", port=8765):
    if host not in {"127.0.0.1","::1","localhost"}:
        raise ValueError("The 0.1.1 reference runtime only binds to loopback. Remote/TLS deployment is not implemented.")
    server=ThreadingHTTPServer((host,port),make_handler(runtime))
    print(f"PDKS Capture Runtime listening on http://{host}:{port} (loopback only)")
    server.serve_forever()
