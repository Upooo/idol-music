"""MusicSession — one session per group.

Holds: player, queue (manual + autoplay), state.
"""

from __future__ import annotations

import logging
from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytgcalls import PyTgCalls

from music.player import Player
from music.track import Track

log = logging.getLogger(__name__)


class MusicSession:
    """Represents an active music session in one group."""

    def __init__(self, chat_id: int, calls: PyTgCalls) -> None:
        self.chat_id = chat_id
        self.queue: deque[Track] = deque()
        self.player = Player(
            chat_id=chat_id,
            calls=calls,
            on_track_end=self._on_track_end,
        )
        self.autoplay_enabled = False

    async def add_and_play(self, track: Track) -> int:
        """Add track to queue. If nothing playing, start immediately.

        Returns position in queue (0 = now playing).
        """
        if not self.player.is_playing:
            await self.player.play(track)
            return 0

        self.queue.append(track)
        return len(self.queue)

    async def skip(self) -> Track | None:
        """Skip current track. Returns next track or None."""
        if self.queue:
            next_track = self.queue.popleft()
            await self.player.play(next_track)
            return next_track
        else:
            await self.player.stop()
            return None

    async def stop(self) -> None:
        """Stop everything — clear queue, leave VC."""
        self.queue.clear()
        self.autoplay_enabled = False
        await self.player.stop()

    async def pause(self) -> None:
        await self.player.pause()

    async def resume(self) -> None:
        await self.player.resume()

    async def _on_track_end(self, chat_id: int) -> None:
        """Callback when a track finishes. Play next or stop."""
        if self.queue:
            next_track = self.queue.popleft()
            await self.player.play(next_track)
            log.info("Auto-next: %s in %d", next_track.title, chat_id)
        else:
            log.info("Queue empty in %d, stopping.", chat_id)
            await self.player.stop()
            # TODO: autoplay logic (Phase 5)
