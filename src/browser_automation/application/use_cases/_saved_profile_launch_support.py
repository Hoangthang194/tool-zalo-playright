from __future__ import annotations

from pathlib import Path

from browser_automation.application.ports.chrome_installation_discovery import (
    ChromeInstallationDiscovery,
)
from browser_automation.application.use_cases._proxy_support import (
    normalize_optional_proxy_server,
)
from browser_automation.domain.exceptions import LauncherValidationError
from browser_automation.domain.zalo_launcher import (
    DEFAULT_ZALO_URL,
    ChromeLaunchConfig,
    SavedChromeProfile,
    WindowPlacement,
)

SUPPORTED_CHROME_EXECUTABLE_NAMES = {
    "chrome.exe",
    "chrome",
    "google-chrome",
    "google-chrome-stable",
}


class SavedProfileLaunchSupport:
    def __init__(self, chrome_discovery: ChromeInstallationDiscovery) -> None:
        self._chrome_discovery = chrome_discovery

    def prepare_launch_config(
        self,
        profile: SavedChromeProfile,
        *,
        window_placement: WindowPlacement | None = None,
        proxy_server: str | None = None,
        remote_debugging_port: int | None = None,
        headless: bool = False,
    ) -> ChromeLaunchConfig:
        chrome_executable = self.resolve_chrome_executable(profile.chrome_executable)
        profile_path = self.resolve_profile_path(profile.profile_path)
        self.validate_target_url(profile.target_url)

        return ChromeLaunchConfig(
            chrome_executable=chrome_executable,
            user_data_dir=profile_path.parent,
            profile_directory=profile_path.name,
            target_url=profile.target_url,
            new_window=not headless,
            headless=headless,
            proxy_server=self.normalize_proxy_server(proxy_server),
            remote_debugging_port=remote_debugging_port,
            window_placement=None if headless else window_placement,
        )

    def resolve_chrome_executable(self, value: str | None) -> Path:
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
        if chrome_executable.name.lower() not in SUPPORTED_CHROME_EXECUTABLE_NAMES:
            raise LauncherValidationError(
                f"Selected executable does not look like Google Chrome: {chrome_executable}"
            )
        return chrome_executable

    def resolve_profile_path(self, value: str) -> Path:
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
        if not self.looks_like_profile_directory(profile_path):
            raise LauncherValidationError(
                "Selected path does not look like a Chrome profile folder."
            )
        return profile_path

    def validate_target_url(self, value: str) -> None:
        if value != DEFAULT_ZALO_URL:
            raise LauncherValidationError(
                f"Target URL is fixed to '{DEFAULT_ZALO_URL}' for the Zalo launcher."
            )

    def normalize_proxy_server(self, value: str | None) -> str | None:
        return normalize_optional_proxy_server(value)

    def looks_like_profile_directory(self, profile_path: Path) -> bool:
        if (profile_path / "Preferences").is_file():
            return True
        if self.is_empty_directory(profile_path):
            return True
        profile_name = profile_path.name
        if profile_name == "Default":
            return True
        if profile_name.startswith("Profile "):
            suffix = profile_name.removeprefix("Profile ").strip()
            return suffix.isdigit()
        return False

    def is_empty_directory(self, profile_path: Path) -> bool:
        try:
            next(profile_path.iterdir())
        except StopIteration:
            return True
        except OSError:
            return False
        return False
