from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class StepAction(StrEnum):
    GOTO = "goto"
    CLICK = "click"
    FILL = "fill"
    PRESS = "press"
    WAIT_FOR_SELECTOR = "wait_for_selector"
    WAIT_FOR_TIMEOUT = "wait_for_timeout"
    SCREENSHOT = "screenshot"


@dataclass(frozen=True, slots=True)
class BrowserSettings:
    engine: str = "chromium"
    channel: str | None = "chrome"
    headless: bool = False
    slow_mo_ms: int = 0
    timeout_ms: int = 30000
    base_url: str | None = None
    viewport_width: int = 1440
    viewport_height: int = 900


@dataclass(frozen=True, slots=True)
class AutomationStep:
    name: str
    action: StepAction
    selector: str | None = None
    url: str | None = None
    text: str | None = None
    key: str | None = None
    milliseconds: int | None = None
    path: str | None = None
    full_page: bool = True
    timeout_ms: int | None = None


@dataclass(frozen=True, slots=True)
class AutomationWorkflow:
    name: str
    browser: BrowserSettings
    steps: tuple[AutomationStep, ...]

