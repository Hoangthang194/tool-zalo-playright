from __future__ import annotations

import json
import socket
from urllib import error, request

from browser_automation.domain.exceptions import SettingsPersistenceError
from browser_automation.infrastructure.webhook.local_zalo_message_webhook_server import (
    LocalZaloMessageWebhookServer,
)


class StubUseCase:
    def execute(self, request_data):
        class Result:
            status = "inserted"
            detail = "Message accepted."
            from_account_id = "account-1"

        return Result()


class FailingUseCase:
    def execute(self, request_data):
        raise SettingsPersistenceError("Could not persist incoming Zalo message to MariaDB.")


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _post_json(url: str, payload: dict[str, object]) -> tuple[int, dict[str, object]]:
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def test_local_zalo_message_webhook_server_returns_json_failure_when_use_case_errors() -> None:
    port = _find_free_port()
    server = LocalZaloMessageWebhookServer(FailingUseCase(), port=port)
    server.start()

    try:
        status_code, payload = _post_json(
            f"http://127.0.0.1:{port}/webhooks/zalo/messages",
            {
                "listenerToken": "token-1",
                "msgId": "msg-1",
                "content": "hello",
            },
        )
    finally:
        server.stop()

    assert status_code == 500
    assert payload == {
        "status": "failed",
        "detail": "Could not persist incoming Zalo message to MariaDB.",
        "fromAccountId": None,
    }


def test_local_zalo_message_webhook_server_rejects_invalid_json_body() -> None:
    port = _find_free_port()
    server = LocalZaloMessageWebhookServer(StubUseCase(), port=port)
    server.start()

    req = request.Request(
        f"http://127.0.0.1:{port}/webhooks/zalo/messages",
        data=b"{bad json",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        try:
            with request.urlopen(req, timeout=5) as response:
                status_code = response.status
                payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            status_code = exc.code
            payload = json.loads(exc.read().decode("utf-8"))
    finally:
        server.stop()

    assert status_code == 400
    assert payload == {
        "status": "invalid",
        "detail": "Request body must be valid JSON.",
    }
