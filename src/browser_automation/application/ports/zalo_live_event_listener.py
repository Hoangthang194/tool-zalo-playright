from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from browser_automation.domain.zalo_live_events import ZaloLiveEventLogEntry


class ZaloLiveEventListener(Protocol):
    def start(
        self,
        *,
        remote_debugging_port: int,
        target_url: str,
        on_event: Callable[[ZaloLiveEventLogEntry], None],
        timeout_seconds: float,
    ) -> None:
        """Start streaming live Zalo events for one attached browser page."""

    def stop(self) -> None:
        """Stop the current live event stream if it is running."""

    def is_running(self) -> bool:
        """Return True while the live event listener is attached."""
