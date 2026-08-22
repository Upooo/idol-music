"""MusicSession — one independent session per group.

Manual requests have priority over autoplay.
Max 5 pending manual requests; reaching the limit disables autoplay.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from pytgcalls import PyTgCalls

from music.player import Player
from music.queue import MusicQueue, QueueFull
from music.track import Track

log = logging.getLogger(__name__)

# Max consecutive autoplay failures before disabling
AUTOPLAY_MAX_FAILURES = 3
MAX_MANUAL_QUEUE = 5


class MusicSession:
    def __init__(self, chat_id: int, calls: "PyTgCalls") -> None:
        self.chat_id = chat_id
        self.queue = MusicQueue(max_size=MAX_MANUAL_QUEUE)
        self.player = Player(
            chat_id=chat_id,
            calls=calls,
            on_track_end=self._on_track_end,
        )
        self.autoplay_enabled = False
        self._autoplay_failures = 0
        self._last_title: Optional[str] = None
        self._processing_end = False

    # ------------------------------------------------------------------
    # Public API used by handlers
    # ------------------------------------------------------------------

    async def add_and_play(self, track: Track) -> int:
        """Add manual track. Returns 0 if started now, else 1-based queue position.

        Raises QueueFull when the manual queue is at the limit (also disables autoplay).
        """
        if not self.player.is_playing:
            await self.player.play(track)
            self._last_title = track.title
            return 0

        if await self.queue.is_full():
            was = self.autoplay_enabled
            self.autoplay_enabled = False
            msg = f"Manual queue is full (max {MAX_MANUAL_QUEUE})."
            if was:
                msg += " Autoplay has been disabled."
            raise QueueFull(msg)

        return await self.queue.put(track)

    async def skip(self) -> Optional[Track]:
        """Skip current track; play next manual or autoplay or stop."""
        next_track = await self.queue.get()
        if next_track is not None:
            await self.player.play(next_track)
            self._last_title = next_track.title
            return next_track

        if self.autoplay_enabled:
            track = await self._try_autoplay()
            if track is not None:
                return track

        await self.player.stop()
        return None

    async def stop(self) -> None:
        """Full reset: clear queue, disable autoplay, leave VC."""
        await self.queue.clear()
        self.autoplay_enabled = False
        self._autoplay_failures = 0
        self._last_title = None
        await self.player.stop()
        log.info("Session stopped/reset for chat %s", self.chat_id)

    async def pause(self) -> bool:
        if not self.player.is_playing or self.player.is_paused:
            return False
        await self.player.pause()
        return True

    async def resume(self) -> bool:
        if not self.player.is_paused:
            return False
        await self.player.resume()
        return True

    async def enable_autoplay(self) -> bool:
        """Enable autoplay for this session. Returns True if newly enabled."""
        if self.autoplay_enabled:
            return False
        self.autoplay_enabled = True
        self._autoplay_failures = 0
        log.info("Autoplay enabled for chat %s", self.chat_id)
        if not self.player.is_playing:
            await self._try_autoplay()
        return True

    @property
    def current(self) -> Optional[Track]:
        return self.player.current

    @property
    def is_active(self) -> bool:
        return self.player.is_playing or self.player.is_paused

    # ------------------------------------------------------------------
    # Stream-end / autoplay internals
    # ------------------------------------------------------------------

    async def _on_track_end(self, chat_id: int) -> None:
        if self._processing_end:
            return
        self._processing_end = True
        try:
            log.info("Track ended in %s — advancing", chat_id)
            next_manual = await self.queue.get()
            if next_manual is not None:
                await self.player.play(next_manual)
                self._last_title = next_manual.title
                return

            if self.autoplay_enabled:
                track = await self._try_autoplay()
                if track is not None:
                    return

            log.info("Nothing left in %s — stopping", chat_id)
            await self.player.stop()
        finally:
            self._processing_end = False

    async def _try_autoplay(self) -> Optional[Track]:
        """Search and play an autoplay track. Disables autoplay after repeated failures."""
        # Lazy import to avoid circular deps; source may not exist yet during early steps
        try:
            from music.source import search_autoplay
        except ImportError:
            log.warning("music.source not available — autoplay skipped")
            self.autoplay_enabled = False
            await self.player.stop()
            return None

        seed = self._last_title or "music"
        track = await search_autoplay(seed)
        if track is None:
            self._autoplay_failures += 1
            log.warning(
                "Autoplay failure %s/%s in %s",
                self._autoplay_failures,
                AUTOPLAY_MAX_FAILURES,
                self.chat_id,
            )
            if self._autoplay_failures >= AUTOPLAY_MAX_FAILURES:
                self.autoplay_enabled = False
                await self.player.stop()
            return None

        self._autoplay_failures = 0
        try:
            await self.player.play(track)
            self._last_title = track.title
            return track
        except Exception as exc:
            log.error("Failed to play autoplay track: %s", exc)
            self._autoplay_failures += 1
            if self._autoplay_failures >= AUTOPLAY_MAX_FAILURES:
                self.autoplay_enabled = False
            await self.player.stop()
            return None
