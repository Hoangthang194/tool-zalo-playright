from __future__ import annotations

import json
import subprocess
import threading
from collections.abc import Callable
from pathlib import Path

from browser_automation.domain.exceptions import BrowserAutomationError
from browser_automation.domain.zalo_live_events import ZaloLiveEventLogEntry


class SubprocessZcaListenerProcess:
    def __init__(
        self,
        *,
        node_executable: str = "node",
        script_path: Path | None = None,
    ) -> None:
        self._node_executable = node_executable
        self._script_path = script_path or Path(__file__).with_name("zca_listener_adapter.mjs")
        self._process: subprocess.Popen[str] | None = None
        self._reader_thread: threading.Thread | None = None
        self._running = False

    def build_command(self, *, credentials_file_path: str) -> list[str]:
        return [
            self._node_executable,
            str(self._script_path),
            "--credentials-file",
            credentials_file_path,
        ]

    def parse_event_line(self, line: str) -> ZaloLiveEventLogEntry | None:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None

        return ZaloLiveEventLogEntry(
            event_type=str(payload.get("eventType") or "listener"),
            scope=str(payload.get("scope") or "listener"),
            summary=str(payload.get("summary") or ""),
            detail=str(payload.get("detail") or ""),
            occurred_at=str(payload.get("occurredAt") or ""),
            msg_id=str(payload.get("msgId") or ""),
            from_group_id=_optional_str(payload.get("fromGroupId")),
            to_group_id=_optional_str(payload.get("toGroupId")),
            content=str(payload.get("content") or ""),
            raw_type=str(payload.get("rawType") or ""),
        )

    def start(
        self,
        *,
        credentials_file_path: str,
        on_event: Callable[[ZaloLiveEventLogEntry], None],
    ) -> None:
        if self._running:
            raise BrowserAutomationError("The ZCA listener is already running.")

        try:
            process = subprocess.Popen(
                self.build_command(credentials_file_path=credentials_file_path),
                cwd=str(self._script_path.parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as exc:
            raise BrowserAutomationError(f"Could not start ZCA listener process: {exc}") from exc

        self._process = process
        self._running = True
        self._reader_thread = threading.Thread(
            target=self._read_stdout,
            args=(process, on_event),
            daemon=True,
        )
        self._reader_thread.start()

    def stop(self) -> None:
        process = self._process
        self._running = False
        if process is None:
            return
        if process.poll() is None:
            process.terminate()
        self._process = None

    def is_running(self) -> bool:
        return self._running

    def _read_stdout(
        self,
        process: subprocess.Popen[str],
        on_event: Callable[[ZaloLiveEventLogEntry], None],
    ) -> None:
        try:
            if process.stdout is None:
                return
            for line in process.stdout:
                parsed_event = self.parse_event_line(line.strip())
                if parsed_event is not None:
                    on_event(parsed_event)
        finally:
            self._running = False


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
