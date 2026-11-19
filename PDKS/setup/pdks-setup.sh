#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
PY=""
for CANDIDATE in python3 python; do
  if command -v "$CANDIDATE" >/dev/null 2>&1 && "$CANDIDATE" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' >/dev/null 2>&1; then
    PY="$(command -v "$CANDIDATE")"
    break
  fi
done
if [ -z "$PY" ]; then
  echo "PDKS Setup requires Python 3.10+. No Python installation was changed." >&2
  echo "Ask your Agent to install Python 3.12 for the current user, then rerun this command." >&2
  exit 2
fi
exec "$PY" "$ROOT/skills/pdks-setup/scripts/pdks_setup.py" --bundle-root "$ROOT" "$@"
