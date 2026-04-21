from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

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
from browser_automation.domain.exceptions import (
    ChromeLaunchError,
    LauncherValidationError,
    SavedProfileConflictError,
    SavedProfileNotFoundError,
    SettingsPersistenceError,
)
from browser_automation.domain.zalo_launcher import (
    DEFAULT_ZALO_URL,
    ChromeLaunchConfig,
    ChromeLaunchResult,
    SavedChromeProfile,
    SavedProfileLibrary,
    WindowPlacement,
)

_SUPPORTED_CHROME_EXECUTABLE_NAMES = {
    "chrome.exe",
    "chrome",
    "google-chrome",
    "google-chrome-stable",
}
DEFAULT_GRID_COLUMNS = 4
DEFAULT_GRID_ROWS = 2
DEFAULT_GRID_LAUNCH_LIMIT = DEFAULT_GRID_COLUMNS * DEFAULT_GRID_ROWS
_GRID_WINDOW_DETECTION_TIMEOUT_SECONDS = 10.0


@dataclass(frozen=True, slots=True)
class SavedProfileUpsertRequest:
    name: str
    chrome_executable: str
    profile_path: str
    profile_id: str | None = None
    target_url: str = DEFAULT_ZALO_URL


@dataclass(frozen=True, slots=True)
class ZaloProfileManagerState:
    profiles: tuple[SavedChromeProfile, ...]
    selected_profile_id: str | None
    default_chrome_executable: str
    default_profile_root: str
    target_url: str = DEFAULT_ZALO_URL


@dataclass(frozen=True, slots=True)
class LaunchSavedProfileResult:
    profile_id: str
    profile_name: str
    launch_result: ChromeLaunchResult
    library_persisted: bool = True


@dataclass(frozen=True, slots=True)
class GridLaunchedProfileResult:
    profile_id: str
    profile_name: str
    launch_result: ChromeLaunchResult
    window_detected: bool = True


@dataclass(frozen=True, slots=True)
class LaunchSavedProfilesGridResult:
    profiles: tuple[GridLaunchedProfileResult, ...]
    grid_columns: int = DEFAULT_GRID_COLUMNS
    grid_rows: int = DEFAULT_GRID_ROWS
    tiled_window_count: int = 0
    omitted_profile_count: int = 0
    library_persisted: bool = True


class ZaloProfileManagerUseCase:
    def __init__(
        self,
        library_store: SavedProfileLibraryStore,
        chrome_discovery: ChromeInstallationDiscovery,
        chrome_launcher: ChromeProcessLauncher,
        chrome_window_arranger: ChromeWindowArranger | None = None,
    ) -> None:
        self._library_store = library_store
        self._chrome_discovery = chrome_discovery
        self._chrome_launcher = chrome_launcher
        self._chrome_window_arranger = chrome_window_arranger

    def load_state(self) -> ZaloProfileManagerState:
        return self._build_state(self._normalized_library(self._library_store.load()))

    def save_profile(self, request: SavedProfileUpsertRequest) -> ZaloProfileManagerState:
        library = self._normalized_library(self._library_store.load())
        profile_name = self._normalize_name(request.name)
        chrome_executable = self._resolve_chrome_executable(request.chrome_executable)
        profile_path = self._resolve_profile_path(request.profile_path)
        self._validate_target_url(request.target_url)

        self._ensure_unique_name(profile_name, request.profile_id, library)
        self._ensure_unique_profile_path(profile_path, request.profile_id, library)

        profile = SavedChromeProfile(
            id=request.profile_id or uuid4().hex,
            name=profile_name,
            chrome_executable=str(chrome_executable),
            profile_path=str(profile_path),
            target_url=request.target_url,
        )

        next_profiles: list[SavedChromeProfile] = []
        replaced = False
        for current_profile in library.profiles:
            if current_profile.id == profile.id:
                next_profiles.append(profile)
                replaced = True
            else:
                next_profiles.append(current_profile)
        if not replaced:
            next_profiles.append(profile)

        updated_library = SavedProfileLibrary(
            profiles=tuple(next_profiles),
            selected_profile_id=profile.id,
        )
        self._library_store.save(updated_library)
        return self._build_state(updated_library)

    def delete_profile(self, profile_id: str) -> ZaloProfileManagerState:
        library = self._normalized_library(self._library_store.load())
        profile = self._find_profile(profile_id, library)

        next_profiles = tuple(
            current_profile for current_profile in library.profiles if current_profile.id != profile.id
        )
        next_selected_id = library.selected_profile_id
        remaining_ids = {current_profile.id for current_profile in next_profiles}
        if next_selected_id not in remaining_ids:
            next_selected_id = next_profiles[0].id if next_profiles else None

        updated_library = SavedProfileLibrary(
            profiles=next_profiles,
            selected_profile_id=next_selected_id,
        )
        self._library_store.save(updated_library)
        return self._build_state(updated_library)

    def select_profile(self, profile_id: str) -> ZaloProfileManagerState:
        library = self._normalized_library(self._library_store.load())
        self._find_profile(profile_id, library)

        updated_library = SavedProfileLibrary(
            profiles=library.profiles,
            selected_profile_id=profile_id,
        )
        self._library_store.save(updated_library)
        return self._build_state(updated_library)

    def launch_profile(self, profile_id: str | None = None) -> LaunchSavedProfileResult:
        library = self._normalized_library(self._library_store.load())
        selected_profile = self._resolve_profile_for_launch(profile_id, library)
        existing_window_handles: set[int] | None = None
        if self._chrome_window_arranger is not None:
            existing_window_handles = set(self._chrome_window_arranger.snapshot_window_handles())
        config = self._prepare_launch_config(
            selected_profile,
            window_placement=self._single_profile_window_placement(
                existing_window_count=0 if existing_window_handles is None else len(existing_window_handles)
            ),
        )
        library_persisted = self._persist_selected_profile_id(selected_profile.id, library)

        self._chrome_launcher.launch(config)
        if self._chrome_window_arranger is not None and existing_window_handles is not None:
            window_handle = self._chrome_window_arranger.wait_for_new_window(
                existing_window_handles,
                timeout_seconds=_GRID_WINDOW_DETECTION_TIMEOUT_SECONDS,
            )
            if window_handle is not None and config.window_placement is not None:
                self._chrome_window_arranger.apply_window_placement(
                    window_handle,
                    config.window_placement,
                )
        launch_result = self._build_launch_result(config)

        return LaunchSavedProfileResult(
            profile_id=selected_profile.id,
            profile_name=selected_profile.name,
            launch_result=launch_result,
            library_persisted=library_persisted,
        )

    def launch_profiles_grid(
        self,
        profile_ids: Sequence[str],
        *,
        columns: int = DEFAULT_GRID_COLUMNS,
        rows: int = DEFAULT_GRID_ROWS,
    ) -> LaunchSavedProfilesGridResult:
        library = self._normalized_library(self._library_store.load())
        selected_profiles = self._resolve_profiles_for_grid_launch(profile_ids, library)
        launch_limit = columns * rows
        omitted_profile_count = max(0, len(selected_profiles) - launch_limit)
        profiles_to_launch = selected_profiles[:launch_limit]

        if self._chrome_window_arranger is None:
            raise ChromeLaunchError("Chrome window arrangement is not configured.")

        planned_window_placements = self._chrome_window_arranger.calculate_grid_placements(
            count=len(profiles_to_launch),
            columns=columns,
            rows=rows,
        )
        prepared_launches = tuple(
            (
                profile,
                self._prepare_launch_config(
                    profile,
                    window_placement=planned_window_placements[index]
                    if index < len(planned_window_placements)
                    else None,
                ),
            )
            for index, profile in enumerate(profiles_to_launch)
        )

        library_persisted = self._persist_selected_profile_id(profiles_to_launch[0].id, library)
        existing_window_handles = set(self._chrome_window_arranger.snapshot_window_handles())
        detected_window_handles: list[int] = []
        launched_profiles: list[GridLaunchedProfileResult] = []

        for profile, config in prepared_launches:
            self._chrome_launcher.launch(config)
            window_handle = self._chrome_window_arranger.wait_for_new_window(
                existing_window_handles,
                timeout_seconds=_GRID_WINDOW_DETECTION_TIMEOUT_SECONDS,
            )
            if window_handle is not None:
                existing_window_handles.add(window_handle)
                detected_window_handles.append(window_handle)

            launched_profiles.append(
                GridLaunchedProfileResult(
                    profile_id=profile.id,
                    profile_name=profile.name,
                    launch_result=self._build_launch_result(config),
                    window_detected=window_handle is not None,
                )
            )

        tiled_window_count = 0
        if detected_window_handles:
            tiled_window_count = self._chrome_window_arranger.tile_windows(
                detected_window_handles,
                columns=columns,
                rows=rows,
            )

        return LaunchSavedProfilesGridResult(
            profiles=tuple(launched_profiles),
            grid_columns=columns,
            grid_rows=rows,
            tiled_window_count=tiled_window_count,
            omitted_profile_count=omitted_profile_count,
            library_persisted=library_persisted,
        )

    def _build_state(self, library: SavedProfileLibrary) -> ZaloProfileManagerState:
        discovered_executable = self._chrome_discovery.discover_executable()
        discovered_user_data_dir = self._chrome_discovery.discover_user_data_dir()
        return ZaloProfileManagerState(
            profiles=library.profiles,
            selected_profile_id=library.selected_profile_id,
            default_chrome_executable="" if discovered_executable is None else str(discovered_executable),
            default_profile_root="" if discovered_user_data_dir is None else str(discovered_user_data_dir),
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

    def _prepare_launch_config(
        self,
        profile: SavedChromeProfile,
        *,
        window_placement: WindowPlacement | None = None,
    ) -> ChromeLaunchConfig:
        chrome_executable = self._resolve_chrome_executable(profile.chrome_executable)
        profile_path = self._resolve_profile_path(profile.profile_path)
        self._validate_target_url(profile.target_url)

        return ChromeLaunchConfig(
            chrome_executable=chrome_executable,
            user_data_dir=profile_path.parent,
            profile_directory=profile_path.name,
            target_url=profile.target_url,
            new_window=True,
            window_placement=window_placement,
        )

    def _build_launch_result(self, config: ChromeLaunchConfig) -> ChromeLaunchResult:
        return ChromeLaunchResult(
            chrome_executable=config.chrome_executable,
            user_data_dir=config.user_data_dir,
            profile_directory=config.profile_directory,
            target_url=config.target_url,
            settings_persisted=True,
            window_placement=config.window_placement,
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

    def _resolve_profile_for_launch(
        self,
        profile_id: str | None,
        library: SavedProfileLibrary,
    ) -> SavedChromeProfile:
        resolved_profile_id = profile_id or library.selected_profile_id
        if resolved_profile_id is None:
            raise SavedProfileNotFoundError("No saved Chrome profile is selected.")
        return self._find_profile(resolved_profile_id, library)

    def _find_profile(self, profile_id: str, library: SavedProfileLibrary) -> SavedChromeProfile:
        for profile in library.profiles:
            if profile.id == profile_id:
                return profile
        raise SavedProfileNotFoundError(f"Saved Chrome profile not found: {profile_id}")

    def _resolve_profiles_for_grid_launch(
        self,
        profile_ids: Sequence[str],
        library: SavedProfileLibrary,
    ) -> tuple[SavedChromeProfile, ...]:
        if not profile_ids:
            raise SavedProfileNotFoundError("Select at least one saved Chrome profile.")

        unique_profile_ids: list[str] = []
        seen_profile_ids: set[str] = set()
        for profile_id in profile_ids:
            if profile_id in seen_profile_ids:
                continue
            unique_profile_ids.append(profile_id)
            seen_profile_ids.add(profile_id)

        return tuple(self._find_profile(profile_id, library) for profile_id in unique_profile_ids)

    def _normalize_name(self, value: str) -> str:
        profile_name = value.strip()
        if not profile_name:
            raise SavedProfileConflictError("Profile name is required.")
        return profile_name

    def _resolve_chrome_executable(self, value: str | None) -> Path:
        raw_value = (value or "").strip()
        if raw_value:
            chrome_executable = Path(raw_value).expanduser()
        else:
            discovered = self._chrome_discovery.discover_executable()
            if discovered is None:
                raise LauncherValidationError(
                    "Google Chrome could not be found automatically. Select the Chrome executable first."
                )
            chrome_executable = discovered

        if not chrome_executable.is_file():
            raise LauncherValidationError(f"Chrome executable not found: {chrome_executable}")
        if chrome_executable.name.lower() not in _SUPPORTED_CHROME_EXECUTABLE_NAMES:
            raise LauncherValidationError(
                f"Selected executable does not look like Google Chrome: {chrome_executable}"
            )
        return chrome_executable

    def _resolve_profile_path(self, value: str) -> Path:
        raw_value = value.strip()
        if not raw_value:
            raise LauncherValidationError("Chrome profile path is required.")

        profile_path = Path(raw_value).expanduser()
        if not profile_path.is_absolute():
            raise LauncherValidationError("Chrome profile path must be an absolute path.")
        profile_path = profile_path.resolve(strict=False)

        if not profile_path.is_dir():
            raise LauncherValidationError(f"Chrome profile path not found: {profile_path}")
        if profile_path.name.casefold() == "user data":
            raise LauncherValidationError(
                "Select the actual Chrome profile folder, for example '...\\User Data\\Profile 1', not the root 'User Data' folder."
            )
        if not self._looks_like_profile_directory(profile_path):
            raise LauncherValidationError(
                "Selected path does not look like a Chrome profile folder."
            )
        return profile_path

    def _looks_like_profile_directory(self, profile_path: Path) -> bool:
        if (profile_path / "Preferences").is_file():
            return True
        profile_name = profile_path.name
        if profile_name == "Default":
            return True
        if profile_name.startswith("Profile "):
            suffix = profile_name.removeprefix("Profile ").strip()
            return suffix.isdigit()
        return False

    def _validate_target_url(self, value: str) -> None:
        if value != DEFAULT_ZALO_URL:
            raise LauncherValidationError(
                f"Target URL is fixed to '{DEFAULT_ZALO_URL}' for the Zalo launcher."
            )

    def _ensure_unique_name(
        self,
        profile_name: str,
        current_profile_id: str | None,
        library: SavedProfileLibrary,
    ) -> None:
        target_name = profile_name.casefold()
        for profile in library.profiles:
            if profile.id == current_profile_id:
                continue
            if profile.name.casefold() == target_name:
                raise SavedProfileConflictError(
                    f"A saved profile named '{profile_name}' already exists."
                )

    def _ensure_unique_profile_path(
        self,
        profile_path: Path,
        current_profile_id: str | None,
        library: SavedProfileLibrary,
    ) -> None:
        normalized_path = os.path.normcase(str(profile_path))
        for profile in library.profiles:
            if profile.id == current_profile_id:
                continue
            other_path = os.path.normcase(str(Path(profile.profile_path).resolve(strict=False)))
            if other_path == normalized_path:
                raise SavedProfileConflictError(
                    "Each saved profile must point to a different Chrome profile path."
                )

    def _persist_selected_profile_id(
        self,
        selected_profile_id: str,
        library: SavedProfileLibrary,
    ) -> bool:
        if library.selected_profile_id == selected_profile_id:
            return True

        try:
            self._library_store.save(
                SavedProfileLibrary(
                    profiles=library.profiles,
                    selected_profile_id=selected_profile_id,
                )
            )
        except SettingsPersistenceError:
            return False
        return True
