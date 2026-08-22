"""SessionManager — registry of active MusicSessions."""

from __future__ import annotations

from pytgcalls import PyTgCalls

from music.session import MusicSession


class SessionManager:
    """Manages all active music sessions across groups."""

    def __init__(self, calls: PyTgCalls) -> None:
        self._calls = calls
        self._sessions: dict[int, MusicSession] = {}

    def get(self, chat_id: int) -> MusicSession:
        """Get or create a session for a chat."""
        if chat_id not in self._sessions:
            self._sessions[chat_id] = MusicSession(chat_id, self._calls)
        return self._sessions[chat_id]

    def remove(self, chat_id: int) -> None:
        """Remove a session after it's fully stopped."""
        self._sessions.pop(chat_id, None)

    @property
    def active_count(self) -> int:
        return len(self._sessions)

    @property
    def active_chats(self) -> list[int]:
        return list(self._sessions.keys())
