"""Read-only Personal Memory / Intent / State context client."""
from __future__ import annotations
import json, os, urllib.error, urllib.request

BASE = os.environ.get("EIL_BASE_URL", "http://127.0.0.1:8765").rstrip("/")
SUBSCRIPTION_ID = os.environ["EIL_AGENT_SUBSCRIPTION_ID"]
TOKEN = os.environ["EIL_AGENT_TOKEN"]
API_TOKEN = os.environ.get("EIL_API_TOKEN")

def get(path: str):
    headers = {"X-Agent-Token": TOKEN, "Accept": "application/json"}
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    req = urllib.request.Request(BASE + path, method="GET", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')}") from exc

def main():
    prefix = f"/v1/agents/subscriptions/{SUBSCRIPTION_ID}"
    result = {
        "memories": get(prefix + "/memories?limit=50").get("items", []),
        "intents": get(prefix + "/intents?limit=50").get("items", []),
        "state": get(prefix + "/state?recent_event_limit=10"),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    # Read-only by design: no memory writes, intent transitions or external side effects.

if __name__ == "__main__":
    main()
