from browser_automation.application.use_cases.monitor_zalo_live_events import (
    StartZaloLiveEventMonitorRequest,
    ZaloLiveEventMonitorUseCase,
    format_zalo_live_event_log_entry,
    format_zalo_live_event_status_message,
)
from browser_automation.domain.exceptions import LauncherValidationError
from browser_automation.domain.zalo_live_events import ZaloLiveEventLogEntry


class FakeZaloLiveEventListener:
    def __init__(self) -> None:
        self.started_with = None
        self.stopped = False
        self.running = False

    def start(self, *, remote_debugging_port: int, target_url: str, on_event, timeout_seconds: float) -> None:
        self.started_with = {
            "remote_debugging_port": remote_debugging_port,
            "target_url": target_url,
            "timeout_seconds": timeout_seconds,
        }
        self.running = True
        on_event(
            ZaloLiveEventLogEntry(
                event_type="new_message",
                scope="group",
                summary="New group message detected.",
                detail="cmd=521",
                occurred_at="2026-04-24T10:00:00Z",
            )
        )

    def stop(self) -> None:
        self.stopped = True
        self.running = False

    def is_running(self) -> bool:
        return self.running


def test_zalo_live_event_monitor_starts_listener_and_applies_account_label() -> None:
    listener = FakeZaloLiveEventListener()
    use_case = ZaloLiveEventMonitorUseCase(listener, timeout_seconds=9.0)
    received_events: list[ZaloLiveEventLogEntry] = []

    result = use_case.start(
        StartZaloLiveEventMonitorRequest(
            remote_debugging_port=9222,
            target_url="https://chat.zalo.me",
            account_label="zalo1",
        ),
        received_events.append,
    )

    assert result.account_label == "zalo1"
    assert listener.started_with == {
        "remote_debugging_port": 9222,
        "target_url": "https://chat.zalo.me",
        "timeout_seconds": 9.0,
    }
    assert received_events[0].account_label == "zalo1"
    assert received_events[0].event_type == "new_message"


def test_zalo_live_event_monitor_rejects_missing_remote_debugging_port() -> None:
    use_case = ZaloLiveEventMonitorUseCase(FakeZaloLiveEventListener())

    try:
        use_case.start(
            StartZaloLiveEventMonitorRequest(
                remote_debugging_port=0,
                target_url="https://chat.zalo.me",
                account_label="zalo1",
            ),
            lambda event: None,
        )
    except LauncherValidationError as exc:
        assert "Launch a visible Zalo account first" in str(exc)
    else:
        raise AssertionError("Expected remote debugging port validation error")


def test_zalo_live_event_monitor_uses_longer_default_timeout_for_real_browser_attach() -> None:
    listener = FakeZaloLiveEventListener()
    use_case = ZaloLiveEventMonitorUseCase(listener)

    use_case.start(
        StartZaloLiveEventMonitorRequest(
            remote_debugging_port=9222,
            target_url="https://chat.zalo.me",
            account_label="zalo1",
        ),
        lambda event: None,
    )

    assert listener.started_with["timeout_seconds"] == 30.0


def test_zalo_live_event_monitor_stops_listener() -> None:
    listener = FakeZaloLiveEventListener()
    use_case = ZaloLiveEventMonitorUseCase(listener)

    use_case.start(
        StartZaloLiveEventMonitorRequest(
            remote_debugging_port=9222,
            target_url="https://chat.zalo.me",
            account_label="zalo1",
        ),
        lambda event: None,
    )
    result = use_case.stop()

    assert result.was_running is True
    assert listener.stopped is True
    assert listener.is_running() is False


def test_format_zalo_live_event_log_entry_renders_readable_line() -> None:
    line = format_zalo_live_event_log_entry(
        ZaloLiveEventLogEntry(
            event_type="delivered",
            scope="network",
            summary="Delivered receipt detected.",
            detail="https://tt-group-wpa.chat.zalo.me/api/group/deliveredv2",
            occurred_at="2026-04-24T10:00:00Z",
            account_label="zalo1",
        )
    )

    assert "[2026-04-24 17:00:00]" in line
    assert "[zalo1]" in line
    assert "[delivered/network]" in line
    assert "Delivered receipt detected." in line


def test_format_zalo_live_event_status_message_includes_detail_for_listener_errors() -> None:
    message = format_zalo_live_event_status_message(
        ZaloLiveEventLogEntry(
            event_type="listener",
            scope="system",
            summary="Live listener stopped unexpectedly.",
            detail="Could not attach to the launched Chrome window for live event monitoring.",
            occurred_at="2026-04-24T10:00:00Z",
            account_label="zalo1",
        )
    )

    assert message == (
        "Live listener stopped unexpectedly. "
        "Could not attach to the launched Chrome window for live event monitoring."
    )


def test_format_zalo_live_event_status_message_includes_preview_for_new_messages() -> None:
    message = format_zalo_live_event_status_message(
        ZaloLiveEventLogEntry(
            event_type="new_message",
            scope="dom",
            summary="New incoming message detected for 'Test zalo'.",
            detail="Hoàng Thắng: test 5",
            occurred_at="2026-04-24T10:00:00Z",
            account_label="zalo1",
        )
    )

    assert message == "New incoming message detected for 'Test zalo'. Hoàng Thắng: test 5"
