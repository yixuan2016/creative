from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any, Callable


def sanitize_diagnostic(value: str) -> str:
    value = re.sub(r"(?i)(access[_-]?token|refresh[_-]?token|authorization|app[_-]?secret|client[_-]?secret|secret)\s*[:=]\s*[^\s,;]+", r"\1=[REDACTED]", value)
    value = re.sub(r"(?i)bearer\s+[^\s,;]+", "Bearer [REDACTED]", value)
    return value[:500]


class DWSCLIError(RuntimeError):
    def __init__(self, message: str, *, returncode: int | None = None, stderr: str = ""):
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


@dataclass(frozen=True)
class DWSResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class DWSCLI:
    """Narrow, read-only wrapper around the official DingTalk Workspace CLI.

    It never invokes a shell, never accepts arbitrary command text from an Agent,
    and never exposes token-bearing auth output to callers.
    """

    def __init__(
        self,
        binary: str = "dws",
        profile: str | None = None,
        timeout: int = 30,
        env: dict[str, str] | None = None,
        runner: Callable[..., Any] | None = None,
    ):
        self.binary = binary
        self.profile = profile
        self.timeout = timeout
        self.env = env
        self.runner = runner or subprocess.run

    def _prefix(self) -> list[str]:
        executable_name = os.path.basename(self.binary).lower()
        if executable_name not in {"dws", "dws.exe"}:
            raise ValueError("DWS executable must be named dws or dws.exe")
        resolved = shutil.which(self.binary) if os.path.sep not in self.binary else self.binary
        if not resolved:
            raise DWSCLIError(
                "DWS CLI was not found. Install the official DingTalk Workspace CLI and ensure `dws` is on PATH."
            )
        argv = [resolved]
        if self.profile:
            if not re.fullmatch(r"[A-Za-z0-9:_-]{1,180}", self.profile):
                raise ValueError("DWS profile selector contains unsupported characters")
            argv.extend(["--profile", self.profile])
        return argv

    def run(self, args: list[str], *, timeout: int | None = None) -> DWSResult:
        if not args or any(not isinstance(x, str) or "\x00" in x for x in args):
            raise ValueError("DWS arguments must be a non-empty list of strings")
        argv = self._prefix() + args
        try:
            completed = self.runner(
                argv,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout or self.timeout,
                env=self.env,
                shell=False,
                check=False,
            )
        except FileNotFoundError as exc:
            raise DWSCLIError("DWS executable was not found") from exc
        except subprocess.TimeoutExpired as exc:
            raise DWSCLIError("DWS command timed out") from exc
        result = DWSResult(tuple(argv), int(completed.returncode), completed.stdout or "", completed.stderr or "")
        if result.returncode != 0:
            # Do not surface arbitrary stderr in exception text: provider diagnostics
            # can contain personal data or implementation details.
            safe_stderr = "\n".join(sanitize_diagnostic(x) for x in result.stderr.splitlines()[-8:])
            raise DWSCLIError(
                f"DWS command failed with exit code {result.returncode}",
                returncode=result.returncode,
                stderr=safe_stderr,
            )
        return result

    @staticmethod
    def _json_output(result: DWSResult) -> Any:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise DWSCLIError("DWS did not return valid JSON for a JSON-mode command", returncode=result.returncode) from exc

    def version(self) -> dict[str, str]:
        result = self.run(["version"])
        text = (result.stdout or result.stderr).strip()
        return {"version_output": text[:160]}

    def auth_status(self) -> dict[str, Any]:
        result = self.run(["auth", "status", "--readonly", "--format", "json"])
        payload = self._json_output(result)
        # Explicit allowlist: never return arbitrary credential/token fields.
        allowed = {
            "authenticated", "token_valid", "currentProfile", "previousProfile",
            "profile", "corpId", "userId", "orgName", "userName", "reason",
            "local_state_requires_repair", "local_state_unreadable",
        }
        def pick(obj):
            if not isinstance(obj, dict):
                return {}
            result = {k: v for k, v in obj.items()
                      if k in allowed and isinstance(v, (str, int, float, bool, type(None)))}
            for nested_key in ("data", "result"):
                nested = obj.get(nested_key)
                if isinstance(nested, dict):
                    result.update({k: v for k, v in nested.items()
                                   if k in allowed and isinstance(v, (str, int, float, bool, type(None)))})
            return result
        return pick(payload)

    def event_catalog(self, category: str | None = None) -> Any:
        args = ["event", "list"]
        if category:
            if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_-]{0,40}", category):
                raise ValueError("Invalid DWS event category")
            args.extend(["--category", category])
        args.extend(["--format", "json"])
        return self._json_output(self.run(args))

    def event_schema(self, event_key: str) -> Any:
        from .catalog import DWS_EVENT_CATALOG
        if event_key not in DWS_EVENT_CATALOG:
            raise ValueError(f"Unsupported DWS event key: {event_key}")
        return self._json_output(self.run(["event", "schema", event_key, "--flatten", "--format", "json"]))

    def command_schema(self, command_path: str) -> Any:
        # Read-only schema discovery for future historical/backfill adapters.
        allowed = {
            "chat message list-all", "chat message list", "minutes list all",
            "minutes get summary", "minutes get transcription", "calendar event list",
            "todo task list", "oa approval list-initiated", "oa approval list-pending",
            "oa approval detail", "drive list", "doc search", "doc get",
        }
        if command_path not in allowed:
            raise ValueError("Only approved read-only DWS command schemas can be inspected")
        return self._json_output(self.run(["schema", command_path, "--compact", "--format", "json"]))

    def minutes_summary(self, task_uuid: str) -> Any:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,180}", task_uuid):
            raise ValueError("Invalid DWS minutes task UUID")
        return self._json_output(self.run(["minutes", "get", "summary", "--id", task_uuid, "--format", "json"]))
