from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from browser_automation.application.ports.zalo_workspace_store import ZaloWorkspaceStore
from browser_automation.domain.exceptions import (
    SavedZaloAccountConflictError,
    SavedZaloAccountNotFoundError,
)
from browser_automation.domain.zalo_workspace import (
    SavedZaloAccount,
    ZaloWorkspaceLibrary,
)


@dataclass(frozen=True, slots=True)
class ZaloAccountUpsertRequest:
    name: str
    account_id: str | None = None
    profile_id: str | None = None
    proxy: str = ""


@dataclass(frozen=True, slots=True)
class ZaloWorkspaceState:
    accounts: tuple[SavedZaloAccount, ...]
    selected_account_id: str | None


class ZaloWorkspaceManagerUseCase:
    def __init__(self, workspace_store: ZaloWorkspaceStore) -> None:
        self._workspace_store = workspace_store

    def load_state(self) -> ZaloWorkspaceState:
        return self._build_state(self._normalized_library(self._workspace_store.load()))

    def select_account(self, account_id: str) -> ZaloWorkspaceState:
        library = self._normalized_library(self._workspace_store.load())
        self._find_account(account_id, library)
        updated_library = ZaloWorkspaceLibrary(
            accounts=library.accounts,
            click_targets=library.click_targets,
            selected_account_id=account_id,
            selected_click_target_id=library.selected_click_target_id,
        )
        self._workspace_store.save(updated_library)
        return self._build_state(updated_library)

    def save_account(self, request: ZaloAccountUpsertRequest) -> ZaloWorkspaceState:
        library = self._normalized_library(self._workspace_store.load())
        account_name = self._normalize_required_name(
            request.name,
            conflict_error_type=SavedZaloAccountConflictError,
            empty_message="A linked profile is required.",
        )
        profile_id = self._normalize_optional_value(request.profile_id)
        proxy = request.proxy.strip()

        if profile_id is None:
            raise SavedZaloAccountConflictError("A linked profile is required.")

        self._ensure_unique_linked_profile(profile_id, request.account_id, library)

        account = SavedZaloAccount(
            id=request.account_id or uuid4().hex,
            name=account_name,
            profile_id=profile_id,
            proxy=proxy,
        )
        next_accounts = self._replace_or_append_account(account, library.accounts)
        updated_library = ZaloWorkspaceLibrary(
            accounts=next_accounts,
            click_targets=library.click_targets,
            selected_account_id=account.id,
            selected_click_target_id=library.selected_click_target_id,
        )
        self._workspace_store.save(updated_library)
        return self._build_state(updated_library)

    def delete_account(self, account_id: str) -> ZaloWorkspaceState:
        library = self._normalized_library(self._workspace_store.load())
        self._find_account(account_id, library)
        next_accounts = tuple(account for account in library.accounts if account.id != account_id)
        next_selected_account_id = library.selected_account_id
        remaining_account_ids = {account.id for account in next_accounts}
        if next_selected_account_id not in remaining_account_ids:
            next_selected_account_id = next_accounts[0].id if next_accounts else None
        updated_library = ZaloWorkspaceLibrary(
            accounts=next_accounts,
            click_targets=library.click_targets,
            selected_account_id=next_selected_account_id,
            selected_click_target_id=library.selected_click_target_id,
        )
        self._workspace_store.save(updated_library)
        return self._build_state(updated_library)

    def _build_state(self, library: ZaloWorkspaceLibrary) -> ZaloWorkspaceState:
        return ZaloWorkspaceState(
            accounts=library.accounts,
            selected_account_id=library.selected_account_id,
        )

    def _normalized_library(self, library: ZaloWorkspaceLibrary) -> ZaloWorkspaceLibrary:
        account_ids = {account.id for account in library.accounts}

        selected_account_id = library.selected_account_id
        if selected_account_id not in account_ids:
            selected_account_id = library.accounts[0].id if library.accounts else None

        return ZaloWorkspaceLibrary(
            accounts=library.accounts,
            click_targets=library.click_targets,
            selected_account_id=selected_account_id,
            selected_click_target_id=library.selected_click_target_id,
        )

    def _replace_or_append_account(
        self,
        account: SavedZaloAccount,
        existing_accounts: tuple[SavedZaloAccount, ...],
    ) -> tuple[SavedZaloAccount, ...]:
        next_accounts: list[SavedZaloAccount] = []
        replaced = False
        for current_account in existing_accounts:
            if current_account.id == account.id:
                next_accounts.append(account)
                replaced = True
            else:
                next_accounts.append(current_account)
        if not replaced:
            next_accounts.append(account)
        return tuple(next_accounts)

    def _find_account(self, account_id: str, library: ZaloWorkspaceLibrary) -> SavedZaloAccount:
        for account in library.accounts:
            if account.id == account_id:
                return account
        raise SavedZaloAccountNotFoundError(f"Saved Zalo account not found: {account_id}")

    def _ensure_unique_linked_profile(
        self,
        profile_id: str,
        current_account_id: str | None,
        library: ZaloWorkspaceLibrary,
    ) -> None:
        for account in library.accounts:
            if account.id == current_account_id:
                continue
            if account.profile_id == profile_id:
                raise SavedZaloAccountConflictError(
                    "A Zalo account entry for the selected profile already exists."
                )

    def _normalize_required_name(
        self,
        value: str,
        *,
        conflict_error_type,
        empty_message: str,
    ) -> str:
        normalized = value.strip()
        if not normalized:
            raise conflict_error_type(empty_message)
        return normalized

    def _normalize_optional_value(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None
