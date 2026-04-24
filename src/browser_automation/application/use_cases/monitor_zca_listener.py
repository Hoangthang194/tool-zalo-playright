from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from browser_automation.application.ports.message_store import MessageStore
from browser_automation.application.ports.zca_listener_process import ZcaListenerProcess
from browser_automation.domain.exceptions import LauncherValidationError, SettingsPersistenceError
from browser_automation.domain.messages import SavedZaloMessage
from browser_automation.domain.zalo_live_events import ZaloLiveEventLogEntry


@dataclass(frozen=True, slots=True)
class StartZcaListenerRequest:
    account_id: str
    account_label: str
    credentials_file_path: str


@dataclass(frozen=True, slots=True)
class StartZcaListenerResult:
    account_id: str
    account_label: str
    credentials_file_path: str


@dataclass(frozen=True, slots=True)
class StopZcaListenerResult:
    was_running: bool


class ZcaListenerMonitorUseCase:
    def __init__(
        self,
        listener_process: ZcaListenerProcess,
        message_store: MessageStore,
    ) -> None:
        self._listener_process = listener_process
        self._message_store = message_store

    def start(
        self,
        request: StartZcaListenerRequest,
        on_event: Callable[[ZaloLiveEventLogEntry], None],
    ) -> StartZcaListenerResult:
        credentials_file_path = request.credentials_file_path.strip()
        if not credentials_file_path:
            raise LauncherValidationError("A credentials file is required to start the listener.")

        def handle_event(event: ZaloLiveEventLogEntry) -> None:
            event_with_label = (
                event
                if event.account_label
                else replace(event, account_label=request.account_label)
            )
            if event_with_label.event_type != "new_message":
                on_event(event_with_label)
                return

            msg_id = event_with_label.msg_id.strip()
            content = (event_with_label.content or event_with_label.detail).strip()
            if not msg_id:
                on_event(
                    replace(
                        event_with_label,
                        event_type="listener_error",
                        summary="Incoming message is missing msgId.",
                        detail=event_with_label.detail,
                    )
                )
                return
            if not content:
                on_event(
                    replace(
                        event_with_label,
                        event_type="listener_error",
                        summary="Incoming message is missing content.",
                        detail=event_with_label.detail,
                    )
                )
                return

            try:
                persistence_status = self._message_store.save_message(
                    SavedZaloMessage(
                        msg_id=msg_id,
                        from_group_id=event_with_label.from_group_id,
                        to_group_id=event_with_label.to_group_id,
                        from_account_id=request.account_id,
                        content=content,
                    )
                )
            except SettingsPersistenceError as exc:
                on_event(
                    replace(
                        event_with_label,
                        event_type="listener_error",
                        summary="Database persistence failed for incoming message.",
                        detail=str(exc),
                    )
                )
                return

            status_summary = (
                "Incoming message already processed."
                if persistence_status == "already_processed"
                else "Incoming message inserted into database."
            )
            on_event(replace(event_with_label, summary=status_summary))

        self._listener_process.start(
            credentials_file_path=credentials_file_path,
            on_event=handle_event,
        )
        return StartZcaListenerResult(
            account_id=request.account_id,
            account_label=request.account_label,
            credentials_file_path=credentials_file_path,
        )

    def stop(self) -> StopZcaListenerResult:
        was_running = self._listener_process.is_running()
        self._listener_process.stop()
        return StopZcaListenerResult(was_running=was_running)

    def is_running(self) -> bool:
        return self._listener_process.is_running()
