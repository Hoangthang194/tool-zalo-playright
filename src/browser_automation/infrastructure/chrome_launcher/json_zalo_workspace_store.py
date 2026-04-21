from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from browser_automation.domain.exceptions import SettingsPersistenceError
from browser_automation.domain.zalo_workspace import (
    SavedCookieEntry,
    SavedZaloAccount,
    ZaloWorkspaceLibrary,
)


def default_zalo_workspace_path(environ: Mapping[str, str] | None = None) -> Path:
    environment = os.environ if environ is None else environ
    app_data = environment.get("APPDATA")
    if app_data:
        return Path(app_data) / "browser-automation" / "zalo-workspace.json"
    return Path.home() / ".browser-automation" / "zalo-workspace.json"


class JsonZaloWorkspaceStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or default_zalo_workspace_path()

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> ZaloWorkspaceLibrary:
        if not self._path.is_file():
            return ZaloWorkspaceLibrary()

        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ZaloWorkspaceLibrary()

        if not isinstance(payload, dict):
            return ZaloWorkspaceLibrary()

        cookies_payload = payload.get("cookies")
        accounts_payload = payload.get("accounts")
        if not isinstance(cookies_payload, list) or not isinstance(accounts_payload, list):
            return ZaloWorkspaceLibrary()

        cookies: list[SavedCookieEntry] = []
        seen_cookie_ids: set[str] = set()
        for cookie_payload in cookies_payload:
            cookie = self._map_cookie(cookie_payload)
            if cookie is None or cookie.id in seen_cookie_ids:
                continue
            cookies.append(cookie)
            seen_cookie_ids.add(cookie.id)

        accounts: list[SavedZaloAccount] = []
        seen_account_ids: set[str] = set()
        for account_payload in accounts_payload:
            account = self._map_account(account_payload)
            if account is None or account.id in seen_account_ids:
                continue
            accounts.append(account)
            seen_account_ids.add(account.id)

        selected_cookie_id = self._optional_str(payload.get("selected_cookie_id"))
        if selected_cookie_id not in seen_cookie_ids:
            selected_cookie_id = cookies[0].id if cookies else None

        selected_account_id = self._optional_str(payload.get("selected_account_id"))
        if selected_account_id not in seen_account_ids:
            selected_account_id = accounts[0].id if accounts else None

        return ZaloWorkspaceLibrary(
            cookies=tuple(cookies),
            accounts=tuple(accounts),
            selected_cookie_id=selected_cookie_id,
            selected_account_id=selected_account_id,
        )

    def save(self, library: ZaloWorkspaceLibrary) -> None:
        payload = {
            "selected_cookie_id": library.selected_cookie_id,
            "selected_account_id": library.selected_account_id,
            "cookies": [
                {
                    "id": cookie.id,
                    "name": cookie.name,
                    "raw_cookie": cookie.raw_cookie,
                    "profile_id": cookie.profile_id,
                    "notes": cookie.notes,
                }
                for cookie in library.cookies
            ],
            "accounts": [
                {
                    "id": account.id,
                    "name": account.name,
                    "phone_number": account.phone_number,
                    "profile_id": account.profile_id,
                    "cookie_id": account.cookie_id,
                    "notes": account.notes,
                }
                for account in library.accounts
            ],
        }

        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError as exc:
            raise SettingsPersistenceError(
                f"Could not persist Zalo workspace data to '{self._path}'."
            ) from exc

    def _map_cookie(self, payload: Any) -> SavedCookieEntry | None:
        if not isinstance(payload, dict):
            return None

        cookie_id = self._optional_str(payload.get("id"))
        name = self._optional_str(payload.get("name"))
        raw_cookie = self._optional_str(payload.get("raw_cookie"))
        profile_id = self._optional_str(payload.get("profile_id"))
        notes = self._optional_str(payload.get("notes")) or ""
        if not all((cookie_id, name, raw_cookie)):
            return None
        return SavedCookieEntry(
            id=cookie_id,
            name=name,
            raw_cookie=raw_cookie,
            profile_id=profile_id,
            notes=notes,
        )

    def _map_account(self, payload: Any) -> SavedZaloAccount | None:
        if not isinstance(payload, dict):
            return None

        account_id = self._optional_str(payload.get("id"))
        name = self._optional_str(payload.get("name"))
        phone_number = self._optional_str(payload.get("phone_number")) or ""
        profile_id = self._optional_str(payload.get("profile_id"))
        cookie_id = self._optional_str(payload.get("cookie_id"))
        notes = self._optional_str(payload.get("notes")) or ""
        if not all((account_id, name)):
            return None
        return SavedZaloAccount(
            id=account_id,
            name=name,
            phone_number=phone_number,
            profile_id=profile_id,
            cookie_id=cookie_id,
            notes=notes,
        )

    def _optional_str(self, value: Any) -> str | None:
        if value is None or not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None
