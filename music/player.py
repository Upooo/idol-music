"""Player — voice chat playback for one group (V1.1.0 Clean).

State machine: IDLE → PLAYING ↔ PAUSED → IDLE.
leave_group_call is called ONLY in stop().
play() never force-leaves first (that caused the mute bug).
"""
from __future__ import annotations

import asyncio
import enum
import logging

from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

from music.track import Track

log = logging.getLogger(__name__)


class PlayerState(enum.Enum):
    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"


class Player:
    """Manages voice chat playback for a single group."""

    def __init__(self, chat_id: int, calls: PyTgCalls) -> None:
        self.chat_id = chat_id
        self._calls = calls
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
        """Start playing a track. Does NOT leave VC first."""
        async with self._lock:
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
        """Stop playback AND leave the voice chat."""
        async with self._lock:
            if self._state == PlayerState.IDLE:
                return
            try:
                await self._calls.leave_group_call(self.chat_id)
            except Exception as exc:
                log.debug("leave_group_call in %d: %s", self.chat_id, exc)
            self.current_track = None
            self._state = PlayerState.IDLE

    async def on_stream_end(self) -> None:
        """Called when PyTgCalls signals stream finished.
        Resets state so the next track can be played.
        Does NOT leave VC — session decides what to do next."""
        async with self._lock:
            self.current_track = None
            self._state = PlayerState.IDLE
