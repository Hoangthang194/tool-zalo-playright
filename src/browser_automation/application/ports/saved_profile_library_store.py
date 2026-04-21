from __future__ import annotations

from typing import Protocol

from browser_automation.domain.zalo_launcher import SavedProfileLibrary


class SavedProfileLibraryStore(Protocol):
    def load(self) -> SavedProfileLibrary:
        """Load the saved Zalo Chrome profile library."""

    def save(self, library: SavedProfileLibrary) -> None:
        """Persist the saved Zalo Chrome profile library."""
