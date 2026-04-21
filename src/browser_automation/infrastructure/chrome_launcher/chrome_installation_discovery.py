from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Mapping


class DefaultChromeInstallationDiscovery:
    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        self._environ = os.environ if environ is None else environ

    def discover_executable(self) -> Path | None:
        for candidate in self._candidate_executables():
            if candidate.is_file():
                return candidate
        return None

    def discover_user_data_dir(self) -> Path | None:
        for candidate in self._candidate_user_data_dirs():
            if candidate.is_dir():
                return candidate
        return None

    def _candidate_executables(self) -> list[Path]:
        candidates: list[Path] = []

        if sys.platform.startswith("win"):
            for env_name in ("LOCALAPPDATA", "PROGRAMFILES", "PROGRAMFILES(X86)"):
                base_path = self._environ.get(env_name)
                if base_path:
                    candidates.append(Path(base_path) / "Google" / "Chrome" / "Application" / "chrome.exe")
        elif sys.platform == "darwin":
            candidates.append(
                Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
            )
        else:
            home = Path.home()
            candidates.append(home / ".local" / "bin" / "google-chrome")

        for binary_name in ("chrome.exe", "chrome", "google-chrome", "google-chrome-stable"):
            discovered = shutil.which(binary_name)
            if discovered:
                candidates.append(Path(discovered))

        return candidates

    def _candidate_user_data_dirs(self) -> list[Path]:
        candidates: list[Path] = []

        if sys.platform.startswith("win"):
            local_app_data = self._environ.get("LOCALAPPDATA")
            if local_app_data:
                candidates.append(Path(local_app_data) / "Google" / "Chrome" / "User Data")
        elif sys.platform == "darwin":
            candidates.append(Path.home() / "Library" / "Application Support" / "Google" / "Chrome")
        else:
            candidates.append(Path.home() / ".config" / "google-chrome")

        return candidates
