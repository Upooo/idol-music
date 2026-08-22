"""FIFO queue for manual user requests only.

Autoplay tracks are never stored here.
Async-safe via asyncio.Lock.
"""
from __future__ import annotations

import asyncio
from collections import deque
from typing import Deque, List, Optional

from music.track import Track


class QueueFull(Exception):
    """Raised when the manual request queue has reached its limit."""


class MusicQueue:
    def __init__(self, max_size: int = 5) -> None:
        self._items: Deque[Track] = deque()
        self._lock = asyncio.Lock()
        self.max_size = max_size

    async def put(self, track: Track) -> int:
        """Append track. Returns 1-based position. Raises QueueFull if full."""
        async with self._lock:
            if len(self._items) >= self.max_size:
                raise QueueFull(f"Manual queue is full (max {self.max_size})")
            self._items.append(track)
            return len(self._items)

    async def get(self) -> Optional[Track]:
        async with self._lock:
            if not self._items:
                return None
            return self._items.popleft()

    async def peek(self) -> Optional[Track]:
        async with self._lock:
            return self._items[0] if self._items else None

    async def clear(self) -> None:
        async with self._lock:
            self._items.clear()

    async def size(self) -> int:
        async with self._lock:
            return len(self._items)

    async def is_empty(self) -> bool:
        async with self._lock:
            return len(self._items) == 0

    async def is_full(self) -> bool:
        async with self._lock:
            return len(self._items) >= self.max_size

    async def snapshot(self) -> List[Track]:
        async with self._lock:
            return list(self._items)
