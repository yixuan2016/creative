#!/usr/bin/env python3
"""PDKS Agent-driven Bootstrap Engine 0.2.0 (experimental, local-only)."""
from __future__ import annotations
import argparse, hashlib, json, os, platform, shutil, subprocess, sys, tempfile, venv
from pathlib import Path
from typing import Any

SETUP_VERSION = "0.2.0"
PDKS_TRACK = "0.5.2.2"
RUNTIME_VERSION = "0.1.1"
OWNER_REF = "urn:pdks:owner:default"
REQUIRED_PYTHON = (3, 10)
DEPENDENCIES = ["jsonschema>=4.18,<5"]


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def default_install_root() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "PDKS" / PDKS_TRACK
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "PDKS" / PDKS_TRACK
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "pdks" / PDKS_TRACK


def bundle_root_from_script() -> Path:
    # <bundle>/skills/pdks-setup/scripts/pdks_setup.py
    return Path(__file__).resolve().parents[3]


def python_version_ok() -> bool:
    return sys.version_info >= REQUIRED_PYTHON


def default_vault_root() -> Path:
    # Use a visible folder directly under Home, avoiding common auto-synced Documents folders by default.
    return Path.home() / "PDKS-Vault"


def directory_state(path: Path, marker: str) -> str:
    if not path.exists():
        return "absent"
    if (path / marker).is_file():
        return "existing_pdks_install" if marker == "install.json" else "existing_pdks_vault"
    if any(path.iterdir()):
        return "non_empty_unmanaged_directory"
    return "empty_directory"


def detect_dws() -> str | None:
    return shutil.which("dws") or shutil.which("dws.exe")


def safe_under_home(path: Path) -> bool:
    home = Path.home().resolve()
    resolved = path.expanduser().resolve()
    return resolved == home or home in resolved.parents


def build_plan(bundle_root: Path, install_root: Path, vault_root: Path | None = None) -> dict[str, Any]:
    runtime_dir = bundle_root / "runtime"
    install_root = install_root.expanduser().resolve()
    vault_root = (vault_root or default_vault_root()).expanduser().resolve()
    existing_state = directory_state(install_root, "install.json")
    vault_state = directory_state(vault_root, "PDKS-MANIFEST.json")
    dws = detect_dws()
    plan = {
        "plan_version": "1",
        "setup_engine_version": SETUP_VERSION,
        "pdks_track": PDKS_TRACK,
        "capture_runtime_version": RUNTIME_VERSION,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "python_supported": python_version_ok(),
        "bundle_root": str(bundle_root.resolve()),
        "runtime_bundle_present": (runtime_dir / "pdks_capture_runtime" / "__main__.py").is_file(),
        "install_root": str(install_root),
        "install_root_state": existing_state,
        "vault_root": str(vault_root),
        "vault_root_state": vault_state,
        "dws_detected": bool(dws),
        "dws_path": dws,
        "actions": [
            "copy the bundled PDKS Runtime source into the user-level PDKS installation directory",
            "create an isolated Python virtual environment",
            "install the pinned dependency range jsonschema>=4.18,<5 from PyPI using binary wheels only",
            "initialize an empty local SQLite operational database and private-per-user blob store",
            "initialize a user-visible file-first PDKS Vault with Markdown, JSONL, ontology assets and a portable manifest",
            "create a local pdks-runtime launcher",
            "run a local health check",
        ],
        "not_included": [
            "no DingTalk login or OAuth token handling",
            "no data-source subscription or historical data import",
            "no background service or auto-start registration in this preview",
            "no cloud backup or network listener",
            "no encryption-at-rest; use only synthetic or non-sensitive test data",
        ],
        "network_access": ["PyPI package index for jsonschema and its dependencies"],
        "admin_privileges_required": False,
        "data_collection_enabled_by_default": False,
        "storage_warning": "SQLite and Vault are not encrypted at rest in this experimental Runtime. Do not collect sensitive work or personal data.",
    }
    plan["plan_sha256"] = sha256_bytes(canonical(plan))
    return plan


def doctor(bundle_root: Path, install_root: Path, vault_root: Path | None = None) -> dict[str, Any]:
    plan = build_plan(bundle_root, install_root, vault_root)
    checks = [
        {"name": "python_version", "ok": plan["python_supported"], "detail": plan["python_version"]},
        {"name": "runtime_bundle", "ok": plan["runtime_bundle_present"], "detail": str(bundle_root / "runtime")},
        {"name": "install_path_under_home", "ok": safe_under_home(install_root), "detail": str(install_root)},
        {"name": "install_path_available", "ok": plan["install_root_state"] in {"absent", "empty_directory"}, "detail": plan["install_root_state"]},
        {"name": "vault_path_under_home", "ok": safe_under_home(Path(plan["vault_root"])), "detail": plan["vault_root"]},
        {"name": "vault_path_available", "ok": plan["vault_root_state"] in {"absent", "empty_directory", "existing_pdks_vault"}, "detail": plan["vault_root_state"]},
        {"name": "pip_available", "ok": importlib_pip_available(), "detail": "python -m pip"},
    ]
    try:
        free = shutil.disk_usage(install_root.parent if install_root.parent.exists() else Path.home()).free
    except OSError:
        free = 0
    checks.append({"name": "disk_space_512mb", "ok": free >= 512 * 1024 * 1024, "detail": free})
    return {"status": "ready" if all(x["ok"] for x in checks) else "blocked", "checks": checks, "dws_detected": plan["dws_detected"], "dws_path": plan["dws_path"]}


def importlib_pip_available() -> bool:
    try:
        import pip  # noqa: F401
        return True
    except Exception:
        return False


def run_checked(argv: list[str], *, env: dict[str, str] | None = None) -> None:
    result = subprocess.run(argv, env=env, shell=False, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"A required installation step failed (exit {result.returncode}): {Path(argv[0]).name}")


def initialize_file_vault(runtime_python: Path, bundle_root: Path, vault_root: Path, env: dict[str, str]) -> dict[str, Any]:
    """Initialize the portable Vault and seed versioned ontology files without overwriting user edits."""
    run_checked([str(runtime_python), "-m", "pdks_capture_runtime", "vault-init", "--file-vault", str(vault_root)], env=env)
    ontology_source = bundle_root / "skills" / "pdks-personal-knowledge" / "assets" / "ontology" / "0.2.1"
    ontology_target = vault_root / ".pdks" / "ontology" / "0.2.1"
    copied = 0
    if ontology_source.is_dir():
        ontology_target.mkdir(parents=True, exist_ok=True)
        for ontology_file in ontology_source.rglob("*"):
            if ontology_file.is_file():
                relative = ontology_file.relative_to(ontology_source)
                destination = ontology_target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                if not destination.exists():
                    shutil.copy2(ontology_file, destination)
                    copied += 1
    config_dir = vault_root / ".pdks" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    runtime_config = {
        "pdks_track": PDKS_TRACK,
        "runtime_version": RUNTIME_VERSION,
        "standard_version": "0.1.0",
        "record_schema_version": "0.1.x",
        "ontology_version": "0.2.1",
        "event_taxonomy_version": "0.1.0",
        "storage_mode": "file-first-vault-plus-local-runtime-db",
        "default_capture_enabled": False,
        "cloud_sync_enabled": False,
        "sensitive_data_allowed": False,
    }
    runtime_config_path = config_dir / "runtime.json"
    config_created = not runtime_config_path.exists()
    if config_created:
        runtime_config_path.write_text(json.dumps(runtime_config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"vault_root": str(vault_root), "ontology_files_added": copied, "runtime_config_created": config_created}


def write_launcher(staging_root: Path, final_root: Path) -> Path:
    bin_dir = staging_root / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        launcher = bin_dir / "pdks-runtime.cmd"
        text = (
            "@echo off\r\n"
            f'"{final_root / "venv" / "Scripts" / "python.exe"}" -m pdks_capture_runtime '
            f'--db "{final_root / "data" / "pdks.sqlite3"}" --vault "{final_root / "data" / "vault"}" %*\r\n'
        )
    else:
        launcher = bin_dir / "pdks-runtime"
        text = f'''#!/bin/sh
set -eu
ROOT="{final_root}"
export PYTHONPATH="$ROOT/runtime${{PYTHONPATH:+:$PYTHONPATH}}"
exec "$ROOT/venv/bin/python" -m pdks_capture_runtime --db "$ROOT/data/pdks.sqlite3" --vault "$ROOT/data/vault" "$@"
'''
    launcher.write_text(text, encoding="utf-8")
    if os.name != "nt":
        launcher.chmod(0o700)
    return launcher


def install(bundle_root: Path, install_root: Path, approved_hash: str, acknowledge_storage_risk: bool, vault_root: Path | None = None) -> dict[str, Any]:
    plan = build_plan(bundle_root, install_root, vault_root)
    if approved_hash != plan["plan_sha256"]:
        raise PermissionError("The approved plan hash does not match the current plan. Re-run `plan` and ask the user to approve again.")
    if not acknowledge_storage_risk:
        raise PermissionError("This experimental Runtime uses unencrypted local storage. Obtain explicit user acknowledgement before installation.")
    result = doctor(bundle_root, install_root, vault_root)
    blocked = [x for x in result["checks"] if not x["ok"]]
    if blocked:
        raise RuntimeError("Preflight blocked: " + "; ".join(f"{x['name']}={x['detail']}" for x in blocked))
    final_root = install_root.expanduser().resolve()
    if final_root.exists() and any(final_root.iterdir()):
        raise FileExistsError("Install target is not empty; this installer will not overwrite or delete existing files.")
    final_root.parent.mkdir(parents=True, exist_ok=True)
    import uuid
    staging = final_root.parent / f".{final_root.name}.staging-{uuid.uuid4().hex}"
    staging.mkdir(mode=0o700)
    try:
        shutil.copytree(bundle_root / "runtime", staging / "runtime", dirs_exist_ok=False)
        venv_dir = staging / "venv"
        venv.EnvBuilder(with_pip=True, clear=False).create(venv_dir)
        py = venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        # Install only the runtime's required dependency; no global packages and no source distributions.
        run_checked([str(py), "-m", "pip", "--disable-pip-version-check", "--no-input", "install", "--only-binary=:all:", *DEPENDENCIES])
        data_dir = staging / "data"
        vault_dir = data_dir / "vault"
        data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        vault_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        launcher = write_launcher(staging, final_root)
        env = os.environ.copy()
        env["PYTHONPATH"] = str(staging / "runtime")
        run_checked([str(py), "-m", "pdks_capture_runtime", "--db", str(data_dir / "pdks.sqlite3"), "--vault", str(vault_dir), "init", "--owner", OWNER_REF], env=env)
        # The portable file-first Vault is initialized separately from the operational DB.
        # Existing PDKS Vaults may be reused; unmanaged non-empty folders were blocked in preflight.
        file_vault_root = Path(plan["vault_root"])
        vault_setup_result = initialize_file_vault(py, bundle_root, file_vault_root, env)
        # Verify import and CLI parser without starting a service or collecting data.
        run_checked([str(py), "-m", "pdks_capture_runtime", "--help"], env=env)
        metadata = {
            "setup_engine_version": SETUP_VERSION,
            "pdks_track": PDKS_TRACK,
            "capture_runtime_version": RUNTIME_VERSION,
            "owner_ref": OWNER_REF,
            "install_root": str(final_root),
            "file_vault_root": str(plan["vault_root"]),
            "ontology_version": "0.2.1",
            "file_vault_setup": vault_setup_result,
            "launcher": str(final_root / "bin" / launcher.name),
            "installed_at_epoch": int(__import__("time").time()),
            "data_collection_enabled": False,
            "storage_encryption": "not_available_in_runtime_0.1.1",
            "experimental": True,
        }
        (staging / "install.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        try:
            if os.name != "nt":
                staging.chmod(0o700); data_dir.chmod(0o700); vault_dir.chmod(0o700)
                (data_dir / "pdks.sqlite3").chmod(0o600)
        except OSError:
            pass
        # If the user created an empty target directory after reviewing the plan, remove only that empty directory.
        if final_root.exists():
            final_root.rmdir()
        os.replace(staging, final_root)
        return {"status": "installed", "install_root": str(final_root), "file_vault_root": plan["vault_root"], "launcher": str(final_root / "bin" / launcher.name), "data_collection_enabled": False, "warning": plan["storage_warning"]}
    except Exception:
        # The final target remains untouched. Only this uniquely named staging directory is removed.
        shutil.rmtree(staging, ignore_errors=True)
        raise


def verify(install_root: Path, vault_root: Path | None = None) -> dict[str, Any]:
    root = install_root.expanduser().resolve()
    meta_path = root / "install.json"
    if not meta_path.is_file():
        return {"status": "not_installed", "install_root": str(root)}
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    py = root / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    launcher = Path(meta["launcher"])
    file_vault = Path(vault_root).expanduser().resolve() if vault_root else Path(meta.get("file_vault_root", default_vault_root())).expanduser().resolve()
    checks = [
        {"name": "metadata", "ok": meta.get("pdks_track") == PDKS_TRACK},
        {"name": "runtime_source", "ok": (root / "runtime" / "pdks_capture_runtime" / "__main__.py").is_file()},
        {"name": "python_environment", "ok": py.is_file()},
        {"name": "launcher", "ok": launcher.is_file()},
        {"name": "database", "ok": (root / "data" / "pdks.sqlite3").is_file()},
        {"name": "blob_vault", "ok": (root / "data" / "vault").is_dir()},
        {"name": "file_vault", "ok": (file_vault / "PDKS-MANIFEST.json").is_file(), "detail": str(file_vault)},
    ]
    env = os.environ.copy(); env["PYTHONPATH"] = str(root / "runtime")
    if py.is_file():
        p = subprocess.run([str(py), "-m", "pdks_capture_runtime", "--help"], env=env, capture_output=True, text=True, shell=False)
        checks.append({"name": "runtime_cli", "ok": p.returncode == 0})
    return {"status": "healthy" if all(x["ok"] for x in checks) else "degraded", "checks": checks, "data_collection_enabled": False}


def main() -> int:
    parser = argparse.ArgumentParser(description="PDKS Agent-driven Bootstrap Engine 0.2.0")
    parser.add_argument("--bundle-root", type=Path, default=bundle_root_from_script())
    parser.add_argument("--install-root", type=Path, default=default_install_root())
    parser.add_argument("--vault-root", type=Path, default=default_vault_root())
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    sub.add_parser("plan")
    p = sub.add_parser("install"); p.add_argument("--approve-plan", required=True); p.add_argument("--acknowledge-unencrypted-storage", action="store_true")
    p = sub.add_parser("verify")
    p = sub.add_parser("uninstall-plan")
    args = parser.parse_args()
    if not safe_under_home(args.install_root):
        raise SystemExit("Blocked: install root must be inside the current user's home directory.")
    if not safe_under_home(args.vault_root):
        raise SystemExit("Blocked: Vault root must be inside the current user's home directory.")
    if args.command == "doctor":
        result = doctor(args.bundle_root, args.install_root, args.vault_root)
    elif args.command == "plan":
        result = build_plan(args.bundle_root, args.install_root, args.vault_root)
    elif args.command == "install":
        result = install(args.bundle_root, args.install_root, args.approve_plan, args.acknowledge_unencrypted_storage, args.vault_root)
    elif args.command == "verify":
        result = verify(args.install_root, args.vault_root)
    elif args.command == "uninstall-plan":
        result = {"status": "dry_run_only", "install_root": str(args.install_root.resolve()), "would_remove": "PDKS application files only", "preserve": ["data directory", "SQLite database", "Vault", "exports", "backups"], "note": "No uninstall or deletion command is implemented in this preview."}
    else:
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") not in {"blocked", "degraded", "not_installed"} else 1

if __name__ == "__main__":
    raise SystemExit(main())
