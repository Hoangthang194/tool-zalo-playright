from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from browser_automation.domain.exceptions import SettingsPersistenceError
from browser_automation.domain.zalo_launcher import DEFAULT_ZALO_URL, SavedChromeProfile, SavedProfileLibrary
from browser_automation.infrastructure.persistence.mariadb_connection import (
    MariaDbConnectionFactory,
    default_profile_selection_path,
)


class MariaDbSavedProfileLibraryStore:
    def __init__(
        self,
        connection_factory: MariaDbConnectionFactory,
        *,
        selection_path: Path | None = None,
    ) -> None:
        self._connection_factory = connection_factory
        self._selection_path = selection_path or default_profile_selection_path()

    @property
    def path(self) -> str:
        return self._connection_factory.label

    def load(self) -> SavedProfileLibrary:
        try:
            with self._connection_factory.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT id, name, chrome_executable, profile_path, target_url
                        FROM profiles
                        ORDER BY created_at ASC, name ASC
                        """
                    )
                    rows = cursor.fetchall()
        except Exception as exc:  # noqa: BLE001
            raise SettingsPersistenceError(
                f"Could not load saved Chrome profiles from '{self.path}'."
            ) from exc

        profiles = tuple(self._map_profile(row) for row in rows)
        selected_profile_id = self._load_selected_profile_id()
        profile_ids = {profile.id for profile in profiles}
        if selected_profile_id not in profile_ids:
            selected_profile_id = profiles[0].id if profiles else None

        return SavedProfileLibrary(
            profiles=profiles,
            selected_profile_id=selected_profile_id,
        )

    def save(self, library: SavedProfileLibrary) -> None:
        try:
            with self._connection_factory.connect() as connection:
                with connection.cursor() as cursor:
                    profile_ids = [profile.id for profile in library.profiles]
                    if profile_ids:
                        placeholders = ", ".join(["%s"] * len(profile_ids))
                        cursor.execute(
                            f"DELETE FROM profiles WHERE id NOT IN ({placeholders})",
                            profile_ids,
                        )
                    else:
                        cursor.execute("DELETE FROM profiles")

                    for profile in library.profiles:
                        cursor.execute(
                            """
                            INSERT INTO profiles (id, name, chrome_executable, profile_path, target_url)
                            VALUES (%s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                name = VALUES(name),
                                chrome_executable = VALUES(chrome_executable),
                                profile_path = VALUES(profile_path),
                                target_url = VALUES(target_url)
                            """,
                            (
                                profile.id,
                                profile.name,
                                profile.chrome_executable,
                                profile.profile_path,
                                profile.target_url,
                            ),
                        )
                connection.commit()
        except Exception as exc:  # noqa: BLE001
            raise SettingsPersistenceError(
                f"Could not persist saved Chrome profiles to '{self.path}'."
            ) from exc

        self._save_selected_profile_id(library.selected_profile_id)

    def _map_profile(self, payload: dict[str, Any]) -> SavedChromeProfile:
        return SavedChromeProfile(
            id=str(payload["id"]),
            name=str(payload["name"]),
            chrome_executable=str(payload["chrome_executable"]),
            profile_path=str(payload["profile_path"]),
            target_url=str(payload.get("target_url") or DEFAULT_ZALO_URL),
        )

    def _load_selected_profile_id(self) -> str | None:
        if not self._selection_path.is_file():
            return None
        try:
            payload = json.loads(self._selection_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        selected_profile_id = payload.get("selected_profile_id")
        if not isinstance(selected_profile_id, str):
            return None
        return selected_profile_id.strip() or None

    def _save_selected_profile_id(self, selected_profile_id: str | None) -> None:
        try:
            self._selection_path.parent.mkdir(parents=True, exist_ok=True)
            self._selection_path.write_text(
                json.dumps({"selected_profile_id": selected_profile_id}, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise SettingsPersistenceError(
                f"Could not persist selected saved Chrome profile to '{self._selection_path}'."
            ) from exc
