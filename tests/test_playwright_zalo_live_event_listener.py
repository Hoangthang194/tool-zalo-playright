from browser_automation.infrastructure.playwright_adapter.playwright_zalo_live_event_listener import (
    PlaywrightZaloLiveEventListener,
)
from browser_automation.infrastructure.playwright_adapter.zalo_live_event_injection_script import (
    BINDING_NAME,
)


class DuplicateBindingContext:
    def expose_binding(self, name, callback) -> None:  # noqa: ANN001
        del callback
        raise RuntimeError(
            f"Function '{name}' has been already registered in browser context"
        )


class FailingBindingContext:
    def expose_binding(self, name, callback) -> None:  # noqa: ANN001
        del name, callback
        raise RuntimeError("Context is gone")


def test_playwright_live_event_listener_reuses_existing_binding() -> None:
    listener = PlaywrightZaloLiveEventListener()

    installed = listener._install_binding(DuplicateBindingContext())

    assert installed is False


def test_playwright_live_event_listener_reraises_unexpected_binding_errors() -> None:
    listener = PlaywrightZaloLiveEventListener()

    try:
        listener._install_binding(FailingBindingContext())
    except RuntimeError as exc:
        assert str(exc) == "Context is gone"
    else:
        raise AssertionError("Expected unexpected binding error to be re-raised")


def test_playwright_live_event_listener_marks_itself_stopped_before_terminal_event() -> None:
    listener = PlaywrightZaloLiveEventListener()
    observed_running_states: list[bool] = []

    listener._running = True
    listener._event_sink = lambda event: observed_running_states.append(listener.is_running())

    listener._emit_terminal_system_event(
        "Live listener stopped unexpectedly.",
        detail=BINDING_NAME,
    )

    assert observed_running_states == [False]


class FakePreparePage:
    def __init__(self) -> None:
        self.url = "https://chat.zalo.me"
        self.load_states: list[tuple[str, int | None]] = []
        self.brought_to_front = False
        self.added_scripts: list[str] = []
        self.evaluated_scripts: list[str] = []
        self.reload_calls: list[dict[str, object]] = []

    def wait_for_load_state(self, state: str, timeout: int | None = None) -> None:
        self.load_states.append((state, timeout))

    def bring_to_front(self) -> None:
        self.brought_to_front = True

    def add_init_script(self, *, script: str) -> None:
        self.added_scripts.append(script)

    def evaluate(self, script: str) -> None:
        self.evaluated_scripts.append(script)

    def reload(self, *, wait_until: str, timeout: int) -> None:
        self.reload_calls.append({"wait_until": wait_until, "timeout": timeout})


def test_playwright_live_event_listener_prepares_page_and_reloads_once_for_decode_hooking() -> None:
    listener = PlaywrightZaloLiveEventListener()
    page = FakePreparePage()

    listener._prepare_page_for_live_decode(page, timeout_seconds=7.0)

    assert page.brought_to_front is True
    assert page.added_scripts
    assert page.evaluated_scripts
    assert page.reload_calls == [{"wait_until": "domcontentloaded", "timeout": 7000}]
