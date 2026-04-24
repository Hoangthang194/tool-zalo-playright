from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from browser_automation.domain.exceptions import SettingsPersistenceError
from browser_automation.domain.zalo_workspace import (
    SavedZaloAccount,
    SavedZaloClickTarget,
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

        accounts_payload = payload.get("accounts")
        if not isinstance(accounts_payload, list):
            return ZaloWorkspaceLibrary()

        accounts: list[SavedZaloAccount] = []
        seen_account_ids: set[str] = set()
        for account_payload in accounts_payload:
            account = self._map_account(account_payload)
            if account is None or account.id in seen_account_ids:
                continue
            accounts.append(account)
            seen_account_ids.add(account.id)

        click_targets_payload = payload.get("click_targets")
        click_targets: list[SavedZaloClickTarget] = []
        seen_click_target_ids: set[str] = set()
        if isinstance(click_targets_payload, list):
            for click_target_payload in click_targets_payload:
                click_target = self._map_click_target(click_target_payload)
                if click_target is None or click_target.id in seen_click_target_ids:
                    continue
                click_targets.append(click_target)
                seen_click_target_ids.add(click_target.id)

        selected_account_id = self._optional_str(payload.get("selected_account_id"))
        if selected_account_id not in seen_account_ids:
            selected_account_id = accounts[0].id if accounts else None
        selected_click_target_id = self._optional_str(payload.get("selected_click_target_id"))
        if selected_click_target_id not in seen_click_target_ids:
            selected_click_target_id = click_targets[0].id if click_targets else None

        return ZaloWorkspaceLibrary(
            accounts=tuple(accounts),
            click_targets=tuple(click_targets),
            selected_account_id=selected_account_id,
            selected_click_target_id=selected_click_target_id,
        )

    def save(self, library: ZaloWorkspaceLibrary) -> None:
        payload = {
            "selected_account_id": library.selected_account_id,
            "accounts": [
                {
                    "id": account.id,
                    "name": account.name,
                    "profile_id": account.profile_id,
                    "proxy": account.proxy,
                    "mode": account.mode,
                    "listener_token": account.listener_token,
                }
                for account in library.accounts
            ],
            "selected_click_target_id": library.selected_click_target_id,
            "click_targets": [
                {
                    "id": click_target.id,
                    "name": click_target.name,
                    "selector_kind": click_target.selector_kind,
                    "selector_value": click_target.selector_value,
                    "upload_file_path": click_target.upload_file_path,
                }
                for click_target in library.click_targets
            ],
        }

        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError as exc:
            raise SettingsPersistenceError(
                f"Could not persist Zalo workspace data to '{self._path}'."
            ) from exc

    def _map_account(self, payload: Any) -> SavedZaloAccount | None:
        if not isinstance(payload, dict):
            return None

        account_id = self._optional_str(payload.get("id"))
        name = self._optional_str(payload.get("name"))
        profile_id = self._optional_str(payload.get("profile_id"))
        proxy = self._optional_str(payload.get("proxy")) or ""
        mode = self._optional_str(payload.get("mode")) or "send"
        listener_token = self._optional_str(payload.get("listener_token")) or ""
        if not account_id:
            return None
        if name is None:
            name = profile_id or account_id
        return SavedZaloAccount(
            id=account_id,
            name=name,
            profile_id=profile_id,
            proxy=proxy,
            mode=mode,
            listener_token=listener_token,
        )

    def _map_click_target(self, payload: Any) -> SavedZaloClickTarget | None:
        if not isinstance(payload, dict):
            return None

        click_target_id = self._optional_str(payload.get("id"))
        name = self._optional_str(payload.get("name"))
        selector_kind = self._optional_str(payload.get("selector_kind"))
        selector_value = self._optional_str(payload.get("selector_value"))
        upload_file_path = self._optional_str(payload.get("upload_file_path")) or ""
        if not all((click_target_id, name, selector_kind, selector_value)):
            return None

        return SavedZaloClickTarget(
            id=click_target_id,
            name=name,
            selector_kind=selector_kind,
            selector_value=selector_value,
            upload_file_path=upload_file_path,
        )

    def _optional_str(self, value: Any) -> str | None:
        if value is None or not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None
