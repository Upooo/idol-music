"""MusicSession — one independent session per group.

Manual requests have priority over autoplay.
Max 5 pending manual requests; reaching the limit disables autoplay.
Auto-leave after 5 minutes with no listeners.
Pauses when 0 listeners, resumes when someone joins back.
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
        assistant: "Client" = None,
        on_auto_leave: Optional[Callable[[int], Awaitable[None]]] = None,
    ) -> None:
        self.chat_id = chat_id
        self._calls = calls
        self._assistant = assistant
        self.player = Player(chat_id, calls)
        self.queue = MusicQueue(max_size=MAX_MANUAL_QUEUE)
        self.votes = VoteTracker()
        self.autoplay = False
        self._autoplay_failures = 0
        self._played_artists: Set[str] = set()
        self._on_auto_leave = on_auto_leave
        self._auto_leave_task: Optional[asyncio.Task] = None
        self._no_listener_since: Optional[float] = None
        self._end_lock = asyncio.Lock()
        self._paused_by_listener_check = False
        self._listener_count = -1  # unknown

    # --- Public API ---

    async def add_and_play(self, track: Track) -> int:
        """Add track. Returns 0 if playing now, else queue position."""
        if not self.player.is_active:
            await self.player.play(track)
            self.votes.clear(self.chat_id)
            self._start_auto_leave_checker()
            await self._db_session_join()
            await self._db_log_play(track)
            return 0
        pos = await self.queue.put(track)
        return pos

    async def skip(self) -> Optional[Track]:
        self.votes.clear(self.chat_id)
        nxt = await self.queue.pop()
        if nxt:
            await self.player.play(nxt)
            await self._db_log_play(nxt)
            return nxt
        if self.autoplay:
            ap = await self._get_autoplay_track()
            if ap:
                await self.player.play(ap)
                await self._db_log_play(ap)
                return ap
        await self.stop()
        return None

    async def pause(self) -> None:
        await self.player.pause()

    async def resume(self) -> None:
        self._paused_by_listener_check = False
        await self.player.resume()

    async def stop(self) -> None:
        self._stop_auto_leave_checker()
        await self.player.stop()
        await self.queue.clear()
        self.votes.clear(self.chat_id)
        self.autoplay = False
        self._autoplay_failures = 0
        self._played_artists.clear()
        self._paused_by_listener_check = False
        await self._db_session_leave()

    async def handle_track_end(self) -> None:
        """Called from main.py on stream_end event."""
        async with self._end_lock:
            await self.player.handle_stream_end()
            nxt = await self.queue.pop()
            if nxt:
                await self.player.play(nxt)
                self.votes.clear(self.chat_id)
                await self._db_log_play(nxt)
                return
            if self.autoplay:
                ap = await self._get_autoplay_track()
                if ap:
                    await self.player.play(ap)
                    self.votes.clear(self.chat_id)
                    await self._db_log_play(ap)
                    return
            await self.stop()

    def update_listeners(self, update) -> None:
        """Called on PyTgCalls participant change."""
        try:
            count = getattr(update, 'participant_count', -1)
            if count >= 0:
                # subtract 1 for the assistant itself
                self._listener_count = max(0, count - 1)
        except Exception:
            pass

    # --- Listener-based pause/resume ---

    def _start_auto_leave_checker(self) -> None:
        self._stop_auto_leave_checker()
        self._no_listener_since = None
        self._auto_leave_task = asyncio.create_task(self._auto_leave_loop())

    def _stop_auto_leave_checker(self) -> None:
        if self._auto_leave_task and not self._auto_leave_task.done():
            self._auto_leave_task.cancel()
        self._auto_leave_task = None
        self._no_listener_since = None

    async def _auto_leave_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(AUTO_LEAVE_CHECK_INTERVAL)
                if not self.player.is_active:
                    continue

                count = await self._get_listener_count()

                if count == 0:
                    if self._no_listener_since is None:
                        self._no_listener_since = time.time()
                        # Pause playback when no listeners
                        if self.player.state.value == "playing" and not self._paused_by_listener_check:
                            await self.player.pause()
                            self._paused_by_listener_check = True
                            log.info("Paused in %d: no listeners", self.chat_id)

                    elapsed = time.time() - self._no_listener_since
                    if elapsed >= AUTO_LEAVE_TIMEOUT:
                        log.info("Auto-leaving %d after %ds no listeners", self.chat_id, int(elapsed))
                        if self._on_auto_leave:
                            await self._on_auto_leave(self.chat_id)
                        await self.stop()
                        return
                else:
                    # Listeners came back — resume if we paused
                    if self._paused_by_listener_check:
                        await self.player.resume()
                        self._paused_by_listener_check = False
                        log.info("Resumed in %d: listeners returned", self.chat_id)
                    self._no_listener_since = None

        except asyncio.CancelledError:
            pass
        except Exception as exc:
            log.exception("Auto-leave loop error in %d: %s", self.chat_id, exc)

    async def _get_listener_count(self) -> int:
        if self._listener_count >= 0:
            return self._listener_count
        # Fallback: use raw API
        if self._assistant:
            try:
                from utils.vc import get_vc_participant_count
                count = await get_vc_participant_count(self._assistant, self.chat_id)
                return count if count >= 0 else 0
            except Exception:
                pass
        return -1  # unknown

    # --- Autoplay ---

    async def _get_autoplay_track(self) -> Optional[Track]:
        if self._autoplay_failures >= AUTOPLAY_MAX_FAILURES:
            log.warning("Autoplay disabled in %d: too many failures", self.chat_id)
            self.autoplay = False
            return None
        try:
            from music.source import search
            from music.artists import get_random_query
            query, artist = get_random_query(self._played_artists)
            track = await search(query)
            if track:
                track.is_autoplay = True
                track.requester_name = "Autoplay"
                self._played_artists.add(artist)
                self._autoplay_failures = 0
                return track
        except Exception as exc:
            log.warning("Autoplay search failed in %d: %s", self.chat_id, exc)
        self._autoplay_failures += 1
        return None

    # --- MongoDB helpers ---

    async def _db_log_play(self, track: Track) -> None:
        try:
            from db.models import log_play
            await log_play(self.chat_id, track)
        except Exception as exc:
            log.debug("DB log_play failed: %s", exc)

    async def _db_session_join(self) -> None:
        try:
            from db.models import session_join
            await session_join(self.chat_id)
        except Exception as exc:
            log.debug("DB session_join failed: %s", exc)

    async def _db_session_leave(self) -> None:
        try:
            from db.models import session_leave
            await session_leave(self.chat_id)
        except Exception as exc:
            log.debug("DB session_leave failed: %s", exc)
