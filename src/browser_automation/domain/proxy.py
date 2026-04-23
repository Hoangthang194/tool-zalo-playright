from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote


@dataclass(frozen=True, slots=True)
class ProxySettings:
    host: str
    port: int
    username: str | None = None
    password: str | None = None
    scheme: str = "http"

    @property
    def has_auth(self) -> bool:
        return self.username is not None

    @property
    def chrome_proxy_server(self) -> str:
        base_address = f"{self.host}:{self.port}"
        if self.scheme == "http":
            return base_address
        return f"{self.scheme}://{base_address}"

    @property
    def request_proxy_url(self) -> str:
        authority = f"{self.host}:{self.port}"
        if not self.has_auth:
            return f"{self.scheme}://{authority}"

        quoted_username = quote(self.username or "", safe="")
        quoted_password = quote(self.password or "", safe="")
        return f"{self.scheme}://{quoted_username}:{quoted_password}@{authority}"
