from __future__ import annotations

import threading
import time
from collections.abc import Callable

from browser_automation.domain.exceptions import (
    BrowserAutomationError,
    ZaloClickAutomationError,
)
from browser_automation.domain.zalo_live_events import ZaloLiveEventLogEntry
from browser_automation.infrastructure.playwright_adapter.zalo_live_event_injection_script import (
    BINDING_NAME,
    ZALO_LIVE_EVENT_INJECTION_SCRIPT,
)


class PlaywrightZaloLiveEventListener:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop_event: threading.Event | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._event_sink: Callable[[ZaloLiveEventLogEntry], None] | None = None

    def start(
        self,
        *,
        remote_debugging_port: int,
        target_url: str,
        on_event: Callable[[ZaloLiveEventLogEntry], None],
        timeout_seconds: float,
    ) -> None:
        with self._lock:
            if self._running:
                raise BrowserAutomationError("The live event listener is already running.")

            self._event_sink = on_event
            self._stop_event = threading.Event()
            self._thread = threading.Thread(
                target=self._run_worker,
                args=(remote_debugging_port, target_url, timeout_seconds),
                daemon=True,
            )
            self._running = True
            self._thread.start()

    def stop(self) -> None:
        with self._lock:
            stop_event = self._stop_event
            thread = self._thread

        if stop_event is None:
            return

        stop_event.set()
        if thread is not None:
            thread.join(timeout=5.0)

        self._clear_state()

    def is_running(self) -> bool:
        with self._lock:
            return self._running

    def _run_worker(self, remote_debugging_port: int, target_url: str, timeout_seconds: float) -> None:
        stop_event = self._stop_event
        if stop_event is None:
            self._clear_state()
            return

        try:
            from playwright.sync_api import Error as PlaywrightError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            self._emit_terminal_system_event(
                "Live event listener could not start because Playwright is not installed.",
                detail=str(exc),
            )
            self._clear_state()
            return

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
                binding_installed = self._install_binding(page.context)
                self._prepare_page_for_live_decode(page, timeout_seconds=timeout_seconds)
                self._emit_system_event(
                    "Attached live listener to the active Zalo tab."
                    if binding_installed
                    else "Attached live listener to the active Zalo tab using the existing page binding.",
                    detail=page.url,
                )

                while not stop_event.is_set():
                    if page.is_closed():
                        raise BrowserAutomationError("The active Zalo tab was closed.")
                    page.wait_for_timeout(250)
        except (PlaywrightError, BrowserAutomationError, ZaloClickAutomationError) as exc:
            if not stop_event.is_set():
                self._emit_terminal_system_event(
                    "Live listener stopped unexpectedly.",
                    detail=str(exc),
                )
        except Exception as exc:  # noqa: BLE001
            if not stop_event.is_set():
                self._emit_terminal_system_event(
                    "Live listener stopped unexpectedly.",
                    detail=str(exc),
                )
        finally:
            if stop_event.is_set():
                self._emit_terminal_system_event("Stopped live listener.")
            self._clear_state()

    def _install_binding(self, context) -> bool:  # noqa: ANN001
        try:
            context.expose_binding(BINDING_NAME, self._handle_binding_event)
        except Exception as exc:  # noqa: BLE001
            if self._is_duplicate_binding_error(exc):
                return False
            raise
        return True

    def _prepare_page_for_live_decode(self, page, *, timeout_seconds: float) -> None:  # noqa: ANN001
        timeout_ms = int(timeout_seconds * 1000)
        page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
        page.bring_to_front()
        page.add_init_script(script=ZALO_LIVE_EVENT_INJECTION_SCRIPT)
        page.evaluate(ZALO_LIVE_EVENT_INJECTION_SCRIPT)
        page.reload(wait_until="domcontentloaded", timeout=timeout_ms)
        page.evaluate(ZALO_LIVE_EVENT_INJECTION_SCRIPT)

    def _is_duplicate_binding_error(self, exc: Exception) -> bool:
        message = str(exc).casefold()
        return "already registered" in message and any(
            fragment in message
            for fragment in ("binding", "browser context", "function")
        )

    def _handle_binding_event(self, source, payload) -> None:  # noqa: ANN001
        del source
        if not isinstance(payload, dict):
            return

        event = ZaloLiveEventLogEntry(
            event_type=str(payload.get("eventType") or "listener"),
            scope=str(payload.get("scope") or "page"),
            summary=str(payload.get("summary") or ""),
            detail=str(payload.get("detail") or ""),
            occurred_at=str(payload.get("occurredAt") or time.strftime("%Y-%m-%dT%H:%M:%SZ")),
        )
        self._emit_event(event)

    def _emit_system_event(self, summary: str, *, detail: str = "") -> None:
        self._emit_event(
            ZaloLiveEventLogEntry(
                event_type="listener",
                scope="system",
                summary=summary,
                detail=detail,
                occurred_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
        )

    def _emit_terminal_system_event(self, summary: str, *, detail: str = "") -> None:
        self._mark_not_running()
        self._emit_system_event(summary, detail=detail)

    def _emit_event(self, event: ZaloLiveEventLogEntry) -> None:
        sink = self._event_sink
        if sink is None:
            return
        sink(event)

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
            "Could not attach to the launched Chrome window for live event monitoring. "
            "Close all Google Chrome windows for that profile and launch again. "
            "If you are launching the real Chrome profile under the default 'Google\\Chrome\\User Data' directory, "
            "recent Chrome versions can ignore '--remote-debugging-port' for that profile. "
            "Use a dedicated automation profile copy or Chrome for Testing when you need live event monitoring."
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
        raise ZaloClickAutomationError("No Chrome page was available for live event monitoring.")

    def _mark_not_running(self) -> None:
        with self._lock:
            self._running = False

    def _clear_state(self) -> None:
        with self._lock:
            self._stop_event = None
            self._thread = None
            self._event_sink = None
            self._running = False
