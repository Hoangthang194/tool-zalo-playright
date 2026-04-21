from __future__ import annotations

from typing import Protocol

from browser_automation.domain.zalo_launcher import ChromeLaunchConfig


class ChromeProcessLauncher(Protocol):
    def launch(self, config: ChromeLaunchConfig) -> None:
        """Launch Chrome with the supplied user profile configuration."""
