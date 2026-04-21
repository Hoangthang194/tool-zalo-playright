from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from browser_automation.application.ports.chrome_installation_discovery import (
    ChromeInstallationDiscovery,
)
from browser_automation.application.ports.chrome_process_launcher import (
    ChromeProcessLauncher,
)
from browser_automation.application.ports.launcher_settings_store import (
    LauncherSettingsStore,
)
from browser_automation.domain.exceptions import (
    LauncherValidationError,
    SettingsPersistenceError,
)
from browser_automation.domain.zalo_launcher import (
    DEFAULT_ZALO_URL,
    ChromeLaunchConfig,
    ChromeLaunchResult,
    LauncherSettings,
)

_SUPPORTED_CHROME_EXECUTABLE_NAMES = {
    "chrome.exe",
    "chrome",
    "google-chrome",
    "google-chrome-stable",
}


@dataclass(frozen=True, slots=True)
class LaunchZaloChatRequest:
    user_data_dir: str
    profile_directory: str
    chrome_executable: str | None = None
    target_url: str = DEFAULT_ZALO_URL


@dataclass(frozen=True, slots=True)
class ZaloLauncherFormState:
    chrome_executable: str
    user_data_dir: str
    profile_directory: str
    target_url: str = DEFAULT_ZALO_URL


class LaunchZaloChatUseCase:
    def __init__(
        self,
        chrome_discovery: ChromeInstallationDiscovery,
        chrome_launcher: ChromeProcessLauncher,
        settings_store: LauncherSettingsStore,
    ) -> None:
        self._chrome_discovery = chrome_discovery
        self._chrome_launcher = chrome_launcher
        self._settings_store = settings_store

    def load_form_state(self) -> ZaloLauncherFormState:
        settings = self._settings_store.load()
        discovered_executable = self._chrome_discovery.discover_executable()
        discovered_user_data_dir = self._chrome_discovery.discover_user_data_dir()

        return ZaloLauncherFormState(
            chrome_executable=settings.chrome_executable or self._stringify_path(discovered_executable),
            user_data_dir=settings.user_data_dir or self._stringify_path(discovered_user_data_dir),
            profile_directory=settings.profile_directory or "Default",
        )

    def prepare_config(self, request: LaunchZaloChatRequest) -> ChromeLaunchConfig:
        chrome_executable = self._resolve_chrome_executable(request.chrome_executable)
        user_data_dir = self._resolve_user_data_dir(request.user_data_dir)
        profile_directory = self._normalize_profile_directory(request.profile_directory)

        if request.target_url != DEFAULT_ZALO_URL:
            raise LauncherValidationError(
                f"Target URL is fixed to '{DEFAULT_ZALO_URL}' for the Zalo launcher."
            )

        self._validate_paths(chrome_executable, user_data_dir, profile_directory)

        return ChromeLaunchConfig(
            chrome_executable=chrome_executable,
            user_data_dir=user_data_dir,
            profile_directory=profile_directory,
            target_url=request.target_url,
        )

    def execute(self, request: LaunchZaloChatRequest) -> ChromeLaunchResult:
        config = self.prepare_config(request)
        self._chrome_launcher.launch(config)

        settings_persisted = True
        try:
            self._settings_store.save(
                LauncherSettings(
                    chrome_executable=str(config.chrome_executable),
                    user_data_dir=str(config.user_data_dir),
                    profile_directory=config.profile_directory,
                )
            )
        except SettingsPersistenceError:
            settings_persisted = False

        return ChromeLaunchResult(
            chrome_executable=config.chrome_executable,
            user_data_dir=config.user_data_dir,
            profile_directory=config.profile_directory,
            target_url=config.target_url,
            settings_persisted=settings_persisted,
        )

    def _resolve_chrome_executable(self, value: str | None) -> Path:
        raw_value = (value or "").strip()
        if raw_value:
            return Path(raw_value).expanduser()

        discovered = self._chrome_discovery.discover_executable()
        if discovered is None:
            raise LauncherValidationError(
                "Google Chrome could not be found automatically. Select the Chrome executable first."
            )
        return discovered

    def _resolve_user_data_dir(self, value: str) -> Path:
        raw_value = value.strip()
        if raw_value:
            return Path(raw_value).expanduser()

        discovered = self._chrome_discovery.discover_user_data_dir()
        if discovered is None:
            raise LauncherValidationError(
                "Chrome user data directory is required. Select the folder that contains 'Default' or 'Profile 1'."
            )
        return discovered

    def _normalize_profile_directory(self, value: str) -> str:
        profile_directory = value.strip()
        if not profile_directory:
            raise LauncherValidationError("Chrome profile directory is required.")

        path_like_value = Path(profile_directory)
        if profile_directory in {".", ".."} or path_like_value.name != profile_directory:
            raise LauncherValidationError(
                "Chrome profile directory must be a directory name such as 'Default' or 'Profile 1'."
            )
        return profile_directory

    def _validate_paths(
        self,
        chrome_executable: Path,
        user_data_dir: Path,
        profile_directory: str,
    ) -> None:
        if not chrome_executable.is_file():
            raise LauncherValidationError(f"Chrome executable not found: {chrome_executable}")
        if chrome_executable.name.lower() not in _SUPPORTED_CHROME_EXECUTABLE_NAMES:
            raise LauncherValidationError(
                f"Selected executable does not look like Google Chrome: {chrome_executable}"
            )
        if not user_data_dir.is_dir():
            raise LauncherValidationError(f"Chrome user data directory not found: {user_data_dir}")

        profile_path = user_data_dir / profile_directory
        if not profile_path.is_dir():
            raise LauncherValidationError(f"Chrome profile directory not found: {profile_path}")

    def _stringify_path(self, value: Path | None) -> str:
        return "" if value is None else str(value)
