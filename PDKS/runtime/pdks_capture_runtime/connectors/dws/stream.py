from __future__ import annotations

import json
import os
import queue
import re
import signal
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Iterator, Any

from .catalog import validate_consume_spec
from .cli import DWSCLI, DWSCLIError, sanitize_diagnostic

MAX_NDJSON_LINE_BYTES = 1_048_576
_READY_SINGLE = re.compile(r"\[event\] ready event_key=([^ ]+).*?subscribe_id=([^ ]+)")
_READY_MULTI = re.compile(r"\[event\] ready event_count=(\d+)")
_SUBSCRIPTION = re.compile(r"\[event\] subscription .*?event_key=([^ ]+).*?subscribe_id=([^ ]+)")


def resolve_event_key(event: dict[str, Any], configured_keys: list[str]) -> str:
    """Resolve the event key from reviewed metadata, or require a single-key stream."""
    candidates = ("event_key", "eventKey", "event_type", "eventType", "type")
    for field in candidates:
        value = event.get(field)
        if isinstance(value, str) and value in configured_keys:
            return value
    if len(configured_keys) == 1:
        return configured_keys[0]
    raise DWSCLIError(
        "DWS multi-event output did not identify a configured event key; "
        "run one event key per consumer until the installed CLI schema is verified"
    )


@dataclass
class DWSConsumer:
    cli: DWSCLI
    event_keys: list[str]
    user: str | None = None
    open_dingtalk_id: str | None = None
    group: str | None = None
    role_types: list[str] | None = None
    calendar_ids: list[str] | None = None
    change_types: list[str] | None = None
    duration: str | None = None
    max_events: int | None = None
    popen_factory: Any = subprocess.Popen
    process: Any = field(default=None, init=False)
    _queue: queue.Queue = field(default_factory=queue.Queue, init=False)
    _threads: list[threading.Thread] = field(default_factory=list, init=False)
    _stdout_backlog: list[str] = field(default_factory=list, init=False)
    _stderr_tail: list[str] = field(default_factory=list, init=False)
    subscribe_ids: dict[str, str] = field(default_factory=dict, init=False)
    ready: bool = field(default=False, init=False)
    _stdout_eof_seen: bool = field(default=False, init=False)

    def command(self) -> list[str]:
        validate_consume_spec(
            self.event_keys, user=self.user, open_dingtalk_id=self.open_dingtalk_id,
            group=self.group, role_types=self.role_types,
            calendar_ids=self.calendar_ids, change_types=self.change_types,
        )
        if self.duration and not re.fullmatch(r"[1-9][0-9]*(s|m|h)", self.duration):
            raise ValueError("duration must look like 30s, 10m or 1h")
        if self.max_events is not None and self.max_events < 1:
            raise ValueError("max_events must be at least 1")
        argv = self.cli._prefix() + ["event", "consume", *self.event_keys]
        if self.user:
            argv.extend(["--user", self.user])
        if self.open_dingtalk_id:
            argv.extend(["--open-dingtalk-id", self.open_dingtalk_id])
        if self.group:
            argv.extend(["--group", self.group])
        if self.role_types:
            argv.extend(["--role-types", ",".join(self.role_types)])
        if self.calendar_ids:
            argv.extend(["--calendar-ids", ",".join(self.calendar_ids)])
        if self.change_types:
            argv.extend(["--change-types", ",".join(self.change_types)])
        argv.extend(["--flatten", "-f", "ndjson"])
        if self.event_keys == ["user_calendar_event_changed"]:
            if not self.calendar_ids:
                argv.extend(["--calendar-ids", "primary"])
            if not self.change_types:
                argv.extend(["--change-types", "eventCreated,eventUpdated,eventCancelled"])
        if self.duration:
            argv.extend(["--duration", self.duration])
        if self.max_events is not None:
            argv.extend(["--max-events", str(self.max_events)])
        return argv

    def start(self) -> "DWSConsumer":
        if self.process is not None:
            raise RuntimeError("DWS consumer has already been started")
        argv = self.command()
        try:
            self.process = self.popen_factory(
                argv,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                shell=False,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0,
            )
        except FileNotFoundError as exc:
            raise DWSCLIError("DWS executable was not found") from exc
        self._threads = [
            threading.Thread(target=self._pump, args=("stdout", self.process.stdout), daemon=True),
            threading.Thread(target=self._pump, args=("stderr", self.process.stderr), daemon=True),
        ]
        for thread in self._threads:
            thread.start()
        return self

    def _pump(self, channel: str, pipe) -> None:
        try:
            while True:
                line = pipe.readline(MAX_NDJSON_LINE_BYTES + 1)
                if line == "":
                    break
                if len(line.encode("utf-8")) > MAX_NDJSON_LINE_BYTES:
                    self._queue.put((channel + "_too_long", None))
                    break
                self._queue.put((channel, line))
        finally:
            self._queue.put((channel + "_eof", None))

    def wait_ready(self, timeout: float = 30.0) -> dict[str, Any]:
        if self.process is None:
            raise RuntimeError("Start the DWS consumer first")
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                raise DWSCLIError(
                    f"DWS consumer exited before ready (exit={self.process.returncode})",
                    returncode=self.process.returncode,
                    stderr="\n".join(self._stderr_tail[-8:]),
                )
            try:
                channel, line = self._queue.get(timeout=min(0.2, max(0.01, deadline-time.monotonic())))
            except queue.Empty:
                continue
            if channel == "stdout_too_long":
                raise DWSCLIError("DWS NDJSON event exceeded the 1 MiB safety limit")
            if channel == "stdout_eof":
                self._stdout_eof_seen = True
                continue
            if channel == "stdout":
                self._stdout_backlog.append(line)
                continue
            if channel != "stderr":
                continue
            clean = line.rstrip("\r\n")
            if clean:
                self._stderr_tail.append(sanitize_diagnostic(clean))
                self._stderr_tail = self._stderr_tail[-100:]
            single = _READY_SINGLE.search(clean)
            if single:
                self.subscribe_ids[single.group(1)] = single.group(2)
                self.ready = True
                return {"ready": True, "subscribe_ids": dict(self.subscribe_ids)}
            multi = _READY_MULTI.search(clean)
            if multi:
                self.ready = True
                return {"ready": True, "event_count": int(multi.group(1)), "subscribe_ids": dict(self.subscribe_ids)}
            subscription = _SUBSCRIPTION.search(clean)
            if subscription:
                self.subscribe_ids[subscription.group(1)] = subscription.group(2)
        raise DWSCLIError("Timed out waiting for the official DWS event-ready marker", stderr="\n".join(self._stderr_tail[-8:]))

    def iter_events(self) -> Iterator[dict[str, Any]]:
        if self.process is None or not self.ready:
            raise RuntimeError("DWS consumer must be started and ready before reading events")
        pending = list(self._stdout_backlog)
        self._stdout_backlog.clear()
        while True:
            if pending:
                line = pending.pop(0)
                yield self._parse_line(line)
                continue
            if self._stdout_eof_seen:
                return
            try:
                channel, line = self._queue.get(timeout=0.5)
            except queue.Empty:
                if self.process.poll() is not None:
                    return
                continue
            if channel == "stdout":
                if len(line.encode("utf-8")) > MAX_NDJSON_LINE_BYTES:
                    raise DWSCLIError("DWS NDJSON event exceeded the 1 MiB safety limit")
                yield self._parse_line(line)
            elif channel == "stdout_eof":
                return
            elif channel == "stdout_too_long":
                raise DWSCLIError("DWS NDJSON event exceeded the 1 MiB safety limit")
            elif channel == "stderr":
                clean = line.rstrip("\r\n")
                if clean:
                    self._stderr_tail.append(sanitize_diagnostic(clean))
                    self._stderr_tail = self._stderr_tail[-100:]

    @staticmethod
    def _parse_line(line: str) -> dict[str, Any]:
        if len(line.encode("utf-8")) > MAX_NDJSON_LINE_BYTES:
            raise DWSCLIError("DWS NDJSON event exceeded the 1 MiB safety limit")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DWSCLIError("DWS stdout contained a non-JSON line; expected NDJSON only") from exc
        if not isinstance(value, dict):
            raise DWSCLIError("DWS NDJSON event must be a JSON object")
        return value

    def stop(self, timeout: float = 10.0) -> dict[str, Any]:
        if self.process is None:
            return {"stopped": True, "already_stopped": True}
        try:
            if self.process.stdin and not self.process.stdin.closed:
                self.process.stdin.close()
        except Exception:
            pass
        try:
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Prefer a graceful control signal so DWS can execute its documented cleanup.
            if os.name == "nt" and hasattr(signal, "CTRL_BREAK_EVENT"):
                self.process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                self.process.terminate()  # SIGTERM on POSIX
            try:
                self.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                raise DWSCLIError("DWS did not stop after graceful stdin close and SIGTERM; do not force-kill it")
        for thread in self._threads:
            thread.join(timeout=1.0)
        return {
            "stopped": self.process.poll() is not None,
            "returncode": self.process.returncode,
            "subscribe_ids": dict(self.subscribe_ids),
        }
