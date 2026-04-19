from __future__ import annotations

from pathlib import Path
from typing import Protocol

from browser_automation.domain.entities import AutomationWorkflow


class WorkflowDefinitionLoader(Protocol):
    def load(self, workflow_path: Path) -> AutomationWorkflow:
        """Load a workflow definition from a file."""

