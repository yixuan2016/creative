#!/bin/sh
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
if [ "${1:-}" != "--confirm" ] || [ "${2:-}" != "INSTALL PDKS AGENT BRIDGE" ]; then
  cat <<'PLAN'
PDKS Agent Bridge installation plan
- Install npm dependencies locally under agent-native/ (official MCP Server, MCP Apps, Zod, Vite build toolchain).
- Network: npm registry only for package installation.
- Build the MCP Apps setup panel into agent-native/dist/.
- Do not modify Agent configuration files.
- Do not install or connect DWS; do not start data collection or background services.
- No administrator privileges are requested.

To proceed, the user must explicitly approve and the Agent must rerun:
  ./setup/install-agent-bridge.sh --confirm "INSTALL PDKS AGENT BRIDGE"
PLAN
  exit 3
fi
NODE="$(command -v node || true)"
NPM="$(command -v npm || true)"
if [ -z "$NODE" ] || [ -z "$NPM" ]; then
  echo "PDKS Agent Bridge requires Node.js 22.12+ and npm. No system changes were made." >&2
  exit 2
fi
VERSION="$($NODE -p 'process.versions.node')"
MAJOR="$(printf '%s' "$VERSION" | cut -d. -f1)"
MINOR="$(printf '%s' "$VERSION" | cut -d. -f2)"
if [ "$MAJOR" -lt 22 ] || { [ "$MAJOR" -eq 22 ] && [ "$MINOR" -lt 12 ]; }; then
  echo "Node.js 22.12+ is required for the selected MCP Apps build toolchain; found $VERSION. No system changes were made." >&2
  exit 2
fi
cd "$ROOT/agent-native"
"$NPM" install
"$NPM" run build
"$NODE" ./bin/pdks-agent.js config --host generic
