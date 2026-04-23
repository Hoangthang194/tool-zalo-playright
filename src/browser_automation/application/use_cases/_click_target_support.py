from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser

from browser_automation.domain.exceptions import (
    ZaloClickTargetConflictError,
)
from browser_automation.domain.zalo_workspace import SavedZaloClickTarget

SUPPORTED_SELECTOR_KINDS = ("class", "id", "data-id", "anim-data-id", "css", "html")
_HTML_TAG_PATTERN = re.compile(r"<[a-zA-Z][^>]*>")
_INTERACTIVE_TAGS = ("input", "textarea", "select", "button", "a")


def normalize_click_target_name(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ZaloClickTargetConflictError("Click target name is required.")
    return normalized


def normalize_selector_kind(value: str) -> str:
    normalized = value.strip().casefold()
    if normalized not in SUPPORTED_SELECTOR_KINDS:
        raise ZaloClickTargetConflictError(
            "Selector type must be one of: class, id, data-id, anim-data-id, css, html."
        )
    return normalized


def normalize_selector_value(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ZaloClickTargetConflictError("Selector value is required.")
    return normalized


def looks_like_html_snippet(value: str) -> bool:
    normalized = value.strip()
    if not normalized or "<" not in normalized or ">" not in normalized:
        return False
    return bool(_HTML_TAG_PATTERN.search(normalized))


@dataclass(frozen=True, slots=True)
class _ParsedHtmlElement:
    tag: str
    attrs: dict[str, str]


class _HtmlElementParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[_ParsedHtmlElement] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._append_element(tag, attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._append_element(tag, attrs)

    def _append_element(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_attrs: dict[str, str] = {}
        for attr_name, attr_value in attrs:
            if attr_name is None or attr_value is None:
                continue
            cleaned_value = attr_value.strip()
            if cleaned_value:
                normalized_attrs[attr_name.casefold()] = cleaned_value

        self.elements.append(
            _ParsedHtmlElement(
                tag=tag.casefold(),
                attrs=normalized_attrs,
            )
        )


def extract_css_selector_from_html_snippet(value: str) -> str:
    normalized = normalize_selector_value(value)
    if not looks_like_html_snippet(normalized):
        raise ZaloClickTargetConflictError(
            "HTML selector type requires a valid HTML snippet."
        )

    parser = _HtmlElementParser()
    parser.feed(normalized)
    parser.close()

    for tag_name in _INTERACTIVE_TAGS:
        selector = _find_selector(parser.elements, preferred_tag=tag_name)
        if selector is not None:
            return selector

    selector = _find_selector(parser.elements)
    if selector is not None:
        return selector

    raise ZaloClickTargetConflictError(
        "Could not resolve a clickable selector from the provided HTML snippet."
    )


def build_css_selector(target: SavedZaloClickTarget) -> str:
    selector_value = target.selector_value.strip()
    if target.selector_kind == "html":
        return extract_css_selector_from_html_snippet(selector_value)

    if target.selector_kind == "class":
        cleaned = selector_value.lstrip(".").strip()
        class_tokens = [token for token in cleaned.split() if token]
        if not class_tokens:
            raise ZaloClickTargetConflictError("Class selector value is required.")
        return "".join(f".{token}" for token in class_tokens)

    if target.selector_kind == "id":
        cleaned = selector_value.lstrip("#").strip()
        if not cleaned:
            raise ZaloClickTargetConflictError("ID selector value is required.")
        return f"#{cleaned}"

    if target.selector_kind == "data-id":
        return _build_attribute_selector("data-id", selector_value)

    if target.selector_kind == "anim-data-id":
        return _build_attribute_selector("anim-data-id", selector_value)

    return selector_value


def _find_selector(
    elements: list[_ParsedHtmlElement],
    *,
    preferred_tag: str | None = None,
) -> str | None:
    for element in elements:
        if preferred_tag is not None and element.tag != preferred_tag:
            continue
        selector = _selector_from_element(element)
        if selector is not None:
            return selector
    return None


def _selector_from_element(element: _ParsedHtmlElement) -> str | None:
    element_id = element.attrs.get("id")
    if element_id:
        cleaned_id = element_id.lstrip("#").strip()
        if cleaned_id:
            return f"#{cleaned_id}"

    anim_data_id = element.attrs.get("anim-data-id")
    if anim_data_id:
        return _build_attribute_selector("anim-data-id", anim_data_id)

    data_id = element.attrs.get("data-id")
    if data_id:
        return _build_attribute_selector("data-id", data_id)

    name = element.attrs.get("name")
    if name:
        return _build_attribute_selector("name", name)

    title = element.attrs.get("title")
    if title:
        return _build_attribute_selector("title", title)

    placeholder = element.attrs.get("placeholder")
    if placeholder:
        return _build_attribute_selector("placeholder", placeholder)

    class_value = element.attrs.get("class")
    if class_value:
        class_tokens = [token for token in class_value.split() if token]
        if class_tokens:
            return "".join(f".{token}" for token in class_tokens)

    return None


def _build_attribute_selector(name: str, value: str) -> str:
    escaped_value = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"[{name}='{escaped_value}']"
