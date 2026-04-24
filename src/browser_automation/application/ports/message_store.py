from __future__ import annotations

from typing import Protocol

from browser_automation.domain.messages import SavedZaloMessage


class MessageStore(Protocol):
    def save_message(self, message: SavedZaloMessage) -> str:
        """Persist one message and return 'inserted' or 'already_processed'."""

