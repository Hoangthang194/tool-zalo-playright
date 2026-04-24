from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ZaloAccountMode(StrEnum):
    SEND = "send"
    LISTEN = "listen"


class ZaloAccountRole(StrEnum):
    SENDER = "sender"
    LISTENER = "listener"


@dataclass(frozen=True, slots=True)
class SavedZaloAccount:
    id: str
    name: str
    profile_id: str | None = None
    proxy: str = ""
    role: str = ZaloAccountRole.SENDER.value
    credentials_file_path: str = ""
    mode: str = ""
    listener_token: str = ""

    def __post_init__(self) -> None:
        if not self.mode:
            resolved_mode = (
                ZaloAccountMode.LISTEN.value
                if self.role == ZaloAccountRole.LISTENER.value
                else ZaloAccountMode.SEND.value
            )
            object.__setattr__(self, "mode", resolved_mode)


@dataclass(frozen=True, slots=True)
class SavedZaloClickTarget:
    id: str
    name: str
    selector_kind: str
    selector_value: str
    upload_file_path: str = ""


@dataclass(frozen=True, slots=True)
class ZaloWorkspaceLibrary:
    accounts: tuple[SavedZaloAccount, ...] = ()
    click_targets: tuple[SavedZaloClickTarget, ...] = ()
    selected_account_id: str | None = None
    selected_click_target_id: str | None = None
