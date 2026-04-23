from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from browser_automation.domain.zalo_workspace import SavedZaloClickTarget


@dataclass(frozen=True, slots=True)
class ClickAutomationResult:
    clicked_target_names: tuple[str, ...]


class ZaloClickAutomationRunner(Protocol):
    def run(
        self,
        *,
        remote_debugging_port: int,
        target_url: str,
        click_targets: tuple[SavedZaloClickTarget, ...],
        timeout_seconds: float,
    ) -> ClickAutomationResult:
        """Execute saved click targets against the launched Zalo page."""
