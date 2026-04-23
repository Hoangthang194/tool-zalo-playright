import pytest

from browser_automation.application.use_cases._click_target_support import (
    extract_css_selector_from_html_snippet,
    looks_like_html_snippet,
)
from browser_automation.domain.exceptions import ZaloClickTargetConflictError


def test_extract_css_selector_from_html_snippet_prefers_interactive_input() -> None:
    html = """
    <div id="contact-search" class="gridv2 flx-al-c ovf-hidden web fluid small grid-fluid-8">
        <div class="group-search grid-item">
            <span>Search</span>
            <input id="contact-search-input" data-id="txt_Main_Search" type="text">
        </div>
        <div data-id="btn_Main_AddFrd" title="Add friend"></div>
    </div>
    """

    selector = extract_css_selector_from_html_snippet(html)

    assert selector == "#contact-search-input"


def test_extract_css_selector_from_html_snippet_falls_back_to_root_id() -> None:
    html = '<div id="contact-search" class="group-search"></div>'

    selector = extract_css_selector_from_html_snippet(html)

    assert selector == "#contact-search"


def test_looks_like_html_snippet_detects_real_html() -> None:
    assert looks_like_html_snippet('<input id="contact-search-input" type="text">')
    assert not looks_like_html_snippet("contact-search-input")


def test_extract_css_selector_from_html_snippet_rejects_invalid_html() -> None:
    with pytest.raises(
        ZaloClickTargetConflictError,
        match="HTML selector type requires a valid HTML snippet",
    ):
        extract_css_selector_from_html_snippet("contact-search-input")
