from __future__ import annotations

from dataclasses import dataclass

from browser_automation.application.ports.proxy_connectivity_checker import (
    ProxyConnectivityChecker,
)
from browser_automation.application.use_cases._proxy_support import parse_proxy_settings

DEFAULT_PROXY_TEST_TIMEOUT_SECONDS = 12.0


@dataclass(frozen=True, slots=True)
class TestProxyConnectionRequest:
    __test__ = False
    raw_proxy: str


@dataclass(frozen=True, slots=True)
class TestProxyConnectionResult:
    __test__ = False
    normalized_proxy_server: str
    detected_ip: str
    uses_authentication: bool


class TestProxyConnectionUseCase:
    __test__ = False

    def __init__(
        self,
        proxy_checker: ProxyConnectivityChecker,
        *,
        timeout_seconds: float = DEFAULT_PROXY_TEST_TIMEOUT_SECONDS,
    ) -> None:
        self._proxy_checker = proxy_checker
        self._timeout_seconds = timeout_seconds

    def execute(self, request: TestProxyConnectionRequest) -> TestProxyConnectionResult:
        proxy = parse_proxy_settings(request.raw_proxy)
        detected_ip = self._proxy_checker.check(proxy, timeout_seconds=self._timeout_seconds).strip()
        return TestProxyConnectionResult(
            normalized_proxy_server=proxy.chrome_proxy_server,
            detected_ip=detected_ip,
            uses_authentication=proxy.has_auth,
        )
