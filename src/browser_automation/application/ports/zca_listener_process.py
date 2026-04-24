from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from browser_automation.domain.zalo_live_events import ZaloLiveEventLogEntry


class ZcaListenerProcess(Protocol):
    def start(
        self,
        *,
        credentials_file_path: str,
        on_event: Callable[[ZaloLiveEventLogEntry], None],
    ) -> None:
        """Start one managed ZCA listener subprocess."""

    def stop(self) -> None:
        """Stop the current listener subprocess if it is running."""

    def is_running(self) -> bool:
        """Return True while the listener subprocess is active."""
