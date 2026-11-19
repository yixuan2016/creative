# Platform prerequisites and behavior

## Supported in PDKS Agent-native Bootstrap 0.5.2.2 preview

- Windows 10/11 x64, macOS and Linux with Node.js 22.12+ and npm for the Agent Bridge.
- Python 3.10+ and pip remain required by the existing Capture Runtime Bootstrap Engine.
- No managed Python runtime is bundled; the Agent must not silently install Python.

The engine refuses to write outside the current user's home directory and never requests administrator/root privileges. It refuses to overwrite a non-empty unmanaged directory.

## Network

The local Runtime dependency `jsonschema>=4.18,<5` and its dependencies are installed from PyPI using binary wheels only. The plan explicitly lists this network access. No PDKS data is uploaded.

## Storage warning

Capture Runtime 0.1.1 does not provide encryption-at-rest. Bootstrap creates user-restricted directories and file permissions where supported, but filesystem permissions are not encryption. This release is suitable only for synthetic or non-sensitive evaluation data. Do not enable real work-data collection until the storage security work is complete.

## Not yet included

- Automatic host-specific MCP config file modification.
- Host-by-host MCP Apps rendering certification.

- Native signed Windows MSI or macOS notarized PKG/DMG.
- Embedded Python runtime; Python 3.10+ is a prerequisite.
- Automatic background service, auto-start, watchdog, and reconnect manager.
- Automatic DWS installation and OAuth flow.
- Historical backfill, encryption-at-rest, cloud backup, and multi-device sync.


## If Python is missing

The Agent should offer a separate, user-approved prerequisite installation. Prefer current-user scope. On Windows, use the official Python package through winget if available; on macOS, use Homebrew only if already present or the official python.org installer; on Linux, do not invoke sudo automatically. If admin privileges are required, pause and ask the user. After installation, restart the shell and rerun `doctor`.
