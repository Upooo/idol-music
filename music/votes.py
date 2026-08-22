"""Vote tracker for skip voting."""
from __future__ import annotations


class VoteTracker:
    """Tracks skip votes per chat."""

    def __init__(self) -> None:
        self._votes: dict[int, set[int]] = {}

    def add_vote(self, chat_id: int, user_id: int) -> int:
        """Add a vote. Returns total vote count for this chat."""
        if chat_id not in self._votes:
            self._votes[chat_id] = set()
        self._votes[chat_id].add(user_id)
        return len(self._votes[chat_id])

    def clear(self, chat_id: int) -> None:
        """Clear votes for a chat (after skip or new track)."""
        self._votes.pop(chat_id, None)

    def count(self, chat_id: int) -> int:
        return len(self._votes.get(chat_id, set()))

    def has_voted(self, chat_id: int, user_id: int) -> bool:
        return user_id in self._votes.get(chat_id, set())
