"""yt-dlp music source — isolated from the rest of the engine."""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

import yt_dlp

from music.track import Track

log = logging.getLogger(__name__)

_COOKIES = Path(__file__).resolve().parent.parent / "cookies.txt"

_YDL_OPTS = {
    "format": "bestaudio/best/18",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "default_search": "ytsearch1",
    "extract_flat": False,
    "geo_bypass": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "no_color": True,
    "socket_timeout": 25,
    "retries": 3,
    # Required for current YouTube JS challenge solving
    "remote_components": {"ejs:github"},
    "extractor_args": {
        "youtube": {
            "player_client": ["web", "tv"],
        }
    },
}

if _COOKIES.is_file():
    _YDL_OPTS["cookiefile"] = str(_COOKIES)


class SourceError(Exception):
    pass


class TrackNotFound(SourceError):
    pass


class ExtractionFailed(SourceError):
    pass


def _extract(query: str) -> Optional[dict]:
    with yt_dlp.YoutubeDL(_YDL_OPTS) as ydl:
        return ydl.extract_info(query, download=False)


async def search(
    query: str,
    requester_id: int = 0,
    requester_name: str = "",
) -> Track:
    query = (query or "").strip()
    if not query:
        raise TrackNotFound("Empty query")

    loop = asyncio.get_event_loop()
    try:
        info = await loop.run_in_executor(None, _extract, query)
    except Exception as exc:
        log.warning("yt-dlp failed for %r: %s", query, exc)
        raise ExtractionFailed(str(exc) or "Extraction failed") from exc

    if not info:
        raise TrackNotFound(f"No results for: {query}")

    if "entries" in info:
        entries = [e for e in (info.get("entries") or []) if e]
        if not entries:
            raise TrackNotFound(f"No results for: {query}")
        info = entries[0]

    title = info.get("title") or info.get("fulltitle") or "Unknown"
    webpage_url = (
        info.get("webpage_url")
        or info.get("original_url")
        or info.get("url")
        or query
    )
    stream_url = info.get("url") or webpage_url

    duration = info.get("duration")
    try:
        duration = int(duration) if duration is not None else 0
    except (TypeError, ValueError):
        duration = 0

    thumbnail = ""
    thumbs = info.get("thumbnails") or []
    if thumbs:
        thumbnail = thumbs[-1].get("url") or ""
    elif info.get("thumbnail"):
        thumbnail = info["thumbnail"]

    track = Track(
        title=title,
        url=stream_url,
        duration=duration,
        thumbnail=thumbnail,
        requester_id=requester_id,
        requester_name=requester_name,
        source="youtube",
        is_autoplay=False,
    )
    log.info("Track found: %s", track.title)
    return track


async def search_autoplay(seed_title: str) -> Optional[Track]:
    query = f"{seed_title} mix" if seed_title else "popular music"
    try:
        track = await search(query)
        track.is_autoplay = True
        track.requester_name = "Autoplay"
        track.requester_id = 0
        track.source = "autoplay"
        return track
    except SourceError as exc:
        log.warning("Autoplay search failed for %r: %s", seed_title, exc)
        return None
