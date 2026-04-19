import json

from browser_automation.domain.entities import StepAction
from browser_automation.infrastructure.workflow_loader import JsonWorkflowDefinitionLoader


def test_json_loader_maps_payload_to_workflow(tmp_path) -> None:
    workflow_path = tmp_path / "workflow.json"
    workflow_path.write_text(
        json.dumps(
            {
                "name": "demo",
                "browser": {
                    "engine": "chromium",
                    "channel": "chrome",
                    "headless": False,
                    "timeout_ms": 10000,
                    "viewport": {
                        "width": 1280,
                        "height": 720,
                    },
                },
                "steps": [
                    {
                        "name": "open home",
                        "action": "goto",
                        "url": "https://example.com",
                    },
                    {
                        "name": "take shot",
                        "action": "screenshot",
                        "path": "artifacts/example.png",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    workflow = JsonWorkflowDefinitionLoader().load(workflow_path)

    assert workflow.name == "demo"
    assert workflow.browser.channel == "chrome"
    assert workflow.browser.viewport_width == 1280
    assert workflow.steps[0].action is StepAction.GOTO
    assert workflow.steps[1].action is StepAction.SCREENSHOT
