"""yt-dlp music source \u2014 isolated from the rest of the engine."""
from __future__ import annotations

import asyncio
import logging
import random
from pathlib import Path
from typing import Optional, Set

import yt_dlp

from music.track import Track

log = logging.getLogger(__name__)

_COOKIES = Path(__file__).resolve().parent.parent / "cookies.txt"

_YDL_BASE_OPTS = {
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
    "remote_components": {"ejs:github"},
    "extractor_args": {
        "youtube": {
            "player_client": ["web", "tv"],
        }
    },
}

if _COOKIES.is_file():
    _YDL_BASE_OPTS["cookiefile"] = str(_COOKIES)

_YDL_AUTOPLAY_OPTS = {**_YDL_BASE_OPTS, "default_search": "ytsearch3"}

AUTOPLAY_MIN_DURATION = 120
AUTOPLAY_MAX_DURATION = 600


class SourceError(Exception):
    pass


class TrackNotFound(SourceError):
    pass


class ExtractionFailed(SourceError):
    pass


def _extract_with_retry(query: str, opts: dict | None = None) -> Optional[dict]:
    """Extract with one retry on 'page needs to be reloaded' errors."""
    use_opts = opts or _YDL_BASE_OPTS
    for attempt in range(2):
        try:
            with yt_dlp.YoutubeDL(use_opts) as ydl:
                return ydl.extract_info(query, download=False)
        except Exception as exc:
            err_str = str(exc).lower()
            if "page needs to be reloaded" in err_str and attempt == 0:
                log.warning("yt-dlp page reload error, retrying: %s", query)
                continue
            raise
    return None


def _build_track(info: dict, requester_id: int = 0, requester_name: str = "") -> Track:
    """Build a Track from yt-dlp info dict."""
    title = info.get("title") or info.get("fulltitle") or "Unknown"
    webpage_url = (
        info.get("webpage_url")
        or info.get("original_url")
        or info.get("url")
        or ""
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

    return Track(
        title=title,
        url=stream_url,
        duration=duration,
        thumbnail=thumbnail,
        requester_id=requester_id,
        requester_name=requester_name,
        source="youtube",
        is_autoplay=False,
    )


async def search(
    query: str,
    requester_id: int = 0,
    requester_name: str = "",
) -> Track:
    query = (query or "").strip()
    if not query:
        raise TrackNotFound("Empty query")

    loop = asyncio.get_running_loop()
    try:
        info = await loop.run_in_executor(None, _extract_with_retry, query, None)
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

    track = _build_track(info, requester_id, requester_name)
    log.info("Track found: %s", track.title)
    return track


async def search_autoplay(
    seed_title: str,
    played_urls: Set[str] | None = None,
) -> Optional[Track]:
    """Search for a random autoplay track using the artist pool."""
    played = played_urls or set()

    from music.artists import get_random_query

    query, artist = get_random_query()
    log.info("Autoplay searching: %s (artist: %s)", query, artist)

    loop = asyncio.get_running_loop()
    try:
        info = await loop.run_in_executor(None, _extract_with_retry, query, _YDL_AUTOPLAY_OPTS)
    except Exception as exc:
        log.warning("Autoplay search failed for %r: %s", query, exc)
        return None

    if not info:
        return None

    candidates = []
    if "entries" in info:
        candidates = [e for e in (info.get("entries") or []) if e]
    else:
        candidates = [info]

    if not candidates:
        return None

    # Filter by duration (2-10 min) and not already played
    random.shuffle(candidates)
    for entry in candidates:
        url = entry.get("url") or entry.get("webpage_url") or ""
        if url and url in played:
            continue
        dur = entry.get("duration")
        try:
            dur = int(dur) if dur is not None else 0
        except (TypeError, ValueError):
            dur = 0
        if dur < AUTOPLAY_MIN_DURATION or dur > AUTOPLAY_MAX_DURATION:
            continue
        try:
            track = _build_track(entry)
            track.is_autoplay = True
            track.requester_name = "Autoplay"
            track.requester_id = 0
            track.source = "autoplay"
            log.info("Autoplay track: %s (%ds) [%s]", track.title, dur, artist)
            return track
        except Exception as exc:
            log.warning("Failed to build autoplay track: %s", exc)
            continue

    # No candidate with duration filter — try without
    for entry in candidates:
        url = entry.get("url") or entry.get("webpage_url") or ""
        if url and url in played:
            continue
        try:
            track = _build_track(entry)
            track.is_autoplay = True
            track.requester_name = "Autoplay"
            track.requester_id = 0
            track.source = "autoplay"
            log.info("Autoplay track (no dur filter): %s [%s]", track.title, artist)
            return track
        except Exception:
            continue

    return None
