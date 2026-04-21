from __future__ import annotations

from typing import Protocol

from browser_automation.domain.zalo_launcher import LauncherSettings


class LauncherSettingsStore(Protocol):
    def load(self) -> LauncherSettings:
        """Load the most recently used launcher configuration."""

    def save(self, settings: LauncherSettings) -> None:
        """Persist the most recently used launcher configuration."""
