from __future__ import annotations

from pathlib import Path
from typing import Protocol


class ChromeInstallationDiscovery(Protocol):
    def discover_executable(self) -> Path | None:
        """Return the path to an installed Google Chrome executable when available."""

    def discover_user_data_dir(self) -> Path | None:
        """Return the default Chrome user data directory when available."""
