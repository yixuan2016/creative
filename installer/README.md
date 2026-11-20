# PDKS Installer and Bootstrap

The Node-native Bootstrap 0.2.0 initializes a local File-first Vault without requiring Python. The Agent Bridge installer installs npm dependencies and builds the optional MCP Apps UI; it does not automatically edit host Agent configuration.

Platform scripts:
- `setup/install-agent-bridge.sh`
- `setup/install-agent-bridge.ps1`
- `setup/pdks-setup.sh`
- `setup/pdks-setup.ps1`

The first install is not yet a signed, self-contained one-click installer. Node.js 22.12+ and npm are prerequisites. Read the exact plan before running mutating steps.
