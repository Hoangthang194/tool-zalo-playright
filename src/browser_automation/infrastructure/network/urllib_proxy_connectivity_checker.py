from __future__ import annotations

from urllib import error, request

from browser_automation.domain.exceptions import ProxyConnectionError
from browser_automation.domain.proxy import ProxySettings

_DEFAULT_PROXY_TEST_URL = "https://api.ipify.org"
_DEFAULT_USER_AGENT = "browser-automation-proxy-test/1.0"


class UrllibProxyConnectivityChecker:
    def __init__(
        self,
        *,
        test_url: str = _DEFAULT_PROXY_TEST_URL,
        user_agent: str = _DEFAULT_USER_AGENT,
    ) -> None:
        self._test_url = test_url
        self._user_agent = user_agent

    def check(self, proxy: ProxySettings, *, timeout_seconds: float) -> str:
        opener = self._build_opener(proxy)
        http_request = request.Request(
            self._test_url,
            headers={"User-Agent": self._user_agent},
        )

        try:
            with opener.open(http_request, timeout=timeout_seconds) as response:
                body = response.read().decode("utf-8", errors="replace").strip()
                status_code = response.getcode()
        except error.HTTPError as exc:
            if exc.code == 407:
                raise ProxyConnectionError("Proxy authentication failed.") from exc
            raise ProxyConnectionError(
                f"Proxy test failed with HTTP status {exc.code}."
            ) from exc
        except error.URLError as exc:
            reason = exc.reason if getattr(exc, "reason", None) is not None else exc
            raise ProxyConnectionError(
                f"Could not connect through the proxy: {reason}"
            ) from exc
        except OSError as exc:
            raise ProxyConnectionError(
                f"Could not connect through the proxy: {exc}"
            ) from exc

        if status_code != 200:
            raise ProxyConnectionError(
                f"Proxy test endpoint returned HTTP status {status_code}."
            )
        if not body:
            raise ProxyConnectionError("Proxy test endpoint returned an empty response.")
        return body

    def _build_opener(self, proxy: ProxySettings):
        handlers: list[object] = [
            request.ProxyHandler(
                {
                    "http": proxy.request_proxy_url,
                    "https": proxy.request_proxy_url,
                }
            )
        ]

        if proxy.has_auth:
            password_manager = request.HTTPPasswordMgrWithDefaultRealm()
            password_manager.add_password(
                None,
                f"{proxy.scheme}://{proxy.host}:{proxy.port}",
                proxy.username or "",
                proxy.password or "",
            )
            handlers.append(request.ProxyBasicAuthHandler(password_manager))
            handlers.append(request.ProxyDigestAuthHandler(password_manager))

        return request.build_opener(*handlers)
