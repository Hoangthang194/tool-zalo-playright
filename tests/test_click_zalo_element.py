import pytest

from browser_automation.application.use_cases.click_zalo_element import (
    ClickZaloElementRequest,
    ClickZaloElementUseCase,
)
from browser_automation.domain.exceptions import ZaloClickTargetConflictError


class FakeClickAutomationRunner:
    def __init__(self) -> None:
        self.remote_debugging_port = None
        self.target_url = None
        self.click_targets = None
        self.timeout_seconds = None

    def run(self, *, remote_debugging_port: int, target_url: str, click_targets, timeout_seconds: float):
        self.remote_debugging_port = remote_debugging_port
        self.target_url = target_url
        self.click_targets = click_targets
        self.timeout_seconds = timeout_seconds

        class Result:
            clicked_target_names = ("Test Element",)

        return Result()


def test_click_zalo_element_uses_current_id_selector() -> None:
    runner = FakeClickAutomationRunner()
    use_case = ClickZaloElementUseCase(runner, timeout_seconds=8.0)

    result = use_case.execute(
        ClickZaloElementRequest(
            target_name="Open Profile",
            selector_kind="id",
            selector_value="btnSubmit",
            remote_debugging_port=9222,
        )
    )

    assert result.clicked_target_name == "Open Profile"
    assert result.resolved_selector == "#btnSubmit"
    assert runner.remote_debugging_port == 9222
    assert runner.click_targets is not None
    assert len(runner.click_targets) == 1
    assert runner.click_targets[0].selector_kind == "id"
    assert runner.click_targets[0].selector_value == "btnSubmit"
    assert runner.timeout_seconds == 8.0


def test_click_zalo_element_rejects_empty_selector_value() -> None:
    use_case = ClickZaloElementUseCase(FakeClickAutomationRunner())

    with pytest.raises(ZaloClickTargetConflictError, match="Selector value is required"):
        use_case.execute(
            ClickZaloElementRequest(
                selector_kind="class",
                selector_value=" ",
                remote_debugging_port=9222,
            )
        )


def test_click_zalo_element_resolves_html_snippet_to_clickable_selector() -> None:
    runner = FakeClickAutomationRunner()
    use_case = ClickZaloElementUseCase(runner)

    result = use_case.execute(
        ClickZaloElementRequest(
            target_name="Search Box",
            selector_kind="html",
            selector_value="""
            <div id="contact-search">
                <span>Search</span>
                <input id="contact-search-input" data-id="txt_Main_Search" type="text">
            </div>
            """,
            remote_debugging_port=9222,
        )
    )

    assert result.clicked_target_name == "Search Box"
    assert result.resolved_selector == "#contact-search-input"
    assert runner.click_targets is not None
    assert runner.click_targets[0].selector_kind == "html"


def test_click_zalo_element_uses_anim_data_id_selector() -> None:
    runner = FakeClickAutomationRunner()
    use_case = ClickZaloElementUseCase(runner)

    result = use_case.execute(
        ClickZaloElementRequest(
            target_name="Open Group",
            selector_kind="anim-data-id",
            selector_value="g1509445607335510374",
            remote_debugging_port=9222,
        )
    )

    assert result.clicked_target_name == "Open Group"
    assert result.resolved_selector == "[anim-data-id='g1509445607335510374']"
    assert runner.click_targets is not None
    assert runner.click_targets[0].selector_kind == "anim-data-id"
