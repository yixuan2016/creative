from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class FileStoreError(RuntimeError):
    """Base error for the portable PDKS file store."""


class FileConflictError(FileStoreError):
    """Raised when an immutable source ID or user-edited note would be overwritten."""


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _safe_segment(value: str, fallback: str = "unknown", max_length: int = 72) -> str:
    value = str(value or "").strip()
    value = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", "-", value)
    value = re.sub(r"\s+", "-", value)
    value = value.strip(" .-_")
    return (value[:max_length] or fallback)


def _iso_date(value: str | None) -> tuple[str, str, str]:
    if not value:
        return ("unknown", "unknown", "unknown")
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return (f"{parsed.year:04d}", f"{parsed.month:02d}", parsed.strftime("%Y-%m-%d"))
    except (ValueError, TypeError):
        return ("unknown", "unknown", "unknown")


def _yaml_quote(value: Any) -> str:
    # JSON strings are valid YAML scalars and avoid a PyYAML runtime dependency.
    if value is None:
        return '""'
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def _frontmatter_value(text: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.*?)\s*$", text, flags=re.MULTILINE)
    if not match:
        return None
    raw = match.group(1)
    try:
        parsed = json.loads(raw)
        return str(parsed) if parsed is not None else None
    except Exception:
        return raw.strip("'\"")


class FileFirstVault:
    """Portable file-first knowledge vault.

    Source records are immutable JSONL entries. Knowledge notes are Markdown
    projections. Attachments are SHA-256 content addressed. The SQLite file
    created by rebuild_index() is a disposable search/index layer, not the
    operational CaptureRuntime database.
    """

    VERSION = "0.1.0"
    MANIFEST = "PDKS-MANIFEST.json"

    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        self.index_path = self.root / ".pdks" / "index" / "pdks-file-index.sqlite3"

    def _atomic_write(self, path: Path, data: bytes, mode: int = 0o600) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=".pdks-tmp-", dir=str(path.parent))
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(tmp_name, path)
            try:
                path.chmod(mode)
            except OSError:
                pass
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    def initialize(self) -> dict[str, Any]:
        if self.root.exists() and any(self.root.iterdir()):
            # A non-empty directory is acceptable only if it is already a PDKS Vault.
            if not (self.root / self.MANIFEST).exists():
                raise FileStoreError("Refusing to initialize a non-empty directory without PDKS-MANIFEST.json")
        directories = [
            "00-Inbox/Candidates", "10-Daily", "20-Events", "30-Projects", "40-People",
            "50-Meetings", "60-Decisions", "70-Tasks", "80-Knowledge", "85-Life",
            "90-Source-Records", "95-Archive", "assets/sha256",
            ".pdks/config", ".pdks/schemas", ".pdks/ontology", ".pdks/index",
            ".pdks/state", ".pdks/audit", ".pdks/cache", ".pdks/conflicts",
        ]
        for item in directories:
            (self.root / item).mkdir(parents=True, exist_ok=True)
        readme = self.root / "README.md"
        if not readme.exists():
            self._atomic_write(readme, (
                "# PDKS Vault\n\n"
                "This is a portable, file-first PDKS knowledge vault. It can be opened directly in Obsidian.\n\n"
                "- Markdown + YAML Frontmatter: human-readable knowledge assets.\n"
                "- JSON / JSONL: source records and evidence.\n"
                "- `assets/sha256/`: original attachments addressed by content hash.\n"
                "- `.pdks/index/`: rebuildable index; safe to recreate from files.\n\n"
                "PDKS does not require Obsidian. Do not sync this folder to a cloud provider unless you have explicitly reviewed and approved that provider and data scope.\n"
            ).encode("utf-8"), 0o600)
        manifest = self.root / self.MANIFEST
        manifest_was_created = not manifest.exists()
        if manifest_was_created:
            self._atomic_write(manifest, _json_bytes({
                "pdks_vault_version": self.VERSION,
                "storage_mode": "file-first",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "formats": {
                    "knowledge": "markdown+yaml-frontmatter",
                    "source_records": "jsonl",
                    "attachments": "sha256-content-addressed",
                    "index": "sqlite-rebuildable",
                },
                "ontology_version": "0.2.1",
                "manifest_policy": "human_assets_only; excludes .pdks runtime state and index",
            }), 0o600)
        try:
            self.root.chmod(0o700)
        except OSError:
            pass
        if manifest_was_created:
            self.refresh_manifest()
        return {"status": "initialized", "vault_path": str(self.root), "manifest": str(manifest)}

    def _source_jsonl_path(self, record: dict[str, Any], collection: str = "sources") -> Path:
        payload = record.get("payload") or {}
        captured = payload.get("captured_at") or record.get("created_at")
        year, month, day = _iso_date(captured)
        origin = _safe_segment(payload.get("origin_system") or "unknown")
        source_type = _safe_segment(payload.get("source_type") or record.get("object_type") or "record")
        return self.root / "90-Source-Records" / collection / origin / source_type / year / month / f"{day}.jsonl"

    def append_jsonl(self, relative_path: str | Path, record: dict[str, Any], id_key: str = "object_id") -> dict[str, Any]:
        path = self.root / relative_path
        resolved = path.resolve()
        if self.root != resolved and self.root not in resolved.parents:
            raise FileStoreError("Path escapes PDKS Vault")
        record_id = record.get(id_key) or record.get("source_id") or record.get("evidence_id")
        if not record_id:
            raise FileStoreError(f"JSONL record must contain stable {id_key}")
        existing_lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
        for line_no, line in enumerate(existing_lines, start=1):
            if not line.strip():
                continue
            try:
                old = json.loads(line)
            except json.JSONDecodeError as exc:
                raise FileStoreError(f"Invalid JSONL at {path}:{line_no}") from exc
            old_id = old.get(id_key) or old.get("source_id") or old.get("evidence_id")
            if old_id == record_id:
                if old == record:
                    return {"status": "duplicate", "path": str(path.relative_to(self.root)), "record_id": record_id}
                raise FileConflictError(f"Immutable source record ID already exists with different content: {record_id}")
        new_data = ("\n".join(existing_lines + [json.dumps(record, ensure_ascii=False, sort_keys=True)]) + "\n").encode("utf-8")
        self._atomic_write(path, new_data)
        return {"status": "written", "path": str(path.relative_to(self.root)), "record_id": record_id}

    def write_source_record(self, record: dict[str, Any]) -> dict[str, Any]:
        return self.append_jsonl(self._source_jsonl_path(record, "sources").relative_to(self.root), record)

    def write_evidence_record(self, record: dict[str, Any]) -> dict[str, Any]:
        created = record.get("created_at")
        year, month, day = _iso_date(created)
        path = Path("90-Source-Records") / "evidence" / year / month / f"{day}.jsonl"
        return self.append_jsonl(path, record)

    def write_attachment(self, data: bytes, filename: str, media_type: str | None = None) -> dict[str, Any]:
        if not isinstance(data, bytes):
            raise FileStoreError("Attachment data must be bytes")
        digest = hashlib.sha256(data).hexdigest()
        suffix = Path(_safe_segment(Path(filename).name, "attachment")).suffix.lower()[:12]
        directory = self.root / "assets" / "sha256" / digest[:2] / digest[2:4]
        directory.mkdir(parents=True, exist_ok=True)
        # Reuse an existing extension for identical bytes: content, not filename, defines identity.
        existing = next(iter(directory.glob(digest + ".*")), None)
        bare = directory / digest
        if existing is None and bare.exists():
            existing = bare
        target = existing or (directory / (digest + suffix if suffix else digest))
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise FileStoreError(f"Attachment hash collision or corrupted file: {target}")
            status = "duplicate"
        else:
            self._atomic_write(target, data)
            status = "written"
        metadata = {
            "sha256": digest, "path": target.relative_to(self.root).as_posix(),
            "original_filename": Path(filename).name, "media_type": media_type,
            "size_bytes": len(data),
        }
        index_path = Path("90-Source-Records") / "attachment-index.jsonl"
        index_file = self.root / index_path
        attachment_id = f"urn:pdks:attachment:{digest}"
        existing_entry = None
        if index_file.exists():
            for line in index_file.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                entry = json.loads(line)
                if entry.get("object_id") == attachment_id:
                    existing_entry = entry
                    break
        if existing_entry:
            if existing_entry.get("sha256") != digest or existing_entry.get("path") != metadata["path"]:
                raise FileConflictError(f"Attachment index conflicts with content-addressed asset: {digest}")
        else:
            self.append_jsonl(index_path, {"object_id": attachment_id, **metadata})
        return {"status": status, **metadata}

    def _object_folder(self, record: dict[str, Any]) -> str:
        kind = record.get("object_type", "knowledge_asset")
        payload = record.get("payload") or {}
        if kind == "event":
            return "20-Events"
        if kind == "entity":
            entity_type = payload.get("entity_type")
            if entity_type == "person":
                return "40-People"
            if entity_type in {"project", "organization"}:
                return "30-Projects"
            return "80-Knowledge/Entities"
        if kind == "action":
            return "70-Tasks"
        if kind == "assertion":
            return "60-Decisions"
        if kind == "personal_context":
            return "85-Life"
        return "80-Knowledge"

    def _record_title(self, record: dict[str, Any]) -> str:
        payload = record.get("payload") or {}
        return str(
            payload.get("title") or payload.get("canonical_name") or payload.get("name")
            or payload.get("description") or payload.get("event_type")
            or record.get("object_type") or "Knowledge"
        ).strip()[:180] or "Knowledge"

    def _render_payload(self, value: Any, level: int = 0) -> list[str]:
        lines: list[str] = []
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"evidence_refs", "source_refs"}:
                    continue
                heading = str(key).replace("_", " ").title()
                if isinstance(item, (dict, list)):
                    lines.append("### " + heading)
                    lines.extend(self._render_payload(item, level + 1))
                else:
                    lines.append(f"- **{heading}**: {item if item is not None else '—'}")
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, (dict, list)):
                    lines.extend(self._render_payload(item, level + 1))
                else:
                    lines.append(f"- {item}")
        else:
            lines.append(str(value))
        return lines

    def render_knowledge_note(self, record: dict[str, Any], review_state: str = "accepted") -> tuple[Path, bytes]:
        object_id = str(record.get("object_id") or "")
        if not object_id:
            raise FileStoreError("Knowledge record requires object_id")
        title = self._record_title(record)
        kind = str(record.get("object_type") or "knowledge_asset")
        payload = record.get("payload") or {}
        domains = record.get("domains") or []
        governance = record.get("governance") or {}
        provenance = record.get("provenance") or {}
        aliases = payload.get("aliases") if isinstance(payload.get("aliases"), list) else []
        source_refs = provenance.get("source_refs") or []
        evidence_refs = payload.get("evidence_refs") or []
        updated = record.get("updated_at") or record.get("created_at") or ""
        created = record.get("created_at") or updated
        status = (record.get("lifecycle") or {}).get("status", review_state)
        filename = f"{_safe_segment(title, 'knowledge', 90)}--{hashlib.sha256(object_id.encode()).hexdigest()[:8]}.md"
        folder = Path("00-Inbox/Candidates") if review_state == "candidate" else Path(self._object_folder(record))
        target = self.root / folder / filename
        front = [
            "---",
            f"pdks_id: {_yaml_quote(object_id)}",
            f"pdks_type: {_yaml_quote(kind)}",
            'schema_version: "0.1.0"',
            f"title: {_yaml_quote(title)}",
            f"created_at: {_yaml_quote(created)}",
            f"updated_at: {_yaml_quote(updated)}",
            f"status: {_yaml_quote(review_state if review_state == 'candidate' else status)}",
            "domains:",
        ]
        front.extend([f"  - {_yaml_quote(x)}" for x in domains] or ['  - "other"'])
        front.append(f"sensitivity: {_yaml_quote(governance.get('sensitivity', 'personal_private'))}")
        if source_refs:
            front.append("source_refs:")
            front.extend([f"  - {_yaml_quote(x)}" for x in source_refs])
        else:
            front.append("source_refs: []")
        if evidence_refs:
            front.append("evidence_refs:")
            front.extend([f"  - {_yaml_quote(x)}" for x in evidence_refs])
        else:
            front.append("evidence_refs: []")
        if aliases:
            front.append("aliases:")
            front.extend([f"  - {_yaml_quote(x)}" for x in aliases])
        else:
            front.append("aliases: []")
        front.append("---")
        body = [f"# {title}", "", f"> PDKS object: `{object_id}` · Type: `{kind}` · Review: **{review_state}**", ""]
        description = payload.get("description") or payload.get("summary")
        if description:
            body.extend(["## Summary", "", str(description), ""])
        details = self._render_payload(payload)
        if details:
            body.extend(["## Details", "", *details, ""])
        if source_refs:
            body.extend(["## Sources", ""])
            body.extend([f"- `{x}`" for x in source_refs])
            body.append("")
        if evidence_refs:
            body.extend(["## Evidence", ""])
            body.extend([f"- `{x}`" for x in evidence_refs])
            body.append("")
        content = ("\n".join(front + [""] + body).rstrip() + "\n").encode("utf-8")
        return folder / filename, content

    def _relative_source_links(self, refs: list[str], note_relative: Path, collection: str) -> list[str]:
        if not refs:
            return []
        lookup: dict[str, tuple[Path, dict[str, Any]]] = {}
        base = self.root / "90-Source-Records" / collection
        if base.exists():
            for jsonl in base.rglob("*.jsonl"):
                for line in jsonl.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    object_id = obj.get("object_id") or obj.get("source_id") or obj.get("evidence_id")
                    if object_id in refs:
                        lookup[object_id] = (jsonl, obj)
        lines = []
        for ref in refs:
            found = lookup.get(ref)
            if not found:
                lines.append(f"- `{ref}` (source file not present in this Vault)")
                continue
            jsonl, obj = found
            json_link = os.path.relpath(jsonl, self.root / note_relative.parent).replace(os.sep, "/")
            link_label = "Evidence record" if collection == "evidence" else "Source record"
            line = f"- [{link_label}]({json_link}) · `{ref}`"
            payload = obj.get("payload") or {}
            hash_value = payload.get("content_hash")
            digest = hash_value.get("value") if isinstance(hash_value, dict) else None
            if digest:
                assets = self.root / "assets" / "sha256"
                asset = next(iter(assets.rglob(digest + "*")), None) if assets.exists() else None
                if asset:
                    asset_link = os.path.relpath(asset, self.root / note_relative.parent).replace(os.sep, "/")
                    line += f" · [Original attachment]({asset_link})"
            lines.append(line)
        return lines

    def write_knowledge_note(self, record: dict[str, Any], review_state: str = "accepted") -> dict[str, Any]:
        relative, content = self.render_knowledge_note(record, review_state)
        # Add portable relative links after source/evidence JSONL and attachments have been projected.
        text = content.decode("utf-8")
        source_refs = (record.get("provenance") or {}).get("source_refs") or []
        evidence_refs = (record.get("payload") or {}).get("evidence_refs") or []
        extra = []
        source_lines = self._relative_source_links(source_refs, relative, "sources")
        evidence_lines = self._relative_source_links(evidence_refs, relative, "evidence")
        if source_lines:
            extra.extend(["## Source links", "", *source_lines, ""])
        if evidence_lines:
            extra.extend(["## Evidence links", "", *evidence_lines, ""])
        if extra:
            text = text.rstrip() + "\n\n" + "\n".join(extra).rstrip() + "\n"
            content = text.encode("utf-8")
        target = self.root / relative
        if target.exists():
            current = target.read_bytes()
            if current == content:
                return {"status": "duplicate", "path": relative.as_posix(), "pdks_id": record["object_id"]}
            # Preserve the incoming version outside the normal note tree; never silently overwrite user edits.
            digest = hashlib.sha256(content).hexdigest()[:12]
            conflict = self.root / ".pdks" / "conflicts" / f"{digest}.incoming.md"
            if not conflict.exists():
                self._atomic_write(conflict, content)
            return {"status": "conflict", "path": relative.as_posix(),
                    "incoming_copy": conflict.relative_to(self.root).as_posix(), "pdks_id": record["object_id"]}
        self._atomic_write(target, content)
        return {"status": "written", "path": relative.as_posix(), "pdks_id": record["object_id"]}

    def sync_from_runtime(self, runtime, owner_ref: str, include_candidates: bool = False,
                          include_raw_sources: bool = False) -> dict[str, Any]:
        """Project an existing CaptureRuntime database into portable files.

        This is a one-way migration/projection in this preview. It does not yet
        make the file vault the transactional source of truth.
        """
        self.initialize()
        with runtime._connection() as con:
            sources = con.execute("SELECT * FROM source_assets WHERE owner_ref=? AND status='active' ORDER BY captured_at",
                                  (owner_ref,)).fetchall()
            evidence = con.execute("SELECT * FROM evidence_segments WHERE owner_ref=? ORDER BY created_at",
                                   (owner_ref,)).fetchall()
            states = ("accepted", "candidate") if include_candidates else ("accepted",)
            placeholders = ",".join("?" for _ in states)
            records = con.execute(
                f"SELECT record_json,review_state FROM records WHERE owner_ref=? AND review_state IN ({placeholders}) AND record_json IS NOT NULL ORDER BY created_at",
                [owner_ref, *states],
            ).fetchall()
        counts = {"source_records": 0, "evidence_records": 0, "knowledge_notes": 0,
                  "attachments": 0, "duplicates": 0, "conflicts": 0, "missing_raw": 0}
        for row in sources:
            if row["source_record_json"]:
                obj = json.loads(row["source_record_json"])
                result = self.write_source_record(obj)
                counts["source_records"] += 1
                counts["duplicates"] += result["status"] == "duplicate"
            if include_raw_sources:
                raw_path = Path(row["raw_path"]) if row["raw_path"] else None
                if raw_path and raw_path.exists():
                    result = self.write_attachment(raw_path.read_bytes(), row["filename"] or "source.bin", row["media_type"])
                    counts["attachments"] += 1
                    counts["duplicates"] += result["status"] == "duplicate"
                else:
                    counts["missing_raw"] += 1
        for row in evidence:
            if row["evidence_record_json"]:
                result = self.write_evidence_record(json.loads(row["evidence_record_json"]))
                counts["evidence_records"] += 1
                counts["duplicates"] += result["status"] == "duplicate"
        for row in records:
            result = self.write_knowledge_note(json.loads(row["record_json"]), row["review_state"])
            counts["knowledge_notes"] += 1
            counts["duplicates"] += result["status"] == "duplicate"
            counts["conflicts"] += result["status"] == "conflict"
        self.refresh_manifest()
        return {"status": "projected", "owner_ref": owner_ref, "vault_path": str(self.root),
                "counts": counts,
                "important": "One-way projection from the current Runtime database. The file vault is not yet the transactional source of truth."}

    def refresh_manifest(self) -> dict[str, Any]:
        files: dict[str, dict[str, Any]] = {}
        for path in sorted(self.root.rglob("*")):
            if not path.is_file() or path.name == self.MANIFEST:
                continue
            rel = path.relative_to(self.root)
            if ".pdks" in rel.parts:
                continue
            data = path.read_bytes()
            files[rel.as_posix()] = {"size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        manifest = {
            "pdks_vault_version": self.VERSION,
            "storage_mode": "file-first",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "formats": {"knowledge": "markdown+yaml-frontmatter", "source_records": "jsonl",
                        "attachments": "sha256-content-addressed", "index": "sqlite-rebuildable"},
            "files": files,
            "file_count": len(files),
            "index_policy": "rebuildable; excluded from portable asset manifest",
        }
        self._atomic_write(self.root / self.MANIFEST, _json_bytes(manifest))
        return {"file_count": len(files), "manifest": str(self.root / self.MANIFEST)}

    def verify_manifest(self) -> dict[str, Any]:
        path = self.root / self.MANIFEST
        if not path.exists():
            raise FileStoreError("PDKS-MANIFEST.json is missing")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        errors = []
        for rel, expected in manifest.get("files", {}).items():
            target = (self.root / rel).resolve()
            if self.root != target and self.root not in target.parents:
                errors.append(f"path_escape:{rel}")
                continue
            if not target.exists():
                errors.append(f"missing:{rel}")
                continue
            data = target.read_bytes()
            if len(data) != expected.get("size_bytes") or hashlib.sha256(data).hexdigest() != expected.get("sha256"):
                errors.append(f"hash_mismatch:{rel}")
        return {"status": "ok" if not errors else "failed", "checked": len(manifest.get("files", {})),
                "errors": errors}

    def rebuild_index(self) -> dict[str, Any]:
        self.initialize()
        index_dir = self.index_path.parent
        index_dir.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix="pdks-index-", suffix=".sqlite3", dir=str(index_dir))
        os.close(fd)
        temp_path = Path(temp_name)
        counts = {"source_records": 0, "evidence_records": 0, "attachment_index_records": 0,
                  "knowledge_notes": 0, "attachments": 0}
        try:
            con = sqlite3.connect(temp_path)
            con.executescript("""
                PRAGMA journal_mode=DELETE;
                CREATE TABLE source_records(
                    object_id TEXT PRIMARY KEY, object_type TEXT, origin_system TEXT,
                    captured_at TEXT, content_hash TEXT, path TEXT NOT NULL, line_no INTEGER NOT NULL
                );
                CREATE TABLE evidence_records(
                    object_id TEXT PRIMARY KEY, object_type TEXT, captured_at TEXT,
                    path TEXT NOT NULL, line_no INTEGER NOT NULL
                );
                CREATE TABLE attachment_records(
                    object_id TEXT PRIMARY KEY, sha256 TEXT NOT NULL, path TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL
                );
                CREATE TABLE knowledge_notes(
                    pdks_id TEXT PRIMARY KEY, pdks_type TEXT, title TEXT, updated_at TEXT,
                    sensitivity TEXT, path TEXT NOT NULL
                );
                CREATE TABLE attachments(
                    sha256 TEXT PRIMARY KEY, path TEXT NOT NULL, size_bytes INTEGER NOT NULL
                );
                CREATE INDEX idx_source_time ON source_records(captured_at);
                CREATE INDEX idx_note_type ON knowledge_notes(pdks_type);
            """)
            for path in sorted((self.root / "90-Source-Records").rglob("*.jsonl")):
                rel = path.relative_to(self.root).as_posix()
                for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    object_id = obj.get("object_id") or obj.get("source_id") or obj.get("evidence_id")
                    if not object_id:
                        continue
                    payload = obj.get("payload") or {}
                    digest = ((payload.get("content_hash") or {}).get("value")
                              if isinstance(payload.get("content_hash"), dict) else None)
                    if "evidence" in path.relative_to(self.root / "90-Source-Records").parts:
                        con.execute("INSERT OR REPLACE INTO evidence_records VALUES(?,?,?,?,?)", (
                            object_id, obj.get("object_type"), obj.get("created_at"), rel, line_no))
                        counts["evidence_records"] += 1
                    elif path.name == "attachment-index.jsonl":
                        con.execute("INSERT OR REPLACE INTO attachment_records VALUES(?,?,?,?)", (
                            object_id, obj.get("sha256"), obj.get("path"), int(obj.get("size_bytes", 0))))
                        counts["attachment_index_records"] += 1
                    else:
                        con.execute("INSERT OR REPLACE INTO source_records VALUES(?,?,?,?,?,?,?)", (
                            object_id, obj.get("object_type"), payload.get("origin_system"),
                            payload.get("captured_at") or obj.get("created_at"), digest, rel, line_no))
                        counts["source_records"] += 1
            for path in sorted(self.root.rglob("*.md")):
                if ".pdks" in path.parts or path.name == "README.md":
                    continue
                content = path.read_text(encoding="utf-8")
                if not content.startswith("---\n"):
                    continue
                end = content.find("\n---", 4)
                if end < 0:
                    continue
                front = content[4:end]
                pdks_id = _frontmatter_value(front, "pdks_id")
                if not pdks_id:
                    continue
                con.execute("INSERT OR REPLACE INTO knowledge_notes VALUES(?,?,?,?,?,?)", (
                    pdks_id, _frontmatter_value(front, "pdks_type"), _frontmatter_value(front, "title"),
                    _frontmatter_value(front, "updated_at"), _frontmatter_value(front, "sensitivity"),
                    path.relative_to(self.root).as_posix()))
                counts["knowledge_notes"] += 1
            assets = self.root / "assets" / "sha256"
            if assets.exists():
                for path in assets.rglob("*"):
                    if not path.is_file():
                        continue
                    digest = path.name.split(".", 1)[0]
                    actual = hashlib.sha256(path.read_bytes()).hexdigest()
                    if digest != actual:
                        raise FileStoreError(f"Attachment checksum mismatch: {path}")
                    con.execute("INSERT OR REPLACE INTO attachments VALUES(?,?,?)",
                                (digest, path.relative_to(self.root).as_posix(), path.stat().st_size))
                    counts["attachments"] += 1
            con.commit()
            check = con.execute("PRAGMA integrity_check").fetchone()[0]
            if check != "ok":
                raise FileStoreError(f"Rebuilt index integrity check failed: {check}")
            con.close()
            os.replace(temp_path, self.index_path)
        except Exception:
            try:
                con.close()
            except Exception:
                pass
            try:
                temp_path.unlink()
            except OSError:
                pass
            raise
        return {"status": "rebuilt", "index_path": str(self.index_path), "counts": counts,
                "integrity_check": "ok",
                "important": "This is a rebuildable file index, not a replacement for the operational CaptureRuntime database."}
