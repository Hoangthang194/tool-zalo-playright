from __future__ import annotations

from dataclasses import dataclass

from browser_automation.application.ports.message_store import MessageStore
from browser_automation.application.ports.zalo_workspace_store import ZaloWorkspaceStore
from browser_automation.domain.exceptions import SettingsPersistenceError
from browser_automation.domain.messages import SavedZaloMessage
from browser_automation.domain.zalo_workspace import SavedZaloAccount


@dataclass(frozen=True, slots=True)
class IngestZaloMessageWebhookRequest:
    listener_token: str
    msg_id: str
    from_group_id: str | None
    to_group_id: str | None
    content: str


@dataclass(frozen=True, slots=True)
class IngestZaloMessageWebhookResult:
    status: str
    from_account_id: str | None = None
    detail: str = ""


class IngestZaloMessageWebhookUseCase:
    def __init__(
        self,
        workspace_store: ZaloWorkspaceStore,
        message_store: MessageStore,
    ) -> None:
        self._workspace_store = workspace_store
        self._message_store = message_store

    def execute(self, request: IngestZaloMessageWebhookRequest) -> IngestZaloMessageWebhookResult:
        listener_token = request.listener_token.strip()
        if not listener_token:
            return IngestZaloMessageWebhookResult(
                status="invalid",
                detail="listenerToken is required.",
            )

        msg_id = request.msg_id.strip()
        if not msg_id:
            return IngestZaloMessageWebhookResult(
                status="invalid",
                detail="msgId is required.",
            )

        if request.content is None or not request.content.strip():
            return IngestZaloMessageWebhookResult(
                status="invalid",
                detail="content is required.",
            )

        account = self._resolve_account_by_listener_token(listener_token)
        if account is None:
            return IngestZaloMessageWebhookResult(
                status="invalid_token",
                detail="listenerToken does not map to a known account.",
            )
        if account.mode != "listen":
            return IngestZaloMessageWebhookResult(
                status="account_mode_conflict",
                from_account_id=account.id,
                detail="Account is not active in listen mode.",
            )

        try:
            persistence_status = self._message_store.save_message(
                SavedZaloMessage(
                    msg_id=msg_id,
                    from_group_id=self._normalize_optional_value(request.from_group_id),
                    to_group_id=self._normalize_optional_value(request.to_group_id),
                    from_account_id=account.id,
                    content=request.content,
                )
            )
        except SettingsPersistenceError as exc:
            return IngestZaloMessageWebhookResult(
                status="failed",
                from_account_id=account.id,
                detail=str(exc),
            )

        return IngestZaloMessageWebhookResult(
            status=persistence_status,
            from_account_id=account.id,
            detail=(
                "Message already processed."
                if persistence_status == "already_processed"
                else "Message accepted."
            ),
        )

    def _resolve_account_by_listener_token(self, listener_token: str) -> SavedZaloAccount | None:
        workspace = self._workspace_store.load()
        for account in workspace.accounts:
            if account.listener_token == listener_token:
                return account
        return None

    def _normalize_optional_value(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

