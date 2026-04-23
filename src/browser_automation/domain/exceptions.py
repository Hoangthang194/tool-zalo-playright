class WorkflowValidationError(ValueError):
    """Raised when a workflow definition is invalid."""


class BrowserAutomationError(RuntimeError):
    """Raised when browser automation cannot be executed."""


class UnsupportedBrowserEngineError(BrowserAutomationError):
    """Raised when the requested browser engine is unsupported."""


class UnsupportedStepError(BrowserAutomationError):
    """Raised when a step cannot be executed."""


class LauncherValidationError(ValueError):
    """Raised when the Zalo launcher configuration is invalid."""


class ChromeLaunchError(RuntimeError):
    """Raised when Chrome cannot be started for the Zalo launcher."""


class ProxyConnectionError(RuntimeError):
    """Raised when a proxy connectivity test fails."""


class ZaloClickTargetConflictError(ValueError):
    """Raised when a saved click target conflicts with an existing entry."""


class ZaloClickTargetNotFoundError(ValueError):
    """Raised when a requested click target does not exist."""


class ZaloClickAutomationError(RuntimeError):
    """Raised when post-launch selector automation fails."""


class SettingsPersistenceError(RuntimeError):
    """Raised when launcher settings cannot be persisted."""


class SavedProfileConflictError(LauncherValidationError):
    """Raised when a saved Chrome profile conflicts with an existing entry."""


class SavedProfileNotFoundError(LauncherValidationError):
    """Raised when a requested saved Chrome profile does not exist."""


class SavedCookieConflictError(ValueError):
    """Raised when a saved cookie entry conflicts with an existing entry."""


class SavedCookieNotFoundError(ValueError):
    """Raised when a requested saved cookie entry does not exist."""


class SavedZaloAccountConflictError(ValueError):
    """Raised when a saved Zalo account entry conflicts with an existing entry."""


class SavedZaloAccountNotFoundError(ValueError):
    """Raised when a requested saved Zalo account entry does not exist."""
