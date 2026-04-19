from __future__ import annotations

from typing import Protocol

from browser_automation.domain.entities import AutomationWorkflow


class BrowserAutomationGateway(Protocol):
    def run(self, workflow: AutomationWorkflow) -> None:
        """Execute the workflow against a real browser."""

