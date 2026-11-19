"""Minimal standard-library HTTP client usable by host-specific Agent adapters."""
from __future__ import annotations
import json
import urllib.request
import urllib.error

class PDKSCaptureClient:
    def __init__(self, base_url: str, bearer_token: str, timeout=20):
        self.base_url=base_url.rstrip("/")
        self.token=bearer_token
        self.timeout=timeout

    def request(self, method: str, path: str, payload=None):
        data=None if payload is None else json.dumps(payload,ensure_ascii=False).encode("utf-8")
        req=urllib.request.Request(self.base_url+path,data=data,method=method,
            headers={"Authorization":"Bearer "+self.token,"Content-Type":"application/json"})
        try:
            with urllib.request.urlopen(req,timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body=exc.read().decode("utf-8",errors="replace")
            raise RuntimeError(f"PDKS Runtime HTTP {exc.code}: {body}") from exc

    def capture_text(self, text, **metadata):
        return self.request("POST","/v1/captures/text",{"text":text,**metadata})

    def capture_file(self, filename, data: bytes, **metadata):
        payload={"filename":filename,"content_base64":base64.b64encode(data).decode("ascii"),**metadata}
        return self.request("POST","/v1/captures/file",payload)

    def get_capture(self, capture_id):
        return self.request("GET","/v1/captures/"+capture_id.replace(":","%3A"))

    def get_record(self, record_id):
        return self.request("GET","/v1/records/"+record_id.replace(":","%3A"))

    def list_captures(self):
        return self.request("GET","/v1/captures")

    def propose_records(self, records, source_ids):
        return self.request("POST","/v1/records/propose",{"records":records,"source_ids":source_ids})

    def list_records(self, review_state="accepted"):
        return self.request("GET","/v1/records?review_state="+review_state)

    def approve_record(self, record_id):
        return self.request("POST","/v1/records/"+record_id.replace(":","%3A")+"/approve",{})
