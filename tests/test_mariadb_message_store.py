from __future__ import annotations

import pytest

from browser_automation.domain.exceptions import SettingsPersistenceError
from browser_automation.domain.messages import SavedZaloMessage
from browser_automation.infrastructure.persistence.mariadb_message_store import (
    MariaDbMessageStore,
)


class FakeDbError(Exception):
    pass


class FakeCursor:
    def __init__(self, error: Exception | None) -> None:
        self._error = error

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def execute(self, query: str, params: tuple[object, ...]) -> None:
        if self._error is not None:
            raise self._error


class FakeConnection:
    def __init__(self, error: Exception | None) -> None:
        self._error = error
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def cursor(self) -> FakeCursor:
        return FakeCursor(self._error)

    def commit(self) -> None:
        self.committed = True


class FakeConnectionFactory:
    def __init__(self, error: Exception | None = None) -> None:
        self._error = error

    def connect(self) -> FakeConnection:
        return FakeConnection(self._error)


def test_mariadb_message_store_returns_already_processed_for_duplicate_key() -> None:
    store = MariaDbMessageStore(FakeConnectionFactory(FakeDbError(1062, "Duplicate entry")))

    result = store.save_message(
        SavedZaloMessage(
            msg_id="msg-1",
            from_group_id="group-a",
            to_group_id="group-b",
            from_account_id="account-1",
            content="hello",
        )
    )

    assert result == "already_processed"


def test_mariadb_message_store_raises_actionable_error_for_foreign_key_failure() -> None:
    store = MariaDbMessageStore(FakeConnectionFactory(FakeDbError(1452, "Cannot add or update child row")))

    with pytest.raises(
        SettingsPersistenceError,
        match="Resolved account could not be persisted to MariaDB.",
    ):
        store.save_message(
            SavedZaloMessage(
                msg_id="msg-1",
                from_group_id="group-a",
                to_group_id="group-b",
                from_account_id="account-1",
                content="hello",
            )
        )
