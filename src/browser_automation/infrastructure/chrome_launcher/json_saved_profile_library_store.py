from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from browser_automation.domain.exceptions import SettingsPersistenceError
from browser_automation.domain.zalo_launcher import (
    DEFAULT_ZALO_URL,
    LauncherSettings,
    SavedChromeProfile,
    SavedProfileLibrary,
)
from browser_automation.infrastructure.chrome_launcher.json_launcher_settings_store import (
    JsonLauncherSettingsStore,
)

_MIGRATED_PROFILE_ID = "migrated-default-profile"


def default_saved_profile_library_path(environ: Mapping[str, str] | None = None) -> Path:
    environment = os.environ if environ is None else environ
    app_data = environment.get("APPDATA")
    if app_data:
        return Path(app_data) / "browser-automation" / "zalo-profiles.json"
    return Path.home() / ".browser-automation" / "zalo-profiles.json"


class JsonSavedProfileLibraryStore:
    def __init__(
        self,
        path: Path | None = None,
        legacy_settings_store: JsonLauncherSettingsStore | None = None,
    ) -> None:
        self._path = path or default_saved_profile_library_path()
        self._legacy_settings_store = legacy_settings_store or JsonLauncherSettingsStore()

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> SavedProfileLibrary:
        if self._path.is_file():
            return self._load_from_library_file()
        return self._load_from_legacy_settings()

    def save(self, library: SavedProfileLibrary) -> None:
        payload = {
            "selected_profile_id": library.selected_profile_id,
            "profiles": [
                {
                    "id": profile.id,
                    "name": profile.name,
                    "chrome_executable": profile.chrome_executable,
                    "profile_path": profile.profile_path,
                    "target_url": profile.target_url,
                }
                for profile in library.profiles
            ],
        }

        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError as exc:
            raise SettingsPersistenceError(
                f"Could not persist saved profile library to '{self._path}'."
            ) from exc

    def _load_from_library_file(self) -> SavedProfileLibrary:
        try:
            payload = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return SavedProfileLibrary()

        if not isinstance(payload, dict):
            return SavedProfileLibrary()

        profiles_payload = payload.get("profiles")
        if not isinstance(profiles_payload, list):
            return SavedProfileLibrary()

        profiles: list[SavedChromeProfile] = []
        seen_ids: set[str] = set()
        for profile_payload in profiles_payload:
            profile = self._map_profile(profile_payload)
            if profile is None or profile.id in seen_ids:
                continue
            profiles.append(profile)
            seen_ids.add(profile.id)

        selected_profile_id = self._optional_str(payload.get("selected_profile_id"))
        if selected_profile_id not in seen_ids:
            selected_profile_id = profiles[0].id if profiles else None

        return SavedProfileLibrary(
            profiles=tuple(profiles),
            selected_profile_id=selected_profile_id,
        )

    def _load_from_legacy_settings(self) -> SavedProfileLibrary:
        settings = self._legacy_settings_store.load()
        if not self._is_complete_legacy_settings(settings):
            return SavedProfileLibrary()

        profile_path = Path(settings.user_data_dir) / settings.profile_directory
        migrated_profile = SavedChromeProfile(
            id=_MIGRATED_PROFILE_ID,
            name=self._legacy_profile_name(settings),
            chrome_executable=settings.chrome_executable,
            profile_path=str(profile_path),
            target_url=DEFAULT_ZALO_URL,
        )
        return SavedProfileLibrary(
            profiles=(migrated_profile,),
            selected_profile_id=migrated_profile.id,
        )

    def _map_profile(self, payload: Any) -> SavedChromeProfile | None:
        if not isinstance(payload, dict):
            return None

        profile_id = self._optional_str(payload.get("id"))
        name = self._optional_str(payload.get("name"))
        chrome_executable = self._optional_str(payload.get("chrome_executable"))
        profile_path = self._optional_str(payload.get("profile_path"))
        target_url = self._optional_str(payload.get("target_url")) or DEFAULT_ZALO_URL

        if not all((profile_id, name, chrome_executable, profile_path)):
            return None

        return SavedChromeProfile(
            id=profile_id,
            name=name,
            chrome_executable=chrome_executable,
            profile_path=profile_path,
            target_url=target_url,
        )

    def _is_complete_legacy_settings(self, settings: LauncherSettings) -> bool:
        return bool(
            settings.chrome_executable
            and settings.user_data_dir
            and settings.profile_directory
        )

    def _legacy_profile_name(self, settings: LauncherSettings) -> str:
        profile_directory = settings.profile_directory or "Default"
        return f"Imported {profile_directory}"

    def _optional_str(self, value: Any) -> str | None:
        if value is None or not isinstance(value, str):
            return None
        stripped = value.strip()
        return stripped or None
