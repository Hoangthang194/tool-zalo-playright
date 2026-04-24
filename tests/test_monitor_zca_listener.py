from browser_automation.application.use_cases.monitor_zca_listener import (
    StartZcaListenerRequest,
    ZcaListenerMonitorUseCase,
)
from browser_automation.domain.exceptions import LauncherValidationError, SettingsPersistenceError
from browser_automation.domain.messages import SavedZaloMessage
from browser_automation.domain.zalo_live_events import ZaloLiveEventLogEntry


class FakeZcaListenerProcess:
    def __init__(self, events=None) -> None:
        self.events = list(events or [])
        self.started_with = None
        self.running = False
        self.stopped = False

    def start(self, *, credentials_file_path: str, on_event) -> None:
        self.started_with = {"credentials_file_path": credentials_file_path}
        self.running = True
        for event in self.events:
            on_event(event)

    def stop(self) -> None:
        self.running = False
        self.stopped = True

    def is_running(self) -> bool:
        return self.running


class FakeMessageStore:
    def __init__(self, save_result: str = "inserted", should_fail: bool = False) -> None:
        self.save_result = save_result
        self.should_fail = should_fail
        self.saved_messages: list[SavedZaloMessage] = []

    def save_message(self, message: SavedZaloMessage) -> str:
        if self.should_fail:
            raise SettingsPersistenceError("boom")
        self.saved_messages.append(message)
        return self.save_result


def test_zca_listener_monitor_persists_new_message_events() -> None:
    listener = FakeZcaListenerProcess(
        events=[
            ZaloLiveEventLogEntry(
                event_type="new_message",
                scope="listener",
                summary="Incoming message received.",
                detail="hello",
                occurred_at="2026-04-24T10:00:00Z",
                msg_id="msg-1",
                from_group_id="group-a",
                to_group_id="group-b",
                content="hello",
                raw_type="text",
            )
        ]
    )
    message_store = FakeMessageStore()
    use_case = ZcaListenerMonitorUseCase(listener, message_store)
    observed: list[ZaloLiveEventLogEntry] = []

    result = use_case.start(
        StartZcaListenerRequest(
            account_id="listener-1",
            account_label="Listener One",
            credentials_file_path=r"C:\zca\listener-1.json",
        ),
        observed.append,
    )

    assert result.account_id == "listener-1"
    assert listener.started_with == {"credentials_file_path": r"C:\zca\listener-1.json"}
    assert message_store.saved_messages[0] == SavedZaloMessage(
        msg_id="msg-1",
        from_group_id="group-a",
        to_group_id="group-b",
        from_account_id="listener-1",
        content="hello",
    )
    assert observed[0].account_label == "Listener One"
    assert "inserted" in observed[0].summary.lower()


def test_zca_listener_monitor_marks_duplicate_message_events_without_failing() -> None:
    listener = FakeZcaListenerProcess(
        events=[
            ZaloLiveEventLogEntry(
                event_type="new_message",
                scope="listener",
                summary="Incoming message received.",
                detail="hello",
                occurred_at="2026-04-24T10:00:00Z",
                msg_id="msg-1",
                content="hello",
            )
        ]
    )
    use_case = ZcaListenerMonitorUseCase(listener, FakeMessageStore(save_result="already_processed"))
    observed: list[ZaloLiveEventLogEntry] = []

    use_case.start(
        StartZcaListenerRequest(
            account_id="listener-1",
            account_label="Listener One",
            credentials_file_path=r"C:\zca\listener-1.json",
        ),
        observed.append,
    )

    assert "already processed" in observed[0].summary.lower()


def test_zca_listener_monitor_logs_database_failures_without_stopping_listener() -> None:
    listener = FakeZcaListenerProcess(
        events=[
            ZaloLiveEventLogEntry(
                event_type="new_message",
                scope="listener",
                summary="Incoming message received.",
                detail="hello",
                occurred_at="2026-04-24T10:00:00Z",
                msg_id="msg-1",
                content="hello",
            )
        ]
    )
    use_case = ZcaListenerMonitorUseCase(listener, FakeMessageStore(should_fail=True))
    observed: list[ZaloLiveEventLogEntry] = []

    use_case.start(
        StartZcaListenerRequest(
            account_id="listener-1",
            account_label="Listener One",
            credentials_file_path=r"C:\zca\listener-1.json",
        ),
        observed.append,
    )

    assert listener.is_running() is True
    assert observed[0].event_type == "listener_error"
    assert "database" in observed[0].summary.lower()


def test_zca_listener_monitor_rejects_blank_credentials_file_path() -> None:
    use_case = ZcaListenerMonitorUseCase(FakeZcaListenerProcess(), FakeMessageStore())

    try:
        use_case.start(
            StartZcaListenerRequest(
                account_id="listener-1",
                account_label="Listener One",
                credentials_file_path="",
            ),
            lambda event: None,
        )
    except LauncherValidationError as exc:
        assert "credentials file" in str(exc).lower()
    else:
        raise AssertionError("Expected credentials file validation error")


def test_zca_listener_monitor_stops_listener() -> None:
    listener = FakeZcaListenerProcess()
    use_case = ZcaListenerMonitorUseCase(listener, FakeMessageStore())

    use_case.start(
        StartZcaListenerRequest(
            account_id="listener-1",
            account_label="Listener One",
            credentials_file_path=r"C:\zca\listener-1.json",
        ),
        lambda event: None,
    )

    result = use_case.stop()

    assert result.was_running is True
    assert listener.stopped is True
