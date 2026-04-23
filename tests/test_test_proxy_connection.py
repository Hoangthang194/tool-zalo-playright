import pytest

from browser_automation.application.use_cases.test_proxy_connection import (
    TestProxyConnectionRequest,
    TestProxyConnectionUseCase,
)
from browser_automation.domain.exceptions import LauncherValidationError


class FakeProxyConnectivityChecker:
    def __init__(self, detected_ip: str = "203.0.113.9") -> None:
        self.detected_ip = detected_ip
        self.last_proxy = None
        self.last_timeout_seconds = None

    def check(self, proxy, *, timeout_seconds: float) -> str:
        self.last_proxy = proxy
        self.last_timeout_seconds = timeout_seconds
        return self.detected_ip


def test_test_proxy_connection_accepts_host_port_user_pass_format() -> None:
    checker = FakeProxyConnectivityChecker()
    use_case = TestProxyConnectionUseCase(checker, timeout_seconds=9.5)

    result = use_case.execute(
        TestProxyConnectionRequest(
            raw_proxy="171.236.172.8:50455:danggiang7:danggiang7"
        )
    )

    assert result.normalized_proxy_server == "171.236.172.8:50455"
    assert result.detected_ip == "203.0.113.9"
    assert result.uses_authentication is True
    assert checker.last_proxy.host == "171.236.172.8"
    assert checker.last_proxy.port == 50455
    assert checker.last_proxy.username == "danggiang7"
    assert checker.last_proxy.password == "danggiang7"
    assert checker.last_timeout_seconds == 9.5


def test_test_proxy_connection_rejects_invalid_format() -> None:
    use_case = TestProxyConnectionUseCase(FakeProxyConnectivityChecker())

    with pytest.raises(LauncherValidationError, match="Proxy format is invalid"):
        use_case.execute(TestProxyConnectionRequest(raw_proxy="171.236.172.8:50455:danggiang7"))
