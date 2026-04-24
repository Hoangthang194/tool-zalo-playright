from __future__ import annotations

from dataclasses import dataclass

from browser_automation.application.ports.zalo_click_automation_runner import (
    ZaloClickAutomationRunner,
)
from browser_automation.application.use_cases._click_target_support import (
    build_css_selector,
    normalize_optional_upload_file_path,
    normalize_selector_kind,
    normalize_selector_value,
)
from browser_automation.domain.zalo_launcher import DEFAULT_ZALO_URL
from browser_automation.domain.zalo_workspace import SavedZaloClickTarget

DEFAULT_CLICK_ELEMENT_TIMEOUT_SECONDS = 12.0


@dataclass(frozen=True, slots=True)
class ClickZaloElementRequest:
    selector_kind: str
    selector_value: str
    remote_debugging_port: int
    target_name: str = "Test Element"
    target_url: str = DEFAULT_ZALO_URL
    upload_file_path: str = ""


@dataclass(frozen=True, slots=True)
class ClickZaloElementResult:
    clicked_target_name: str
    resolved_selector: str
    uploaded_file_path: str | None = None


class ClickZaloElementUseCase:
    def __init__(
        self,
        click_automation_runner: ZaloClickAutomationRunner,
        *,
        timeout_seconds: float = DEFAULT_CLICK_ELEMENT_TIMEOUT_SECONDS,
    ) -> None:
        self._click_automation_runner = click_automation_runner
        self._timeout_seconds = timeout_seconds

    def execute(self, request: ClickZaloElementRequest) -> ClickZaloElementResult:
        selector_kind = normalize_selector_kind(request.selector_kind)
        upload_file_path = normalize_optional_upload_file_path(request.upload_file_path)

        click_target = SavedZaloClickTarget(
            id="adhoc-click-target",
            name=request.target_name.strip() or "Test Element",
            selector_kind=selector_kind,
            selector_value=normalize_selector_value(request.selector_value),
            upload_file_path=upload_file_path,
        )
        resolved_selector = build_css_selector(click_target)

        self._click_automation_runner.run(
            remote_debugging_port=request.remote_debugging_port,
            target_url=request.target_url,
            click_targets=(click_target,),
            timeout_seconds=self._timeout_seconds,
        )

        return ClickZaloElementResult(
            clicked_target_name=click_target.name,
            resolved_selector=resolved_selector,
            uploaded_file_path=click_target.upload_file_path or None,
        )
