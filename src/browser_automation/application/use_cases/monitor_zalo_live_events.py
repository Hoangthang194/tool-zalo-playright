from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime

from browser_automation.application.ports.zalo_live_event_listener import ZaloLiveEventListener
from browser_automation.domain.exceptions import LauncherValidationError
from browser_automation.domain.zalo_launcher import DEFAULT_ZALO_URL
from browser_automation.domain.zalo_live_events import ZaloLiveEventLogEntry

DEFAULT_ZALO_LIVE_EVENT_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True, slots=True)
class StartZaloLiveEventMonitorRequest:
    remote_debugging_port: int
    account_label: str
    target_url: str = DEFAULT_ZALO_URL


@dataclass(frozen=True, slots=True)
class StartZaloLiveEventMonitorResult:
    remote_debugging_port: int
    account_label: str
    target_url: str


@dataclass(frozen=True, slots=True)
class StopZaloLiveEventMonitorResult:
    was_running: bool


class ZaloLiveEventMonitorUseCase:
    def __init__(
        self,
        listener: ZaloLiveEventListener,
        *,
        timeout_seconds: float = DEFAULT_ZALO_LIVE_EVENT_TIMEOUT_SECONDS,
    ) -> None:
        self._listener = listener
        self._timeout_seconds = timeout_seconds

    def start(
        self,
        request: StartZaloLiveEventMonitorRequest,
        on_event: Callable[[ZaloLiveEventLogEntry], None],
    ) -> StartZaloLiveEventMonitorResult:
        if request.remote_debugging_port <= 0:
            raise LauncherValidationError(
                "Launch a visible Zalo account first so the tool can attach to the active Chrome tab."
            )

        def handle_event(event: ZaloLiveEventLogEntry) -> None:
            if request.account_label and not event.account_label:
                on_event(replace(event, account_label=request.account_label))
                return
            on_event(event)

        self._listener.start(
            remote_debugging_port=request.remote_debugging_port,
            target_url=request.target_url,
            on_event=handle_event,
            timeout_seconds=self._timeout_seconds,
        )

        return StartZaloLiveEventMonitorResult(
            remote_debugging_port=request.remote_debugging_port,
            account_label=request.account_label,
            target_url=request.target_url,
        )

    def stop(self) -> StopZaloLiveEventMonitorResult:
        was_running = self._listener.is_running()
        self._listener.stop()
        return StopZaloLiveEventMonitorResult(was_running=was_running)

    def is_running(self) -> bool:
        return self._listener.is_running()


def format_zalo_live_event_log_entry(entry: ZaloLiveEventLogEntry) -> str:
    timestamp = _format_timestamp(entry.occurred_at)
    account_part = f" [{entry.account_label}]" if entry.account_label else ""
    detail_part = f" | {entry.detail}" if entry.detail else ""
    return (
        f"[{timestamp}]{account_part} "
        f"[{entry.event_type}/{entry.scope}] {entry.summary}{detail_part}"
    )


def format_zalo_live_event_status_message(entry: ZaloLiveEventLogEntry) -> str:
    if not entry.detail:
        return entry.summary

    if entry.event_type.startswith("listener"):
        return f"{entry.summary} {entry.detail}"

    if entry.event_type == "new_message":
        return f"{entry.summary} {entry.detail}"

    return entry.summary


def _format_timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value

    local_dt = parsed.astimezone(UTC).astimezone()
    return local_dt.strftime("%Y-%m-%d %H:%M:%S")
