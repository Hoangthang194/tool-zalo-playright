from __future__ import annotations

import socket
from collections.abc import Sequence
from dataclasses import dataclass

from browser_automation.application.ports.chrome_installation_discovery import (
    ChromeInstallationDiscovery,
)
from browser_automation.application.ports.chrome_process_launcher import (
    ChromeProcessLauncher,
)
from browser_automation.application.ports.chrome_window_arranger import ChromeWindowArranger
from browser_automation.application.ports.saved_profile_library_store import (
    SavedProfileLibraryStore,
)
from browser_automation.application.ports.zalo_click_automation_runner import (
    ZaloClickAutomationRunner,
)
from browser_automation.application.ports.zalo_workspace_store import ZaloWorkspaceStore
from browser_automation.application.use_cases._saved_profile_launch_support import (
    SavedProfileLaunchSupport,
)
from browser_automation.application.use_cases.manage_zalo_profiles import (
    DEFAULT_GRID_COLUMNS,
    DEFAULT_GRID_LAUNCH_LIMIT,
    DEFAULT_GRID_ROWS,
)
from browser_automation.domain.exceptions import (
    SavedProfileNotFoundError,
    SavedZaloAccountConflictError,
    SavedZaloAccountNotFoundError,
    SettingsPersistenceError,
)
from browser_automation.domain.zalo_launcher import (
    ChromeLaunchResult,
    SavedChromeProfile,
    SavedProfileLibrary,
    WindowPlacement,
)
from browser_automation.domain.zalo_workspace import SavedZaloAccount, ZaloWorkspaceLibrary

_WINDOW_DETECTION_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True, slots=True)
class LaunchSavedZaloAccountResult:
    account_id: str
    profile_id: str
    profile_name: str
    proxy: str
    launch_result: ChromeLaunchResult
    headless: bool = False
    workspace_persisted: bool = True


@dataclass(frozen=True, slots=True)
class LaunchSavedZaloAccountsResult:
    accounts: tuple[LaunchSavedZaloAccountResult, ...]
    headless: bool
    tiled_window_count: int = 0
    omitted_account_count: int = 0
    workspace_persisted: bool = True


class LaunchZaloAccountUseCase:
    def __init__(
        self,
        workspace_store: ZaloWorkspaceStore,
        library_store: SavedProfileLibraryStore,
        chrome_discovery: ChromeInstallationDiscovery,
        chrome_launcher: ChromeProcessLauncher,
        chrome_window_arranger: ChromeWindowArranger | None = None,
        click_automation_runner: ZaloClickAutomationRunner | None = None,
    ) -> None:
        self._workspace_store = workspace_store
        self._library_store = library_store
        self._chrome_launcher = chrome_launcher
        self._chrome_window_arranger = chrome_window_arranger
        self._launch_support = SavedProfileLaunchSupport(chrome_discovery)
        self._click_automation_runner = click_automation_runner

    def launch_account(
        self,
        account_id: str | None = None,
        *,
        headless: bool = False,
    ) -> LaunchSavedZaloAccountResult:
        workspace = self._normalized_workspace(self._workspace_store.load())
        account = self._resolve_account_for_launch(account_id, workspace)
        if account.profile_id is None:
            raise SavedZaloAccountConflictError("Saved Zalo account requires a linked profile.")

        library = self._normalized_library(self._library_store.load())
        profile = self._find_profile(account.profile_id, library)

        existing_window_handles: set[int] | None = None
        if self._chrome_window_arranger is not None and not headless:
            existing_window_handles = set(self._chrome_window_arranger.snapshot_window_handles())

        remote_debugging_port = None
        if self._click_automation_runner is not None:
            remote_debugging_port = _allocate_local_port()

        config = self._launch_support.prepare_launch_config(
            profile,
            window_placement=self._single_profile_window_placement(
                existing_window_count=0 if existing_window_handles is None else len(existing_window_handles)
            ) if not headless else None,
            proxy_server=account.proxy,
            remote_debugging_port=remote_debugging_port,
            headless=headless,
        )
        workspace_persisted = self._persist_selected_account_id(account.id, workspace)

        self._chrome_launcher.launch(config)
        if self._chrome_window_arranger is not None and existing_window_handles is not None:
            window_handle = self._chrome_window_arranger.wait_for_new_window(
                existing_window_handles,
                timeout_seconds=_WINDOW_DETECTION_TIMEOUT_SECONDS,
            )
            if window_handle is not None and config.window_placement is not None:
                self._chrome_window_arranger.apply_window_placement(
                    window_handle,
                    config.window_placement,
                )

        return LaunchSavedZaloAccountResult(
            account_id=account.id,
            profile_id=profile.id,
            profile_name=profile.name,
            proxy=account.proxy,
            launch_result=ChromeLaunchResult(
                chrome_executable=config.chrome_executable,
                user_data_dir=config.user_data_dir,
                profile_directory=config.profile_directory,
                target_url=config.target_url,
                settings_persisted=True,
                headless=config.headless,
                proxy_server=config.proxy_server,
                remote_debugging_port=config.remote_debugging_port,
                window_placement=config.window_placement,
            ),
            headless=headless,
            workspace_persisted=workspace_persisted,
        )

    def launch_accounts(
        self,
        account_ids: Sequence[str],
        *,
        headless: bool = False,
    ) -> LaunchSavedZaloAccountsResult:
        workspace = self._normalized_workspace(self._workspace_store.load())
        selected_accounts = self._resolve_accounts_for_launch(account_ids, workspace)
        profiles_by_id = {
            profile.id: profile for profile in self._normalized_library(self._library_store.load()).profiles
        }
        launch_limit = DEFAULT_GRID_LAUNCH_LIMIT
        omitted_account_count = max(0, len(selected_accounts) - launch_limit)
        accounts_to_launch = selected_accounts[:launch_limit]

        prepared_launches: list[tuple[SavedZaloAccount, SavedChromeProfile, ChromeLaunchConfig]] = []
        placements: tuple[WindowPlacement, ...] = ()
        existing_window_handles: set[int] | None = None
        if not headless:
            if self._chrome_window_arranger is None:
                raise ChromeLaunchError("Chrome window arrangement is not configured.")
            placements = self._chrome_window_arranger.calculate_grid_placements(
                count=len(accounts_to_launch),
                columns=DEFAULT_GRID_COLUMNS,
                rows=DEFAULT_GRID_ROWS,
            )
            existing_window_handles = set(self._chrome_window_arranger.snapshot_window_handles())

        for index, account in enumerate(accounts_to_launch):
            if account.profile_id is None:
                raise SavedZaloAccountConflictError("Saved Zalo account requires a linked profile.")
            profile = profiles_by_id.get(account.profile_id)
            if profile is None:
                raise SavedProfileNotFoundError(
                    f"Linked saved Chrome profile not found for Zalo account: {account.profile_id}"
                )
            remote_debugging_port = _allocate_local_port() if self._click_automation_runner is not None else None
            prepared_launches.append(
                (
                    account,
                    profile,
                    self._launch_support.prepare_launch_config(
                        profile,
                        window_placement=placements[index] if index < len(placements) else None,
                        proxy_server=account.proxy,
                        remote_debugging_port=remote_debugging_port,
                        headless=headless,
                    ),
                )
            )

        workspace_persisted = self._persist_selected_account_id(accounts_to_launch[0].id, workspace)
        launched_accounts: list[LaunchSavedZaloAccountResult] = []
        detected_window_handles: list[int] = []

        for account, profile, config in prepared_launches:
            self._chrome_launcher.launch(config)
            window_handle = None
            if self._chrome_window_arranger is not None and existing_window_handles is not None:
                window_handle = self._chrome_window_arranger.wait_for_new_window(
                    existing_window_handles,
                    timeout_seconds=_WINDOW_DETECTION_TIMEOUT_SECONDS,
                )
                if window_handle is not None:
                    existing_window_handles.add(window_handle)
                    detected_window_handles.append(window_handle)
            launched_accounts.append(
                LaunchSavedZaloAccountResult(
                    account_id=account.id,
                    profile_id=profile.id,
                    profile_name=profile.name,
                    proxy=account.proxy,
                    launch_result=ChromeLaunchResult(
                        chrome_executable=config.chrome_executable,
                        user_data_dir=config.user_data_dir,
                        profile_directory=config.profile_directory,
                        target_url=config.target_url,
                        settings_persisted=True,
                        headless=config.headless,
                        proxy_server=config.proxy_server,
                        remote_debugging_port=config.remote_debugging_port,
                        window_placement=config.window_placement,
                    ),
                    headless=headless,
                    workspace_persisted=workspace_persisted,
                )
            )

        tiled_window_count = 0
        if self._chrome_window_arranger is not None and detected_window_handles:
            tiled_window_count = self._chrome_window_arranger.tile_windows(
                detected_window_handles,
                columns=DEFAULT_GRID_COLUMNS,
                rows=DEFAULT_GRID_ROWS,
            )

        return LaunchSavedZaloAccountsResult(
            accounts=tuple(launched_accounts),
            headless=headless,
            tiled_window_count=0 if headless else tiled_window_count,
            omitted_account_count=omitted_account_count,
            workspace_persisted=workspace_persisted,
        )

    def _normalized_workspace(self, library: ZaloWorkspaceLibrary) -> ZaloWorkspaceLibrary:
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

    def _normalized_library(self, library: SavedProfileLibrary) -> SavedProfileLibrary:
        if not library.profiles:
            return SavedProfileLibrary()

        profile_ids = {profile.id for profile in library.profiles}
        selected_profile_id = library.selected_profile_id
        if selected_profile_id not in profile_ids:
            selected_profile_id = library.profiles[0].id

        return SavedProfileLibrary(
            profiles=library.profiles,
            selected_profile_id=selected_profile_id,
        )

    def _resolve_account_for_launch(
        self,
        account_id: str | None,
        workspace: ZaloWorkspaceLibrary,
    ) -> SavedZaloAccount:
        resolved_account_id = account_id or workspace.selected_account_id
        if resolved_account_id is None:
            raise SavedZaloAccountNotFoundError("No saved Zalo account is selected.")
        return self._find_account(resolved_account_id, workspace)

    def _find_account(self, account_id: str, workspace: ZaloWorkspaceLibrary) -> SavedZaloAccount:
        for account in workspace.accounts:
            if account.id == account_id:
                return account
        raise SavedZaloAccountNotFoundError(f"Saved Zalo account not found: {account_id}")

    def _resolve_accounts_for_launch(
        self,
        account_ids: Sequence[str],
        workspace: ZaloWorkspaceLibrary,
    ) -> tuple[SavedZaloAccount, ...]:
        if not account_ids:
            raise SavedZaloAccountNotFoundError("Select at least one saved Zalo account.")

        unique_account_ids: list[str] = []
        seen_account_ids: set[str] = set()
        for account_id in account_ids:
            if account_id in seen_account_ids:
                continue
            unique_account_ids.append(account_id)
            seen_account_ids.add(account_id)

        return tuple(self._find_account(account_id, workspace) for account_id in unique_account_ids)

    def _find_profile(self, profile_id: str, library: SavedProfileLibrary) -> SavedChromeProfile:
        for profile in library.profiles:
            if profile.id == profile_id:
                return profile
        raise SavedProfileNotFoundError(
            f"Linked saved Chrome profile not found for Zalo account: {profile_id}"
        )

    def _single_profile_window_placement(self, *, existing_window_count: int) -> WindowPlacement | None:
        if self._chrome_window_arranger is None:
            return None
        placement_index = min(existing_window_count, DEFAULT_GRID_LAUNCH_LIMIT - 1)
        placements = self._chrome_window_arranger.calculate_grid_placements(
            count=placement_index + 1,
            columns=DEFAULT_GRID_COLUMNS,
            rows=DEFAULT_GRID_ROWS,
        )
        if not placements:
            return None
        return placements[placement_index]

    def _persist_selected_account_id(
        self,
        selected_account_id: str,
        workspace: ZaloWorkspaceLibrary,
    ) -> bool:
        if workspace.selected_account_id == selected_account_id:
            return True

        try:
            self._workspace_store.save(
                ZaloWorkspaceLibrary(
                    accounts=workspace.accounts,
                    click_targets=workspace.click_targets,
                    selected_account_id=selected_account_id,
                    selected_click_target_id=workspace.selected_click_target_id,
                )
            )
        except SettingsPersistenceError:
            return False
        return True


def _allocate_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]
