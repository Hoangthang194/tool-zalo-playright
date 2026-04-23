from __future__ import annotations

import time

from browser_automation.application.ports.zalo_click_automation_runner import (
    ClickAutomationResult,
    ZaloClickAutomationRunner,
)
from browser_automation.application.use_cases._click_target_support import (
    build_css_selector,
)
from browser_automation.domain.exceptions import (
    BrowserAutomationError,
    ZaloClickAutomationError,
)
from browser_automation.domain.zalo_workspace import SavedZaloClickTarget


class PlaywrightZaloClickAutomationRunner(ZaloClickAutomationRunner):
    def run(
        self,
        *,
        remote_debugging_port: int,
        target_url: str,
        click_targets: tuple[SavedZaloClickTarget, ...],
        timeout_seconds: float,
    ) -> ClickAutomationResult:
        try:
            from playwright.sync_api import Error as PlaywrightError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise BrowserAutomationError(
                "Playwright is not installed. Run 'python -m pip install -e \".[dev]\"' or 'pip install playwright'."
            ) from exc

        endpoint = f"http://127.0.0.1:{remote_debugging_port}"

        try:
            with sync_playwright() as playwright:
                browser = self._connect_with_retry(
                    playwright,
                    endpoint=endpoint,
                    timeout_seconds=timeout_seconds,
                )
                page = self._wait_for_target_page(
                    browser=browser,
                    target_url=target_url,
                    timeout_seconds=timeout_seconds,
                )
                page.wait_for_load_state("domcontentloaded", timeout=int(timeout_seconds * 1000))
                page.bring_to_front()

                clicked_target_names: list[str] = []
                for click_target in click_targets:
                    css_selector = build_css_selector(click_target)
                    locator = page.locator(css_selector).first
                    self._ensure_locator_exists(locator, css_selector=css_selector)
                    if click_target.upload_file_path:
                        self._handle_file_target(
                            page,
                            locator,
                            css_selector=css_selector,
                            upload_file_path=click_target.upload_file_path,
                            timeout_seconds=timeout_seconds,
                        )
                        clicked_target_names.append(click_target.name)
                        return ClickAutomationResult(
                            clicked_target_names=tuple(clicked_target_names)
                        )

                    self._click_locator(
                        locator,
                        css_selector=css_selector,
                        timeout_seconds=timeout_seconds,
                    )
                    clicked_target_names.append(click_target.name)

                return ClickAutomationResult(
                    clicked_target_names=tuple(clicked_target_names)
                )
        except PlaywrightError as exc:
            raise ZaloClickAutomationError(f"Selector automation failed: {exc}") from exc

    def _connect_with_retry(self, playwright, *, endpoint: str, timeout_seconds: float):
        deadline = time.monotonic() + timeout_seconds
        last_error = None

        while time.monotonic() < deadline:
            remaining_ms = max(250, int((deadline - time.monotonic()) * 1000))
            try:
                return playwright.chromium.connect_over_cdp(
                    endpoint,
                    timeout=min(1500, remaining_ms),
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(0.5)

        raise ZaloClickAutomationError(
            "Could not attach to the launched Chrome window for selector automation. "
            "Close all Google Chrome windows for that profile and launch again. "
            "If you are launching the real Chrome profile under the default 'Google\\Chrome\\User Data' directory, "
            "recent Chrome versions can ignore '--remote-debugging-port' for that profile. "
            "Use a dedicated automation profile copy or Chrome for Testing when you need selector automation."
        ) from last_error

    def _wait_for_target_page(self, *, browser, target_url: str, timeout_seconds: float):
        deadline = time.monotonic() + timeout_seconds
        fallback_page = None

        while time.monotonic() < deadline:
            for context in browser.contexts:
                for page in context.pages:
                    if fallback_page is None:
                        fallback_page = page
                    if not page.url:
                        continue
                    if page.url.startswith(target_url):
                        return page
            time.sleep(0.3)

        if fallback_page is not None:
            return fallback_page
        raise ZaloClickAutomationError("No Chrome page was available for selector automation.")

    def _ensure_locator_exists(self, locator, *, css_selector: str) -> None:
        try:
            if locator.count() > 0:
                return
        except Exception as exc:  # noqa: BLE001
            raise ZaloClickAutomationError(
                f"Could not inspect selector '{css_selector}' on the active page."
            ) from exc

        raise ZaloClickAutomationError(
            f"Selector not found on the active page: '{css_selector}'."
        )

    def _click_locator(self, locator, *, css_selector: str, timeout_seconds: float) -> None:
        timeout_ms = int(timeout_seconds * 1000)
        locator.scroll_into_view_if_needed(timeout=timeout_ms)

        try:
            locator.click(timeout=timeout_ms)
            return
        except Exception:  # noqa: BLE001
            # Zalo sometimes wraps real inputs with placeholder overlays.
            # Fallback to direct DOM focus/click for controls such as the search box.
            try:
                locator.evaluate(
                    """
                    (element) => {
                        if (typeof element.focus === "function") {
                            element.focus();
                        }
                        if (typeof element.click === "function") {
                            element.click();
                        }
                    }
                    """
                )
            except Exception as fallback_exc:  # noqa: BLE001
                raise ZaloClickAutomationError(
                    f"Selector was found but could not be clicked: '{css_selector}'."
                ) from fallback_exc

    def _handle_file_target(
        self,
        page,
        locator,
        *,
        css_selector: str,
        upload_file_path: str,
        timeout_seconds: float,
    ) -> None:
        timeout_ms = int(timeout_seconds * 1000)

        try:
            element_info = locator.evaluate(
                """
                (element) => ({
                    tag: (element.tagName || "").toLowerCase(),
                    type: (element.getAttribute("type") || "").toLowerCase(),
                })
                """
            )
        except Exception:  # noqa: BLE001
            element_info = {"tag": "", "type": ""}

        if element_info.get("tag") == "input" and element_info.get("type") == "file":
            locator.set_input_files(upload_file_path, timeout=timeout_ms)
            self._submit_uploaded_file(page, timeout_seconds=timeout_seconds)
            return

        try:
            with page.expect_file_chooser(timeout=timeout_ms) as file_chooser_info:
                self._click_locator(
                    locator,
                    css_selector=css_selector,
                    timeout_seconds=timeout_seconds,
                )
            file_chooser_info.value.set_files(upload_file_path, timeout=timeout_ms)
            self._submit_uploaded_file(page, timeout_seconds=timeout_seconds)
            return
        except Exception as exc:  # noqa: BLE001
            raise ZaloClickAutomationError(
                f"The selected element did not expose a file chooser for upload automation: '{css_selector}'."
            ) from exc

    def _submit_uploaded_file(self, page, *, timeout_seconds: float) -> None:
        timeout_ms = int(timeout_seconds * 1000)
        time.sleep(0.5)

        send_selectors = (
            "[data-id='btn_Send_Text']",
            "[data-id='btn_send']",
            "[aria-label='Send']",
            "button[type='submit']",
        )

        for selector in send_selectors:
            locator = page.locator(selector).first
            try:
                if locator.count() == 0:
                    continue
                locator.click(timeout=1000)
                return
            except Exception:
                continue

        try:
            page.keyboard.press("Enter", timeout=timeout_ms)
            return
        except Exception as exc:
            raise ZaloClickAutomationError(
                "The file was selected but the app could not send it automatically."
            ) from exc
