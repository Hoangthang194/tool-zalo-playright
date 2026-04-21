from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from browser_automation.domain.exceptions import SettingsPersistenceError
from browser_automation.domain.zalo_launcher import LauncherSettings


def default_launcher_settings_path(environ: Mapping[str, str] | None = None) -> Path:
    environment = os.environ if environ is None else environ
    app_data = environment.get("APPDATA")
    if app_data:
        return Path(app_data) / "browser-automation" / "zalo-launcher.json"
    return Path.home() / ".browser-automation" / "zalo-launcher.json"


class JsonLauncherSettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or default_launcher_settings_path()

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> LauncherSettings:
        if not self._path.is_file():
            return LauncherSettings()

        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return LauncherSettings()

        if not isinstance(payload, dict):
            return LauncherSettings()

        return LauncherSettings(
            chrome_executable=self._optional_str(payload.get("chrome_executable")),
            user_data_dir=self._optional_str(payload.get("user_data_dir")),
            profile_directory=self._optional_str(payload.get("profile_directory")),
        )

    def save(self, settings: LauncherSettings) -> None:
        payload = {
            "chrome_executable": settings.chrome_executable,
            "user_data_dir": settings.user_data_dir,
            "profile_directory": settings.profile_directory,
        }

        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError as exc:
            raise SettingsPersistenceError(
                f"Could not persist launcher settings to '{self._path}'."
            ) from exc

    def _optional_str(self, value: Any) -> str | None:
        if value is None or not isinstance(value, str):
            return None
        return value
