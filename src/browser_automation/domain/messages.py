from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SavedZaloMessage:
    msg_id: str
    from_group_id: str | None
    to_group_id: str | None
    from_account_id: str
    content: str

