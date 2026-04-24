from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class MariaDbSettings:
    host: str
    port: int
    user: str
    password: str
    database: str
    charset: str = "utf8mb4"

    @property
    def label(self) -> str:
        return f"mariadb://{self.user}@{self.host}:{self.port}/{self.database}"


def load_mariadb_settings(environ: Mapping[str, str] | None = None) -> MariaDbSettings | None:
    environment = os.environ if environ is None else environ
    host = (environment.get("ZALO_DB_HOST") or "").strip()
    user = (environment.get("ZALO_DB_USER") or "").strip()
    database = (environment.get("ZALO_DB_NAME") or "").strip()
    if not all((host, user, database)):
        return None

    port_raw = (environment.get("ZALO_DB_PORT") or "3306").strip()
    password = environment.get("ZALO_DB_PASSWORD") or ""
    try:
        port = int(port_raw)
    except ValueError:
        port = 3306

    return MariaDbSettings(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
    )


def default_profile_selection_path(environ: Mapping[str, str] | None = None) -> Path:
    environment = os.environ if environ is None else environ
    app_data = environment.get("APPDATA")
    if app_data:
        return Path(app_data) / "browser-automation" / "zalo-profile-selection.json"
    return Path.home() / ".browser-automation" / "zalo-profile-selection.json"


class MariaDbConnectionFactory:
    def __init__(self, settings: MariaDbSettings) -> None:
        self._settings = settings

    @property
    def label(self) -> str:
        return self._settings.label

    def connect(self) -> Any:
        try:
            import pymysql
        except ImportError as exc:  # pragma: no cover - dependency error path
            raise RuntimeError(
                "PyMySQL is required for MariaDB persistence. Install dependencies with 'pip install -e .[dev]'."
            ) from exc

        return pymysql.connect(
            host=self._settings.host,
            port=self._settings.port,
            user=self._settings.user,
            password=self._settings.password,
            database=self._settings.database,
            charset=self._settings.charset,
            autocommit=False,
            cursorclass=pymysql.cursors.DictCursor,
        )

