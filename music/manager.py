"""SessionManager \u2014 registry of active MusicSessions."""
from __future__ import annotations

from typing import Callable, Awaitable, Optional

from pytgcalls import PyTgCalls

from music.session import MusicSession


class SessionManager:
    """Manages all active music sessions across groups."""

    def __init__(
        self,
        calls: PyTgCalls,
        assistant=None,
        on_auto_leave: Optional[Callable[[int], Awaitable[None]]] = None,
    ) -> None:
        self._calls = calls
        self._assistant = assistant
        self._on_auto_leave = on_auto_leave
        self._sessions: dict[int, MusicSession] = {}

    def get(self, chat_id: int) -> MusicSession:
        if chat_id not in self._sessions:
            self._sessions[chat_id] = MusicSession(
                chat_id,
                self._calls,
                assistant=self._assistant,
                on_auto_leave=self._on_auto_leave,
            )
        return self._sessions[chat_id]

    def remove(self, chat_id: int) -> None:
        self._sessions.pop(chat_id, None)

    @property
    def active_count(self) -> int:
        return len(self._sessions)

    @property
    def active_chats(self) -> list[int]:
        return list(self._sessions.keys())
