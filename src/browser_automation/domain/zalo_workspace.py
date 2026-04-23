from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SavedZaloAccount:
    id: str
    name: str
    profile_id: str | None = None
    proxy: str = ""


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
