from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Sequence

from browser_automation.application.use_cases.run_workflow import (
    RunAutomationWorkflowUseCase,
)
from browser_automation.domain.exceptions import BrowserAutomationError, WorkflowValidationError
from browser_automation.infrastructure.playwright_adapter.playwright_browser_gateway import (
    PlaywrightBrowserAutomationGateway,
)
from browser_automation.infrastructure.workflow_loader import JsonWorkflowDefinitionLoader

LOGGER = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="browser-automation",
        description="Run browser automation workflows with Playwright.",
    )
    parser.add_argument("workflow", help="Path to workflow JSON file.")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s %(message)s",
    )

    use_case = RunAutomationWorkflowUseCase(
        workflow_loader=JsonWorkflowDefinitionLoader(),
        browser_gateway=PlaywrightBrowserAutomationGateway(),
    )

    try:
        result = use_case.execute(Path(args.workflow))
    except (BrowserAutomationError, WorkflowValidationError, FileNotFoundError, OSError) as exc:
        LOGGER.error("%s", exc)
        return 1

    LOGGER.info(
        "Workflow '%s' completed with %d step(s) on channel '%s'.",
        result.workflow_name,
        result.steps_executed,
        result.browser_channel or "default",
    )
    return 0

