from __future__ import annotations

import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from browser_automation.application.use_cases.ingest_zalo_message_webhook import (
    IngestZaloMessageWebhookRequest,
    IngestZaloMessageWebhookUseCase,
)


class LocalZaloMessageWebhookServer:
    def __init__(
        self,
        use_case: IngestZaloMessageWebhookUseCase,
        *,
        host: str = "127.0.0.1",
        port: int = 8765,
    ) -> None:
        self._use_case = use_case
        self._host = host
        self._port = port
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def url(self) -> str:
        return f"http://{self._host}:{self._port}/webhooks/zalo/messages"

    def start(self) -> None:
        if self._server is not None:
            return
        server = ThreadingHTTPServer((self._host, self._port), self._build_handler())
        self._server = server
        self._thread = threading.Thread(target=server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        self._server = None
        self._thread = None

    def _build_handler(self):
        use_case = self._use_case

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                if self.path != "/webhooks/zalo/messages":
                    self._write_json(HTTPStatus.NOT_FOUND, {"status": "not_found"})
                    return

                content_length = int(self.headers.get("Content-Length", "0"))
                raw_body = self.rfile.read(content_length)
                try:
                    payload = json.loads(raw_body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    self._write_json(
                        HTTPStatus.BAD_REQUEST,
                        {"status": "invalid", "detail": "Request body must be valid JSON."},
                    )
                    return

                if not isinstance(payload, dict):
                    self._write_json(
                        HTTPStatus.BAD_REQUEST,
                        {"status": "invalid", "detail": "Request body must be a JSON object."},
                    )
                    return

                result = use_case.execute(
                    IngestZaloMessageWebhookRequest(
                        listener_token=str(payload.get("listenerToken") or ""),
                        msg_id=str(payload.get("msgId") or ""),
                        from_group_id=_optional_str(payload.get("fromGroupId")),
                        to_group_id=_optional_str(payload.get("toGroupId")),
                        content=str(payload.get("content") or ""),
                    )
                )
                status_code = HTTPStatus.OK
                if result.status in {"invalid", "invalid_token", "account_mode_conflict"}:
                    status_code = HTTPStatus.BAD_REQUEST
                self._write_json(
                    status_code,
                    {
                        "status": result.status,
                        "detail": result.detail,
                        "fromAccountId": result.from_account_id,
                    },
                )

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
                return

            def _write_json(self, status_code: HTTPStatus, payload: dict[str, Any]) -> None:
                encoded_payload = json.dumps(payload).encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded_payload)))
                self.end_headers()
                self.wfile.write(encoded_payload)

        return Handler


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    normalized = value.strip()
    return normalized or None
