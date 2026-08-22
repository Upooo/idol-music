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
        self.current: Track | None = None
        self._state = PlayerState.IDLE
        self._lock = asyncio.Lock()

    # --- State properties (read-only from outside) ---

    @property
    def state(self) -> PlayerState:
        return self._state

    @property
    def is_playing(self) -> bool:
        return self._state == PlayerState.PLAYING

    @property
    def is_paused(self) -> bool:
        return self._state == PlayerState.PAUSED

    @property
    def is_active(self) -> bool:
        return self._state in (PlayerState.PLAYING, PlayerState.PAUSED)

    # --- Playback controls ---

    async def play(self, track: Track) -> None:
        """Join VC (if needed) and start streaming a track."""
        async with self._lock:
            self.current = track
            self._state = PlayerState.PLAYING

            try:
                await self._calls.play(
                    self.chat_id,
                    MediaStream(
                        track.url,
                        video_flags=MediaStream.Flags.IGNORE,
                    ),
                )
                log.info("Playing: %s in %d", track.title, self.chat_id)
            except Exception as e:
                log.exception("Failed to play in %d: %s", self.chat_id, e)
                self._state = PlayerState.IDLE
                self.current = None
                raise

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
        """Stop playback and leave VC. Full reset."""
        async with self._lock:
            self._state = PlayerState.STOPPING
            self.current = None
            try:
                await self._calls.leave_call(self.chat_id)
            except Exception:
                pass  # already left or not in call
            self._state = PlayerState.IDLE

    async def handle_stream_end(self) -> None:
        """Called when PyTgCalls fires StreamEnded for this chat."""
        async with self._lock:
            if self._state in (PlayerState.IDLE, PlayerState.STOPPING):
                return  # Already handled or stop() in progress
            log.info("Stream ended in %d", self.chat_id)
            self.current = None
            self._state = PlayerState.IDLE

        # Notify session OUTSIDE the lock so it can call play() again
        if self._on_track_end:
            await self._on_track_end(self.chat_id)
