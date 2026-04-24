from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ZaloLiveEventLogEntry:
    event_type: str
    scope: str
    summary: str
    occurred_at: str
    detail: str = ""
    account_label: str = ""
    msg_id: str = ""
    from_group_id: str | None = None
    to_group_id: str | None = None
    content: str = ""
    raw_type: str = ""
