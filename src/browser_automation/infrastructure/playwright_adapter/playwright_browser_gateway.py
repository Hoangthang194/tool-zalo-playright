from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from browser_automation.domain.entities import AutomationStep, AutomationWorkflow, StepAction
from browser_automation.domain.exceptions import (
    BrowserAutomationError,
    UnsupportedBrowserEngineError,
    UnsupportedStepError,
)

LOGGER = logging.getLogger(__name__)


class PlaywrightBrowserAutomationGateway:
    def run(self, workflow: AutomationWorkflow) -> None:
        try:
            from playwright.sync_api import Error as PlaywrightError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise BrowserAutomationError(
                "Playwright is not installed. Run 'python -m pip install -e \".[dev]\"' or 'pip install playwright'."
            ) from exc

        try:
            with sync_playwright() as playwright:
                browser_type = self._resolve_browser_type(playwright, workflow.browser.engine)
                launch_options: dict[str, Any] = {
                    "headless": workflow.browser.headless,
                    "slow_mo": workflow.browser.slow_mo_ms,
                }
                if workflow.browser.channel:
                    launch_options["channel"] = workflow.browser.channel

                browser = browser_type.launch(**launch_options)
                context = browser.new_context(
                    base_url=workflow.browser.base_url,
                    viewport={
                        "width": workflow.browser.viewport_width,
                        "height": workflow.browser.viewport_height,
                    },
                )
                context.set_default_timeout(workflow.browser.timeout_ms)
                page = context.new_page()

                for step in workflow.steps:
                    LOGGER.info("Running step '%s' (%s)", step.name, step.action.value)
                    self._execute_step(page, step)

                context.close()
                browser.close()
        except PlaywrightError as exc:
            raise BrowserAutomationError(f"Playwright execution failed: {exc}") from exc

    def _resolve_browser_type(self, playwright: Any, engine: str) -> Any:
        browser_types: dict[str, Any] = {
            "chromium": playwright.chromium,
            "firefox": playwright.firefox,
            "webkit": playwright.webkit,
        }

        if engine not in browser_types:
            raise UnsupportedBrowserEngineError(
                f"Unsupported browser engine '{engine}'. Expected one of: chromium, firefox, webkit."
            )
        return browser_types[engine]

    def _execute_step(self, page: Any, step: AutomationStep) -> None:
        if step.action is StepAction.GOTO:
            page.goto(step.url, wait_until="domcontentloaded")
            return

        if step.action is StepAction.CLICK:
            page.locator(step.selector).click(timeout=step.timeout_ms)
            return

        if step.action is StepAction.FILL:
            page.locator(step.selector).fill(step.text, timeout=step.timeout_ms)
            return

        if step.action is StepAction.PRESS:
            page.locator(step.selector).press(step.key, timeout=step.timeout_ms)
            return

        if step.action is StepAction.WAIT_FOR_SELECTOR:
            page.locator(step.selector).wait_for(timeout=step.timeout_ms)
            return

        if step.action is StepAction.WAIT_FOR_TIMEOUT:
            page.wait_for_timeout(step.milliseconds)
            return

        if step.action is StepAction.SCREENSHOT:
            output_path = Path(step.path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(output_path), full_page=step.full_page)
            return

        raise UnsupportedStepError(f"Unsupported step action: {step.action}")
