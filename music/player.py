"""Player — abstraction over PyTgCalls 2.x for one group.

Handles: join, play, pause, resume, stop, leave.
Uses an enum-based state machine and asyncio.Lock for thread safety.
"""

from __future__ import annotations

import asyncio
import enum
import logging
from typing import Callable, Awaitable

from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

from music.track import Track

log = logging.getLogger(__name__)


class PlayerState(enum.Enum):
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"
    STOPPING = "stopping"


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
        self._state = PlayerState.IDLE
        self._lock = asyncio.Lock()
        self.current_track: Track | None = None

    @property
    def state(self) -> PlayerState:
        return self._state

    @property
    def is_active(self) -> bool:
        return self._state in (PlayerState.PLAYING, PlayerState.PAUSED)

    async def play(self, track: Track) -> None:
        async with self._lock:
            # Force leave first to reset stale PyTgCalls state (fixes ghost VC after restart)
            try:
                await self._calls.leave_call(self.chat_id)
            except Exception:
                pass
            await asyncio.sleep(0.3)  # brief pause for Telegram to process

            self.current_track = track
            stream = MediaStream(track.url, video_flags=MediaStream.Flags.IGNORE)
            await self._calls.play(self.chat_id, stream)
            self._state = PlayerState.PLAYING
            log.info("Playing in %d: %s", self.chat_id, track.title)

    async def pause(self) -> None:
        async with self._lock:
            if self._state != PlayerState.PLAYING:
                return
            await self._calls.pause(self.chat_id)
            self._state = PlayerState.PAUSED

    async def resume(self) -> None:
        async with self._lock:
            if self._state != PlayerState.PAUSED:
                return
            await self._calls.resume(self.chat_id)
            self._state = PlayerState.PLAYING

    async def stop(self) -> None:
        async with self._lock:
            if self._state == PlayerState.IDLE:
                return
            self._state = PlayerState.STOPPING
            try:
                await self._calls.leave_call(self.chat_id)
            except Exception:
                pass
            self.current_track = None
            self._state = PlayerState.IDLE

    async def handle_stream_end(self) -> None:
        """Called by PyTgCalls when stream finishes."""
        async with self._lock:
            if self._state == PlayerState.STOPPING:
                return
            self._state = PlayerState.IDLE
            self.current_track = None

        if self._on_track_end:
            await self._on_track_end(self.chat_id)
