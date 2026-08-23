"""SessionManager — registry of active MusicSessions."""
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
        """Get or create a session (use for write commands like play)."""
        if chat_id not in self._sessions:
            self._sessions[chat_id] = MusicSession(
                chat_id,
                self._calls,
                assistant=self._assistant,
                on_auto_leave=self._on_auto_leave,
            )
        return self._sessions[chat_id]

    def get_existing(self, chat_id: int) -> Optional[MusicSession]:
        """Get session only if it exists (use for read/event commands)."""
        return self._sessions.get(chat_id)

    async def remove(self, chat_id: int) -> None:
        """Remove session with proper cleanup."""
        session = self._sessions.pop(chat_id, None)
        if session:
            session._stop_auto_leave_checker()
            # Ensure player is stopped
            try:
                await session.player.stop()
            except Exception:
                pass

    def active_chat_ids(self) -> list[int]:
        return list(self._sessions.keys())

    def __len__(self) -> int:
        return len(self._sessions)
