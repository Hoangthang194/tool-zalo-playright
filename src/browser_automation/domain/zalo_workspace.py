from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SavedCookieEntry:
    id: str
    name: str
    raw_cookie: str
    profile_id: str | None = None
    notes: str = ""


@dataclass(frozen=True, slots=True)
class SavedZaloAccount:
    id: str
    name: str
    phone_number: str = ""
    profile_id: str | None = None
    cookie_id: str | None = None
    notes: str = ""


@dataclass(frozen=True, slots=True)
class ZaloWorkspaceLibrary:
    cookies: tuple[SavedCookieEntry, ...] = ()
    accounts: tuple[SavedZaloAccount, ...] = ()
    selected_cookie_id: str | None = None
    selected_account_id: str | None = None
