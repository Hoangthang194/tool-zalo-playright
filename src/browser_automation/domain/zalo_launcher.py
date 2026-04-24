from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

DEFAULT_ZALO_URL = "https://chat.zalo.me"


@dataclass(frozen=True, slots=True)
class WindowPlacement:
    left: int
    top: int
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class ChromeLaunchConfig:
    chrome_executable: Path
    user_data_dir: Path
    profile_directory: str | None = None
    target_url: str = DEFAULT_ZALO_URL
    new_window: bool = True
    headless: bool = False
    proxy_server: str | None = None
    remote_debugging_port: int | None = None
    window_placement: WindowPlacement | None = None


@dataclass(frozen=True, slots=True)
class ChromeLaunchResult:
    chrome_executable: Path
    user_data_dir: Path
    profile_directory: str | None
    target_url: str
    settings_persisted: bool = True
    headless: bool = False
    proxy_server: str | None = None
    remote_debugging_port: int | None = None
    window_placement: WindowPlacement | None = None


@dataclass(frozen=True, slots=True)
class LauncherSettings:
    chrome_executable: str | None = None
    user_data_dir: str | None = None
    profile_directory: str | None = None


@dataclass(frozen=True, slots=True)
class SavedChromeProfile:
    id: str
    name: str
    chrome_executable: str
    profile_path: str
    target_url: str = DEFAULT_ZALO_URL


@dataclass(frozen=True, slots=True)
class SavedProfileLibrary:
    profiles: tuple[SavedChromeProfile, ...] = ()
    selected_profile_id: str | None = None
