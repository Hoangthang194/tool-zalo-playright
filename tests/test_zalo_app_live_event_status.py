import tkinter as tk

from browser_automation.domain.zalo_live_events import ZaloLiveEventLogEntry
from browser_automation.interfaces.gui.zalo_app import ZaloLauncherGui


def test_zalo_gui_keeps_new_message_status_when_receipt_events_arrive() -> None:
    root = tk.Tk()
    try:
        app = ZaloLauncherGui(root)
        app._append_live_event_log_entry(
            ZaloLiveEventLogEntry(
                event_type="new_message",
                scope="dom",
                summary="New incoming message detected for 'Test zalo'.",
                detail="Test 7",
                occurred_at="2026-04-24T10:00:00Z",
                account_label="zalo1",
            )
        )
        app._append_live_event_log_entry(
            ZaloLiveEventLogEntry(
                event_type="delivered",
                scope="network",
                summary="Delivered receipt detected for 'Test zalo'.",
                detail="https://chat.zalo.me/api/delivered",
                occurred_at="2026-04-24T10:00:01Z",
                account_label="zalo1",
            )
        )

        assert app.account_status_var.get() == (
            "New incoming message detected for 'Test zalo'. Test 7"
        )
    finally:
        root.destroy()


def test_zalo_gui_prefers_decoded_new_message_status_over_later_dom_fallback() -> None:
    root = tk.Tk()
    try:
        app = ZaloLauncherGui(root)
        app._append_live_event_log_entry(
            ZaloLiveEventLogEntry(
                event_type="new_message",
                scope="group",
                summary="New group message from 'Hoàng Thắng' in 'Test zalo'.",
                detail="https://example.com/image.jpg",
                occurred_at="2026-04-24T10:00:00Z",
                account_label="zalo1",
            )
        )
        app._append_live_event_log_entry(
            ZaloLiveEventLogEntry(
                event_type="new_message",
                scope="dom",
                summary="New incoming message from 'Hoàng Thắng' in 'Test zalo'.",
                detail="Hình ảnh",
                occurred_at="2026-04-24T10:00:01Z",
                account_label="zalo1",
            )
        )

        assert app.account_status_var.get() == (
            "New group message from 'Hoàng Thắng' in 'Test zalo'. https://example.com/image.jpg"
        )
    finally:
        root.destroy()
