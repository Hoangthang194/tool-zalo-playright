from __future__ import annotations

from collections.abc import Collection, Sequence
from typing import Protocol

from browser_automation.domain.zalo_launcher import WindowPlacement


class ChromeWindowArranger(Protocol):
    def snapshot_window_handles(self) -> frozenset[int]:
        """Return the currently visible top-level Chrome window handles."""

    def calculate_grid_placements(
        self,
        *,
        count: int,
        columns: int,
        rows: int,
    ) -> tuple[WindowPlacement, ...]:
        """Return planned window placements for a grid on the primary monitor."""

    def wait_for_new_window(
        self,
        existing_window_handles: Collection[int],
        timeout_seconds: float,
    ) -> int | None:
        """Wait for a newly visible Chrome window not present in the supplied snapshot."""

    def apply_window_placement(
        self,
        window_handle: int,
        placement: WindowPlacement,
    ) -> None:
        """Move a single Chrome window into the supplied placement."""

    def tile_windows(
        self,
        window_handles: Sequence[int],
        *,
        columns: int,
        rows: int,
    ) -> int:
        """Arrange the supplied Chrome windows into a grid and return the number tiled."""
