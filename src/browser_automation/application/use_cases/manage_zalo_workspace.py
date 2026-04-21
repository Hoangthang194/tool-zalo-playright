from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from browser_automation.application.ports.zalo_workspace_store import ZaloWorkspaceStore
from browser_automation.domain.exceptions import (
    SavedCookieConflictError,
    SavedCookieNotFoundError,
    SavedZaloAccountConflictError,
    SavedZaloAccountNotFoundError,
)
from browser_automation.domain.zalo_workspace import (
    SavedCookieEntry,
    SavedZaloAccount,
    ZaloWorkspaceLibrary,
)


@dataclass(frozen=True, slots=True)
class CookieUpsertRequest:
    name: str
    raw_cookie: str
    cookie_id: str | None = None
    profile_id: str | None = None
    notes: str = ""


@dataclass(frozen=True, slots=True)
class ZaloAccountUpsertRequest:
    name: str
    phone_number: str = ""
    account_id: str | None = None
    profile_id: str | None = None
    cookie_id: str | None = None
    notes: str = ""


@dataclass(frozen=True, slots=True)
class ZaloWorkspaceState:
    cookies: tuple[SavedCookieEntry, ...]
    accounts: tuple[SavedZaloAccount, ...]
    selected_cookie_id: str | None
    selected_account_id: str | None


class ZaloWorkspaceManagerUseCase:
    def __init__(self, workspace_store: ZaloWorkspaceStore) -> None:
        self._workspace_store = workspace_store

    def load_state(self) -> ZaloWorkspaceState:
        return self._build_state(self._normalized_library(self._workspace_store.load()))

    def select_cookie(self, cookie_id: str) -> ZaloWorkspaceState:
        library = self._normalized_library(self._workspace_store.load())
        self._find_cookie(cookie_id, library)
        updated_library = ZaloWorkspaceLibrary(
            cookies=library.cookies,
            accounts=library.accounts,
            selected_cookie_id=cookie_id,
            selected_account_id=library.selected_account_id,
        )
        self._workspace_store.save(updated_library)
        return self._build_state(updated_library)

    def save_cookie(self, request: CookieUpsertRequest) -> ZaloWorkspaceState:
        library = self._normalized_library(self._workspace_store.load())
        cookie_name = self._normalize_required_name(
            request.name,
            conflict_error_type=SavedCookieConflictError,
            empty_message="Cookie name is required.",
        )
        raw_cookie = self._normalize_required_text(
            request.raw_cookie,
            error_type=SavedCookieConflictError,
            empty_message="Cookie payload is required.",
        )
        profile_id = self._normalize_optional_value(request.profile_id)
        notes = request.notes.strip()

        self._ensure_unique_cookie_name(cookie_name, request.cookie_id, library)

        cookie = SavedCookieEntry(
            id=request.cookie_id or uuid4().hex,
            name=cookie_name,
            raw_cookie=raw_cookie,
            profile_id=profile_id,
            notes=notes,
        )
        next_cookies = self._replace_or_append_cookie(cookie, library.cookies)
        updated_library = ZaloWorkspaceLibrary(
            cookies=next_cookies,
            accounts=library.accounts,
            selected_cookie_id=cookie.id,
            selected_account_id=library.selected_account_id,
        )
        self._workspace_store.save(updated_library)
        return self._build_state(updated_library)

    def delete_cookie(self, cookie_id: str) -> ZaloWorkspaceState:
        library = self._normalized_library(self._workspace_store.load())
        self._find_cookie(cookie_id, library)
        next_cookies = tuple(cookie for cookie in library.cookies if cookie.id != cookie_id)
        next_selected_cookie_id = library.selected_cookie_id
        remaining_cookie_ids = {cookie.id for cookie in next_cookies}
        if next_selected_cookie_id not in remaining_cookie_ids:
            next_selected_cookie_id = next_cookies[0].id if next_cookies else None
        updated_library = ZaloWorkspaceLibrary(
            cookies=next_cookies,
            accounts=library.accounts,
            selected_cookie_id=next_selected_cookie_id,
            selected_account_id=library.selected_account_id,
        )
        self._workspace_store.save(updated_library)
        return self._build_state(updated_library)

    def select_account(self, account_id: str) -> ZaloWorkspaceState:
        library = self._normalized_library(self._workspace_store.load())
        self._find_account(account_id, library)
        updated_library = ZaloWorkspaceLibrary(
            cookies=library.cookies,
            accounts=library.accounts,
            selected_cookie_id=library.selected_cookie_id,
            selected_account_id=account_id,
        )
        self._workspace_store.save(updated_library)
        return self._build_state(updated_library)

    def save_account(self, request: ZaloAccountUpsertRequest) -> ZaloWorkspaceState:
        library = self._normalized_library(self._workspace_store.load())
        account_name = self._normalize_required_name(
            request.name,
            conflict_error_type=SavedZaloAccountConflictError,
            empty_message="Account name is required.",
        )
        phone_number = request.phone_number.strip()
        profile_id = self._normalize_optional_value(request.profile_id)
        cookie_id = self._normalize_optional_value(request.cookie_id)
        notes = request.notes.strip()

        self._ensure_unique_account_name(account_name, request.account_id, library)

        account = SavedZaloAccount(
            id=request.account_id or uuid4().hex,
            name=account_name,
            phone_number=phone_number,
            profile_id=profile_id,
            cookie_id=cookie_id,
            notes=notes,
        )
        next_accounts = self._replace_or_append_account(account, library.accounts)
        updated_library = ZaloWorkspaceLibrary(
            cookies=library.cookies,
            accounts=next_accounts,
            selected_cookie_id=library.selected_cookie_id,
            selected_account_id=account.id,
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
            cookies=library.cookies,
            accounts=next_accounts,
            selected_cookie_id=library.selected_cookie_id,
            selected_account_id=next_selected_account_id,
        )
        self._workspace_store.save(updated_library)
        return self._build_state(updated_library)

    def _build_state(self, library: ZaloWorkspaceLibrary) -> ZaloWorkspaceState:
        return ZaloWorkspaceState(
            cookies=library.cookies,
            accounts=library.accounts,
            selected_cookie_id=library.selected_cookie_id,
            selected_account_id=library.selected_account_id,
        )

    def _normalized_library(self, library: ZaloWorkspaceLibrary) -> ZaloWorkspaceLibrary:
        cookie_ids = {cookie.id for cookie in library.cookies}
        account_ids = {account.id for account in library.accounts}

        selected_cookie_id = library.selected_cookie_id
        if selected_cookie_id not in cookie_ids:
            selected_cookie_id = library.cookies[0].id if library.cookies else None

        selected_account_id = library.selected_account_id
        if selected_account_id not in account_ids:
            selected_account_id = library.accounts[0].id if library.accounts else None

        return ZaloWorkspaceLibrary(
            cookies=library.cookies,
            accounts=library.accounts,
            selected_cookie_id=selected_cookie_id,
            selected_account_id=selected_account_id,
        )

    def _replace_or_append_cookie(
        self,
        cookie: SavedCookieEntry,
        existing_cookies: tuple[SavedCookieEntry, ...],
    ) -> tuple[SavedCookieEntry, ...]:
        next_cookies: list[SavedCookieEntry] = []
        replaced = False
        for current_cookie in existing_cookies:
            if current_cookie.id == cookie.id:
                next_cookies.append(cookie)
                replaced = True
            else:
                next_cookies.append(current_cookie)
        if not replaced:
            next_cookies.append(cookie)
        return tuple(next_cookies)

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

    def _find_cookie(self, cookie_id: str, library: ZaloWorkspaceLibrary) -> SavedCookieEntry:
        for cookie in library.cookies:
            if cookie.id == cookie_id:
                return cookie
        raise SavedCookieNotFoundError(f"Saved cookie not found: {cookie_id}")

    def _find_account(self, account_id: str, library: ZaloWorkspaceLibrary) -> SavedZaloAccount:
        for account in library.accounts:
            if account.id == account_id:
                return account
        raise SavedZaloAccountNotFoundError(f"Saved Zalo account not found: {account_id}")

    def _ensure_unique_cookie_name(
        self,
        name: str,
        current_cookie_id: str | None,
        library: ZaloWorkspaceLibrary,
    ) -> None:
        target_name = name.casefold()
        for cookie in library.cookies:
            if cookie.id == current_cookie_id:
                continue
            if cookie.name.casefold() == target_name:
                raise SavedCookieConflictError(f"A saved cookie named '{name}' already exists.")

    def _ensure_unique_account_name(
        self,
        name: str,
        current_account_id: str | None,
        library: ZaloWorkspaceLibrary,
    ) -> None:
        target_name = name.casefold()
        for account in library.accounts:
            if account.id == current_account_id:
                continue
            if account.name.casefold() == target_name:
                raise SavedZaloAccountConflictError(f"A saved account named '{name}' already exists.")

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

    def _normalize_required_text(
        self,
        value: str,
        *,
        error_type,
        empty_message: str,
    ) -> str:
        normalized = value.strip()
        if not normalized:
            raise error_type(empty_message)
        return normalized

    def _normalize_optional_value(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None
