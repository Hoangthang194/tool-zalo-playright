import pytest

from browser_automation.application.use_cases._click_target_support import (
    build_css_selector,
    extract_css_selector_from_html_snippet,
    looks_like_html_snippet,
    normalize_optional_upload_file_path,
)
from browser_automation.domain.exceptions import ZaloClickTargetConflictError
from browser_automation.domain.zalo_workspace import SavedZaloClickTarget


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


def test_normalize_optional_upload_file_path_accepts_existing_file(tmp_path) -> None:
    upload_file = tmp_path / "photo.png"
    upload_file.write_text("data", encoding="utf-8")

    normalized = normalize_optional_upload_file_path(str(upload_file))

    assert normalized == str(upload_file)


def test_normalize_optional_upload_file_path_rejects_missing_file(tmp_path) -> None:
    missing_file = tmp_path / "missing.png"

    with pytest.raises(ZaloClickTargetConflictError, match="Upload file path not found"):
        normalize_optional_upload_file_path(str(missing_file))


def test_build_css_selector_supports_anim_data_id() -> None:
    selector = build_css_selector(
        SavedZaloClickTarget(
            id="target-1",
            name="Open Group",
            selector_kind="anim-data-id",
            selector_value="g1509445607335510374",
        )
    )

    assert selector == "[anim-data-id='g1509445607335510374']"


def test_build_css_selector_supports_data_id() -> None:
    selector = build_css_selector(
        SavedZaloClickTarget(
            id="target-1",
            name="Open Thread",
            selector_kind="data-id",
            selector_value="div_TabMsg_ThrdChItem",
        )
    )

    assert selector == "[data-id='div_TabMsg_ThrdChItem']"


def test_extract_css_selector_from_html_snippet_can_prefer_anim_data_id() -> None:
    html = """
    <div class="msg-item" data-id="div_TabMsg_ThrdChItem" anim-data-id="g1509445607335510374">
        <div class="truncate">Sale Group</div>
    </div>
    """

    selector = extract_css_selector_from_html_snippet(html)

    assert selector == "[anim-data-id='g1509445607335510374']"
