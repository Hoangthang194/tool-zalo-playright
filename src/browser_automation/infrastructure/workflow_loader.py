from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from browser_automation.domain.entities import (
    AutomationStep,
    AutomationWorkflow,
    BrowserSettings,
    StepAction,
)
from browser_automation.domain.exceptions import WorkflowValidationError


class JsonWorkflowDefinitionLoader:
    def load(self, workflow_path: Path) -> AutomationWorkflow:
        path = Path(workflow_path)
        if not path.is_file():
            raise FileNotFoundError(f"Workflow file not found: {path}")

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise WorkflowValidationError(f"Workflow file is not valid JSON: {path}") from exc
        return self._map_payload_to_workflow(payload)

    def _map_payload_to_workflow(self, payload: dict[str, Any]) -> AutomationWorkflow:
        if not isinstance(payload, dict):
            raise WorkflowValidationError("Workflow root must be a JSON object.")

        browser_payload = payload.get("browser", {})
        steps_payload = payload.get("steps")

        if not isinstance(browser_payload, dict):
            raise WorkflowValidationError("Field 'browser' must be an object.")
        if not isinstance(steps_payload, list) or not steps_payload:
            raise WorkflowValidationError("Field 'steps' must be a non-empty array.")

        workflow_name = self._optional_str(payload.get("name"), "workflow.name") or "unnamed-workflow"
        browser_settings = self._map_browser_settings(browser_payload)
        steps = tuple(self._map_step(index, step) for index, step in enumerate(steps_payload, start=1))

        return AutomationWorkflow(
            name=workflow_name,
            browser=browser_settings,
            steps=steps,
        )

    def _map_browser_settings(self, payload: dict[str, Any]) -> BrowserSettings:
        viewport_payload = payload.get("viewport")
        if viewport_payload is None:
            viewport_payload = {}
        elif not isinstance(viewport_payload, dict):
            raise WorkflowValidationError("Field 'browser.viewport' must be an object.")

        engine = self._optional_str(payload.get("engine"), "browser.engine") or "chromium"
        channel = self._optional_str(payload.get("channel"), "browser.channel")
        slow_mo_ms = self._optional_int(payload.get("slow_mo_ms"), "browser.slow_mo_ms", default=0)
        timeout_ms = self._optional_int(payload.get("timeout_ms"), "browser.timeout_ms", default=30000)
        viewport_width = self._optional_int(viewport_payload.get("width"), "browser.viewport.width", default=1440)
        viewport_height = self._optional_int(
            viewport_payload.get("height"),
            "browser.viewport.height",
            default=900,
        )

        if channel and engine != "chromium":
            raise WorkflowValidationError("Field 'browser.channel' is only supported with engine 'chromium'.")
        if slow_mo_ms < 0:
            raise WorkflowValidationError("Field 'browser.slow_mo_ms' must be >= 0.")
        if timeout_ms < 0:
            raise WorkflowValidationError("Field 'browser.timeout_ms' must be >= 0.")
        if viewport_width <= 0 or viewport_height <= 0:
            raise WorkflowValidationError("Viewport width and height must be > 0.")

        return BrowserSettings(
            engine=engine,
            channel=channel,
            headless=self._optional_bool(payload.get("headless"), "browser.headless", default=False),
            slow_mo_ms=slow_mo_ms,
            timeout_ms=timeout_ms,
            base_url=self._optional_str(payload.get("base_url"), "browser.base_url"),
            viewport_width=viewport_width,
            viewport_height=viewport_height,
        )

    def _map_step(self, index: int, payload: Any) -> AutomationStep:
        if not isinstance(payload, dict):
            raise WorkflowValidationError(f"Step #{index} must be an object.")

        action_raw = self._required_str(payload.get("action"), f"steps[{index}].action")
        try:
            action = StepAction(action_raw)
        except ValueError as exc:
            raise WorkflowValidationError(f"Unsupported action '{action_raw}' at step #{index}.") from exc

        step = AutomationStep(
            name=self._optional_str(payload.get("name"), f"steps[{index}].name") or f"step-{index}",
            action=action,
            selector=self._optional_str(payload.get("selector"), f"steps[{index}].selector"),
            url=self._optional_str(payload.get("url"), f"steps[{index}].url"),
            text=self._optional_str(payload.get("text"), f"steps[{index}].text"),
            key=self._optional_str(payload.get("key"), f"steps[{index}].key"),
            milliseconds=self._optional_int(payload.get("milliseconds"), f"steps[{index}].milliseconds"),
            path=self._optional_str(payload.get("path"), f"steps[{index}].path"),
            full_page=self._optional_bool(payload.get("full_page"), f"steps[{index}].full_page", default=True),
            timeout_ms=self._optional_int(payload.get("timeout_ms"), f"steps[{index}].timeout_ms"),
        )
        self._validate_step(step, index)
        return step

    def _validate_step(self, step: AutomationStep, index: int) -> None:
        if step.action is StepAction.GOTO and not step.url:
            raise WorkflowValidationError(f"Step #{index} with action 'goto' requires 'url'.")
        if step.action in {StepAction.CLICK, StepAction.WAIT_FOR_SELECTOR} and not step.selector:
            raise WorkflowValidationError(
                f"Step #{index} with action '{step.action.value}' requires 'selector'."
            )
        if step.action is StepAction.FILL and (not step.selector or step.text is None):
            raise WorkflowValidationError(f"Step #{index} with action 'fill' requires 'selector' and 'text'.")
        if step.action is StepAction.PRESS and (not step.selector or not step.key):
            raise WorkflowValidationError(f"Step #{index} with action 'press' requires 'selector' and 'key'.")
        if step.action is StepAction.WAIT_FOR_TIMEOUT and step.milliseconds is None:
            raise WorkflowValidationError(
                f"Step #{index} with action 'wait_for_timeout' requires 'milliseconds'."
            )
        if step.action is StepAction.SCREENSHOT and not step.path:
            raise WorkflowValidationError(f"Step #{index} with action 'screenshot' requires 'path'.")
        if step.milliseconds is not None and step.milliseconds < 0:
            raise WorkflowValidationError(f"Step #{index} field 'milliseconds' must be >= 0.")
        if step.timeout_ms is not None and step.timeout_ms < 0:
            raise WorkflowValidationError(f"Step #{index} field 'timeout_ms' must be >= 0.")

    def _required_str(self, value: Any, field_name: str) -> str:
        parsed = self._optional_str(value, field_name)
        if parsed is None:
            raise WorkflowValidationError(f"Field '{field_name}' is required and must be a string.")
        return parsed

    def _optional_str(self, value: Any, field_name: str) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise WorkflowValidationError(f"Field '{field_name}' must be a string.")
        return value

    def _optional_bool(self, value: Any, field_name: str, default: bool | None = None) -> bool:
        if value is None:
            if default is None:
                raise WorkflowValidationError(f"Field '{field_name}' must be a boolean.")
            return default
        if not isinstance(value, bool):
            raise WorkflowValidationError(f"Field '{field_name}' must be a boolean.")
        return value

    def _optional_int(self, value: Any, field_name: str, default: int | None = None) -> int | None:
        if value is None:
            return default
        if isinstance(value, bool) or not isinstance(value, int):
            raise WorkflowValidationError(f"Field '{field_name}' must be an integer.")
        return value
