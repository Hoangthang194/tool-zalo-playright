from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from browser_automation.application.ports.browser_automation_gateway import (
    BrowserAutomationGateway,
)
from browser_automation.application.ports.workflow_definition_loader import (
    WorkflowDefinitionLoader,
)


@dataclass(frozen=True, slots=True)
class WorkflowExecutionResult:
    workflow_name: str
    steps_executed: int
    browser_channel: str | None


class RunAutomationWorkflowUseCase:
    def __init__(
        self,
        workflow_loader: WorkflowDefinitionLoader,
        browser_gateway: BrowserAutomationGateway,
    ) -> None:
        self._workflow_loader = workflow_loader
        self._browser_gateway = browser_gateway

    def execute(self, workflow_path: Path) -> WorkflowExecutionResult:
        workflow = self._workflow_loader.load(workflow_path)
        self._browser_gateway.run(workflow)
        return WorkflowExecutionResult(
            workflow_name=workflow.name,
            steps_executed=len(workflow.steps),
            browser_channel=workflow.browser.channel,
        )

