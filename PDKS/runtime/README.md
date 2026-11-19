# PDKS Personal Capture Runtime 0.1.1

Experimental local reference implementation for PDKS 0.5.1. It remains part of transitional Skill development.

## Install

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e runtime
```

## Initialize and run

```bash
pdks-runtime --db ./data/pdks.sqlite3 --vault ./data/vault init --owner urn:pdks:owner:me
pdks-runtime --db ./data/pdks.sqlite3 --vault ./data/vault token-create --owner urn:pdks:owner:me --agent-id agent-a --scopes capture:read,capture:write,records:read,records:propose
pdks-runtime --db ./data/pdks.sqlite3 --vault ./data/vault serve --host 127.0.0.1 --port 8765
```

The service binds to loopback only. It is not safe for public network exposure. Production encryption, remote Agent relay, and background device capture are not implemented.

## DWS Connector 0.1.0

The official DingTalk Workspace CLI connector is located in `pdks_capture_runtime/connectors/dws/`.

```bash
pdks-runtime --db ./data/pdks.sqlite3 --vault ./data/vault dws-doctor --profile <corpId:userId>
pdks-runtime --db ./data/pdks.sqlite3 --vault ./data/vault dws-event-catalog
pdks-runtime --db ./data/pdks.sqlite3 --vault ./data/vault dws-event-schema --event-key user_im_message_receive_at
pdks-runtime --db ./data/pdks.sqlite3 --vault ./data/vault dws-consume --owner urn:pdks:owner:me --consent-ref <PDKS_CONSENT_REF> --profile <corpId:userId> --event-key user_im_message_receive_at --max-events 3
```

The connector requires the official DWS CLI, DWS OAuth login, tenant CLI access, and an active PDKS Consent Grant. It does not perform historical pagination/backfill yet. No real user account or tenant delivery was verified in the local development environment.

See `../docs/19-PDKS_0.5.1_DWS官方CLI接入适配器设计与参考实现.md` for installation, event selection, consent and limitations.

## Synthetic end-to-end demo

From the `runtime/` directory after installation:

```bash
python examples/demo_local_flow.py
```

The demo uses only a temporary directory and synthetic meeting text; it exercises capture, candidate validation, owner approval, export and bundle verification.
