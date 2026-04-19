class WorkflowValidationError(ValueError):
    """Raised when a workflow definition is invalid."""


class BrowserAutomationError(RuntimeError):
    """Raised when browser automation cannot be executed."""


class UnsupportedBrowserEngineError(BrowserAutomationError):
    """Raised when the requested browser engine is unsupported."""


class UnsupportedStepError(BrowserAutomationError):
    """Raised when a step cannot be executed."""

