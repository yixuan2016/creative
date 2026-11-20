# PDKS Personal Capture Runtime 0.1.1

Experimental local reference implementation in the transitional Skill development track.

## Install
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e runtime
```

## Initialize and run
```bash
pdks-runtime --db ./data/pdks.sqlite3 --vault ./data/vault init --owner urn:pdks:owner:me
pdks-runtime --db ./data/pdks.sqlite3 --vault ./data/vault serve --host 127.0.0.1 --port 8765
```

The service binds to loopback only. It is not safe for public network exposure. Encryption, remote Agent relay and background device capture are not implemented.

## DWS connector
The official DingTalk Workspace CLI connector is under `pdks_capture_runtime/connectors/dws/`. It requires the official DWS CLI, OAuth login, tenant CLI access and an active PDKS Consent Grant. Historical pagination/backfill and real tenant validation are not complete.

Native Vault initialization does not require Python. This Capture Runtime remains a separate optional component.
