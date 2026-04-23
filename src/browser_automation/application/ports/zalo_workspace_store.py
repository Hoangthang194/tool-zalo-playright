from __future__ import annotations

from typing import Protocol

from browser_automation.domain.zalo_workspace import ZaloWorkspaceLibrary


class ZaloWorkspaceStore(Protocol):
    def load(self) -> ZaloWorkspaceLibrary:
        """Load the saved Zalo account workspace."""

    def save(self, library: ZaloWorkspaceLibrary) -> None:
        """Persist the saved Zalo account workspace."""
