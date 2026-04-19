from pathlib import Path

from browser_automation.application.use_cases.run_workflow import (
    RunAutomationWorkflowUseCase,
)
from browser_automation.domain.entities import (
    AutomationStep,
    AutomationWorkflow,
    BrowserSettings,
    StepAction,
)


class FakeWorkflowLoader:
    def __init__(self, workflow: AutomationWorkflow) -> None:
        self.workflow = workflow
        self.loaded_path: Path | None = None

    def load(self, workflow_path: Path) -> AutomationWorkflow:
        self.loaded_path = workflow_path
        return self.workflow


class FakeBrowserGateway:
    def __init__(self) -> None:
        self.executed_workflow: AutomationWorkflow | None = None

    def run(self, workflow: AutomationWorkflow) -> None:
        self.executed_workflow = workflow


def test_use_case_loads_and_executes_workflow() -> None:
    workflow = AutomationWorkflow(
        name="demo",
        browser=BrowserSettings(channel="chrome"),
        steps=(
            AutomationStep(
                name="open",
                action=StepAction.GOTO,
                url="https://example.com",
            ),
        ),
    )
    loader = FakeWorkflowLoader(workflow)
    gateway = FakeBrowserGateway()
    use_case = RunAutomationWorkflowUseCase(loader, gateway)

    result = use_case.execute(Path("examples/sample_workflow.json"))

    assert loader.loaded_path == Path("examples/sample_workflow.json")
    assert gateway.executed_workflow == workflow
    assert result.workflow_name == "demo"
    assert result.steps_executed == 1
    assert result.browser_channel == "chrome"

