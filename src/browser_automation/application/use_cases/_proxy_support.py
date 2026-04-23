from __future__ import annotations

from urllib.parse import unquote, urlsplit

from browser_automation.domain.exceptions import LauncherValidationError
from browser_automation.domain.proxy import ProxySettings

_SUPPORTED_PROXY_SCHEMES = {"http", "https", "socks4", "socks5"}


def parse_proxy_settings(raw_value: str) -> ProxySettings:
    value = raw_value.strip()
    if not value:
        raise LauncherValidationError("Proxy is required.")

    if "://" in value:
        return _parse_url_style_proxy(value)
    if "@" in value:
        return _parse_at_sign_proxy(value)
    return _parse_colon_style_proxy(value)


def normalize_optional_proxy_server(raw_value: str | None) -> str | None:
    if raw_value is None:
        return None

    normalized = raw_value.strip()
    if not normalized:
        return None
    return parse_proxy_settings(normalized).chrome_proxy_server


def _parse_url_style_proxy(value: str) -> ProxySettings:
    parsed = urlsplit(value)
    scheme = parsed.scheme.lower()
    if scheme not in _SUPPORTED_PROXY_SCHEMES:
        raise LauncherValidationError(
            "Unsupported proxy scheme. Use http, https, socks4, or socks5."
        )
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise LauncherValidationError(
            "Proxy value must not contain extra path, query, or fragment parts."
        )

    try:
        host = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise LauncherValidationError("Proxy port must be a valid number.") from exc

    username = None if parsed.username is None else unquote(parsed.username)
    password = None if parsed.password is None else unquote(parsed.password)
    return _build_proxy_settings(
        scheme=scheme,
        host=host,
        port=port,
        username=username,
        password=password,
    )


def _parse_at_sign_proxy(value: str) -> ProxySettings:
    credentials, address = value.rsplit("@", 1)
    if ":" not in credentials:
        raise LauncherValidationError(
            "Proxy credentials must use the format user:pass@host:port."
        )

    username, password = credentials.split(":", 1)
    host, port = _parse_host_and_port(address)
    return _build_proxy_settings(
        scheme="http",
        host=host,
        port=port,
        username=username,
        password=password,
    )


def _parse_colon_style_proxy(value: str) -> ProxySettings:
    parts = value.split(":")
    if len(parts) == 2:
        host, port_text = parts
        return _build_proxy_settings(
            scheme="http",
            host=host,
            port=_parse_port(port_text),
            username=None,
            password=None,
        )

    if len(parts) >= 4:
        host = parts[0]
        port_text = parts[1]
        username = parts[2]
        password = ":".join(parts[3:])
        return _build_proxy_settings(
            scheme="http",
            host=host,
            port=_parse_port(port_text),
            username=username,
            password=password,
        )

    raise LauncherValidationError(
        "Proxy format is invalid. Use host:port, user:pass@host:port, or host:port:user:pass."
    )


def _parse_host_and_port(address: str) -> tuple[str | None, int | None]:
    parsed = urlsplit(f"//{address}")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise LauncherValidationError(
            "Proxy value must only contain host and port."
        )

    try:
        return parsed.hostname, parsed.port
    except ValueError as exc:
        raise LauncherValidationError("Proxy port must be a valid number.") from exc


def _parse_port(value: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise LauncherValidationError("Proxy port must be a valid number.") from exc


def _build_proxy_settings(
    *,
    scheme: str,
    host: str | None,
    port: int | None,
    username: str | None,
    password: str | None,
) -> ProxySettings:
    normalized_host = "" if host is None else host.strip()
    if not normalized_host:
        raise LauncherValidationError("Proxy host is required.")
    if port is None or not (1 <= port <= 65535):
        raise LauncherValidationError("Proxy port must be between 1 and 65535.")

    normalized_username = None if username is None else username.strip()
    normalized_password = None if password is None else password.strip()
    if normalized_username == "":
        normalized_username = None
    if normalized_password == "":
        normalized_password = None
    if (normalized_username is None) != (normalized_password is None):
        raise LauncherValidationError(
            "Proxy credentials must include both username and password."
        )

    return ProxySettings(
        scheme=scheme,
        host=normalized_host,
        port=port,
        username=normalized_username,
        password=normalized_password,
    )
