from browser_automation.application.use_cases.ingest_zalo_message_webhook import (
    IngestZaloMessageWebhookRequest,
    IngestZaloMessageWebhookUseCase,
)
from browser_automation.domain.messages import SavedZaloMessage
from browser_automation.domain.zalo_workspace import SavedZaloAccount, ZaloWorkspaceLibrary


class InMemoryZaloWorkspaceStore:
    def __init__(self, library: ZaloWorkspaceLibrary | None = None) -> None:
        self.library = ZaloWorkspaceLibrary() if library is None else library

    def load(self) -> ZaloWorkspaceLibrary:
        return self.library

    def save(self, library: ZaloWorkspaceLibrary) -> None:
        self.library = library


class InMemoryMessageStore:
    def __init__(self) -> None:
        self.messages: dict[str, SavedZaloMessage] = {}

    def save_message(self, message: SavedZaloMessage) -> str:
        if message.msg_id in self.messages:
            return "already_processed"
        self.messages[message.msg_id] = message
        return "inserted"


def test_ingest_zalo_message_webhook_accepts_message_for_listen_account() -> None:
    workspace_store = InMemoryZaloWorkspaceStore(
        ZaloWorkspaceLibrary(
            accounts=(
                SavedZaloAccount(
                    id="account-1",
                    name="Profile 1",
                    profile_id="profile-1",
                    mode="listen",
                    listener_token="token-1",
                ),
            )
        )
    )
    message_store = InMemoryMessageStore()
    use_case = IngestZaloMessageWebhookUseCase(workspace_store, message_store)

    result = use_case.execute(
        IngestZaloMessageWebhookRequest(
            listener_token="token-1",
            msg_id="msg-1",
            from_group_id="group-a",
            to_group_id="group-b",
            content="hello",
        )
    )

    assert result.status == "inserted"
    assert result.from_account_id == "account-1"
    assert message_store.messages["msg-1"].from_account_id == "account-1"


def test_ingest_zalo_message_webhook_rejects_invalid_token() -> None:
    use_case = IngestZaloMessageWebhookUseCase(InMemoryZaloWorkspaceStore(), InMemoryMessageStore())

    result = use_case.execute(
        IngestZaloMessageWebhookRequest(
            listener_token="missing",
            msg_id="msg-1",
            from_group_id=None,
            to_group_id=None,
            content="hello",
        )
    )

    assert result.status == "invalid_token"


def test_ingest_zalo_message_webhook_rejects_send_mode_account() -> None:
    workspace_store = InMemoryZaloWorkspaceStore(
        ZaloWorkspaceLibrary(
            accounts=(
                SavedZaloAccount(
                    id="account-1",
                    name="Profile 1",
                    profile_id="profile-1",
                    mode="send",
                    listener_token="token-1",
                ),
            )
        )
    )
    use_case = IngestZaloMessageWebhookUseCase(workspace_store, InMemoryMessageStore())

    result = use_case.execute(
        IngestZaloMessageWebhookRequest(
            listener_token="token-1",
            msg_id="msg-1",
            from_group_id=None,
            to_group_id=None,
            content="hello",
        )
    )

    assert result.status == "account_mode_conflict"


def test_ingest_zalo_message_webhook_returns_already_processed_for_duplicate_msg_id() -> None:
    workspace_store = InMemoryZaloWorkspaceStore(
        ZaloWorkspaceLibrary(
            accounts=(
                SavedZaloAccount(
                    id="account-1",
                    name="Profile 1",
                    profile_id="profile-1",
                    mode="listen",
                    listener_token="token-1",
                ),
            )
        )
    )
    message_store = InMemoryMessageStore()
    use_case = IngestZaloMessageWebhookUseCase(workspace_store, message_store)

    first_result = use_case.execute(
        IngestZaloMessageWebhookRequest(
            listener_token="token-1",
            msg_id="msg-1",
            from_group_id=None,
            to_group_id=None,
            content="hello",
        )
    )
    second_result = use_case.execute(
        IngestZaloMessageWebhookRequest(
            listener_token="token-1",
            msg_id="msg-1",
            from_group_id=None,
            to_group_id=None,
            content="hello",
        )
    )

    assert first_result.status == "inserted"
    assert second_result.status == "already_processed"
