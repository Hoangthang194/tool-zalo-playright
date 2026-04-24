from __future__ import annotations

from browser_automation.domain.exceptions import SettingsPersistenceError
from browser_automation.domain.messages import SavedZaloMessage
from browser_automation.infrastructure.persistence.mariadb_connection import MariaDbConnectionFactory


class MariaDbMessageStore:
    def __init__(self, connection_factory: MariaDbConnectionFactory) -> None:
        self._connection_factory = connection_factory

    def save_message(self, message: SavedZaloMessage) -> str:
        try:
            with self._connection_factory.connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO messages (msgId, fromGroupId, toGroupId, fromAccountId, content)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            message.msg_id,
                            message.from_group_id,
                            message.to_group_id,
                            message.from_account_id,
                            message.content,
                        ),
                    )
                connection.commit()
        except Exception as exc:  # noqa: BLE001
            if getattr(exc, "args", None):
                error_code = exc.args[0]
                if error_code == 1062:
                    return "already_processed"
            raise SettingsPersistenceError("Could not persist incoming Zalo message to MariaDB.") from exc
        return "inserted"

