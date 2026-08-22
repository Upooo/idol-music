"""Player — abstraction over PyTgCalls for one group.

Handles: join, play, pause, resume, stop, leave.
Emits stream_ended callback so the session can advance the queue.
"""

from __future__ import annotations

import logging
from typing import Callable, Awaitable

from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped

from music.track import Track

log = logging.getLogger(__name__)


class Player:
    """Manages voice chat playback for a single group."""

    def __init__(
        self,
        chat_id: int,
        calls: PyTgCalls,
        on_track_end: Callable[[int], Awaitable[None]] | None = None,
    ) -> None:
        self.chat_id = chat_id
        self._calls = calls
        self._on_track_end = on_track_end
        self.current: Track | None = None
        self.is_playing = False
        self.is_paused = False

    async def play(self, track: Track) -> None:
        """Join VC (if needed) and start streaming a track."""
        self.current = track
        self.is_playing = True
        self.is_paused = False

        try:
            await self._calls.play(
                self.chat_id,
                AudioPiped(track.url),
            )
            log.info("Playing: %s in %d", track.title, self.chat_id)
        except Exception as e:
            log.exception("Failed to play in %d: %s", self.chat_id, e)
            self.is_playing = False
            self.current = None
            raise

    async def pause(self) -> None:
        if not self.is_playing or self.is_paused:
            return
        await self._calls.pause_stream(self.chat_id)
        self.is_paused = True

    async def resume(self) -> None:
        if not self.is_paused:
            return
        await self._calls.resume_stream(self.chat_id)
        self.is_paused = False

    async def stop(self) -> None:
        """Stop playback and leave VC. Full reset."""
        self.current = None
        self.is_playing = False
        self.is_paused = False
        try:
            await self._calls.leave_call(self.chat_id)
        except Exception:
            pass  # already left or not in call

    async def handle_stream_end(self) -> None:
        """Called by PyTgCalls when the current stream ends."""
        log.info("Stream ended in %d", self.chat_id)
        self.current = None
        self.is_playing = False
        self.is_paused = False
        if self._on_track_end:
            await self._on_track_end(self.chat_id)
