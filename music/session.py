"""MusicSession \u2014 one independent session per group.

Manual requests have priority over autoplay.
Max 5 pending manual requests; reaching the limit disables autoplay.
Auto-leave after 5 minutes with no listeners.
Bot leaves VC when queue is empty and autoplay is off.
"""
from __future__ import annotations

import asyncio
import logging
import math
import time
from typing import TYPE_CHECKING, Optional, Set, Callable, Awaitable

if TYPE_CHECKING:
    from pytgcalls import PyTgCalls
    from pyrogram import Client

from music.player import Player
from music.queue import MusicQueue, QueueFull
from music.track import Track
from music.votes import VoteTracker

log = logging.getLogger(__name__)

AUTOPLAY_MAX_FAILURES = 3
MAX_MANUAL_QUEUE = 5
AUTO_LEAVE_TIMEOUT = 300
AUTO_LEAVE_CHECK_INTERVAL = 60
DEFAULT_VOTE_THRESHOLD = 2


class MusicSession:
    def __init__(
        self,
        chat_id: int,
        calls: "PyTgCalls",
        assistant: "Optional[Client]" = None,
        on_auto_leave: "Optional[Callable[[int], Awaitable[None]]]" = None,
    ) -> None:
        self.chat_id = chat_id
        self.queue = MusicQueue(max_size=MAX_MANUAL_QUEUE)
        self.player = Player(
            chat_id=chat_id,
            calls=calls,
            on_track_end=self._on_track_end,
        )
        self._assistant = assistant
        self._on_auto_leave = on_auto_leave
        self.autoplay_enabled = False
        self._autoplay_failures = 0
        self._last_title: Optional[str] = None
        self._end_lock = asyncio.Lock()
        self._play_history: Set[str] = set()
        self.votes = VoteTracker()

        self._no_listeners_since: Optional[float] = None
        self._auto_leave_task: Optional[asyncio.Task] = None

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    async def add_and_play(self, track: Track) -> int:
        if not self.player.is_active:
            await self.player.play(track)
            self._last_title = track.title
            self._record_play(track)
            self.votes.clear(self.chat_id)
            self._start_auto_leave_checker()
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
        self.votes.clear(self.chat_id)
        next_track = await self.queue.get()
        if next_track is not None:
            await self.player.play(next_track)
            self._last_title = next_track.title
            self._record_play(next_track)
            return next_track

        if self.autoplay_enabled:
            track = await self._try_autoplay()
            if track is not None:
                return track

        await self.player.stop()
        return None

    async def stop(self) -> None:
        self._stop_auto_leave_checker()
        await self.queue.clear()
        self.autoplay_enabled = False
        self._autoplay_failures = 0
        self._last_title = None
        self._play_history.clear()
        self.votes.clear(self.chat_id)
        await self.player.stop()
        log.info("Session stopped/reset for chat %s", self.chat_id)

    async def pause(self) -> bool:
        if not self.player.is_playing:
            return False
        await self.player.pause()
        return self.player.is_paused

    async def resume(self) -> bool:
        if not self.player.is_paused:
            return False
        await self.player.resume()
        return self.player.is_playing

    async def enable_autoplay(self) -> bool:
        if self.autoplay_enabled:
            return False
        self.autoplay_enabled = True
        self._autoplay_failures = 0
        log.info("Autoplay enabled for chat %s", self.chat_id)
        if not self.player.is_active:
            await self._try_autoplay()
            if self.player.is_active:
                self._start_auto_leave_checker()
        return True

    @property
    def current(self) -> Optional[Track]:
        return self.player.current

    @property
    def is_active(self) -> bool:
        return self.player.is_active

    # ----------------------------------------------------------------
    # Vote skip helpers
    # ----------------------------------------------------------------

    async def get_skip_threshold(self) -> int:
        count = await self._get_vc_count()
        if count <= 0:
            return DEFAULT_VOTE_THRESHOLD
        return max(1, math.ceil(count / 2))

    async def _get_vc_count(self) -> int:
        if self._assistant is None:
            return -1
        try:
            from utils.vc import get_vc_participant_count
            return await get_vc_participant_count(self._assistant, self.chat_id)
        except Exception:
            return -1

    # ----------------------------------------------------------------
    # Auto-leave checker
    # ----------------------------------------------------------------

    def _start_auto_leave_checker(self) -> None:
        if self._auto_leave_task is not None and not self._auto_leave_task.done():
            return
        self._no_listeners_since = None
        self._auto_leave_task = asyncio.create_task(self._auto_leave_loop())

    def _stop_auto_leave_checker(self) -> None:
        if self._auto_leave_task is not None:
            self._auto_leave_task.cancel()
            self._auto_leave_task = None
        self._no_listeners_since = None

    async def _auto_leave_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(AUTO_LEAVE_CHECK_INTERVAL)
                if not self.player.is_active:
                    break

                count = await self._get_vc_count()
                if count == -1:
                    self._no_listeners_since = None
                    continue

                if count == 0:
                    if self._no_listeners_since is None:
                        self._no_listeners_since = time.time()
                        log.info("No listeners in %s \u2014 timer started", self.chat_id)
                    elif time.time() - self._no_listeners_since >= AUTO_LEAVE_TIMEOUT:
                        log.info("Auto-leaving %s (no listeners for %ds)",
                                 self.chat_id, AUTO_LEAVE_TIMEOUT)
                        await self.stop()
                        if self._on_auto_leave:
                            await self._on_auto_leave(self.chat_id)
                        break
                else:
                    if self._no_listeners_since is not None:
                        log.info("Listeners back in %s \u2014 timer reset", self.chat_id)
                    self._no_listeners_since = None
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            log.error("Auto-leave loop error in %s: %s", self.chat_id, exc)

    # ----------------------------------------------------------------
    # Stream-end / autoplay internals
    # ----------------------------------------------------------------

    def _record_play(self, track: Track) -> None:
        if track.url:
            self._play_history.add(track.url)
        if len(self._play_history) > 50:
            keep = list(self._play_history)[-30:]
            self._play_history = set(keep)

    async def _on_track_end(self, chat_id: int) -> None:
        async with self._end_lock:
            self.votes.clear(self.chat_id)
            log.info("Track ended in %s \u2014 advancing", chat_id)
            next_manual = await self.queue.get()
            if next_manual is not None:
                await self.player.play(next_manual)
                self._last_title = next_manual.title
                self._record_play(next_manual)
                return

            if self.autoplay_enabled:
                track = await self._try_autoplay()
                if track is not None:
                    return

            # Nothing left \u2014 leave VC
            log.info("Nothing left in %s \u2014 leaving VC", chat_id)
            await self.player.stop()
            if self._on_auto_leave:
                await self._on_auto_leave(chat_id)

    async def _try_autoplay(self) -> Optional[Track]:
        try:
            from music.source import search_autoplay
        except ImportError:
            log.warning("music.source not available \u2014 autoplay skipped")
            self.autoplay_enabled = False
            await self.player.stop()
            return None

        seed = self._last_title or "music"
        track = await search_autoplay(seed, played_urls=self._play_history)
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
            self._record_play(track)
            return track
        except Exception as exc:
            log.error("Failed to play autoplay track: %s", exc)
            self._autoplay_failures += 1
            if self._autoplay_failures >= AUTOPLAY_MAX_FAILURES:
                self.autoplay_enabled = False
            await self.player.stop()
            return None
