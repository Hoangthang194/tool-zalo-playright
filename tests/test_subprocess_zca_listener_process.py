from pathlib import Path

from browser_automation.domain.zalo_live_events import ZaloLiveEventLogEntry
from browser_automation.infrastructure.zca.subprocess_zca_listener_process import (
    SubprocessZcaListenerProcess,
)


def test_subprocess_zca_listener_process_builds_expected_command() -> None:
    process = SubprocessZcaListenerProcess(
        node_executable="node",
        script_path=Path(r"C:\tool\src\browser_automation\infrastructure\zca\zca_listener_adapter.mjs"),
    )

    assert process.build_command(credentials_file_path=r"C:\zca\listener.json") == [
        "node",
        r"C:\tool\src\browser_automation\infrastructure\zca\zca_listener_adapter.mjs",
        "--credentials-file",
        r"C:\zca\listener.json",
    ]


def test_subprocess_zca_listener_process_parses_new_message_json_line() -> None:
    process = SubprocessZcaListenerProcess(
        node_executable="node",
        script_path=Path(r"C:\tool\zca_listener_adapter.mjs"),
    )

    event = process.parse_event_line(
        '{"eventType":"new_message","occurredAt":"2026-04-24T10:00:00Z","summary":"Incoming message received.","detail":"hello","msgId":"msg-1","fromGroupId":"group-a","toGroupId":"group-b","content":"hello","rawType":"text"}'
    )

    assert event == ZaloLiveEventLogEntry(
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


def test_subprocess_zca_listener_process_ignores_invalid_json_lines() -> None:
    process = SubprocessZcaListenerProcess(
        node_executable="node",
        script_path=Path(r"C:\tool\zca_listener_adapter.mjs"),
    )

    assert process.parse_event_line("not-json") is None
