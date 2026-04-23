from __future__ import annotations

from typing import Protocol

from browser_automation.domain.proxy import ProxySettings


class ProxyConnectivityChecker(Protocol):
    def check(self, proxy: ProxySettings, *, timeout_seconds: float) -> str:
        """Return the public IP or response body observed through the proxy."""
