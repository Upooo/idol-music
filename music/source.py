"""yt-dlp music source — isolated from the rest of the engine."""
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

# Autoplay uses ytsearch5 to get multiple candidates
_YDL_AUTOPLAY_OPTS = {**_YDL_BASE_OPTS, "default_search": "ytsearch5"}

# Query templates for autoplay variety
_AUTOPLAY_QUERIES = [
    "{title} music",
    "songs like {title}",
    "{title} similar songs",
    "music mix {title}",
    "{title} related",
    "{title} recommended",
]


class SourceError(Exception):
    pass


class TrackNotFound(SourceError):
    pass


class ExtractionFailed(SourceError):
    pass


def _extract(query: str, opts: dict | None = None) -> Optional[dict]:
    use_opts = opts or _YDL_BASE_OPTS
    with yt_dlp.YoutubeDL(use_opts) as ydl:
        return ydl.extract_info(query, download=False)


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
        info = await loop.run_in_executor(None, _extract, query, None)
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
    """Search for an autoplay track, avoiding already-played URLs."""
    played = played_urls or set()

    template = random.choice(_AUTOPLAY_QUERIES)
    query = template.format(title=seed_title) if seed_title else "popular music mix"

    loop = asyncio.get_running_loop()
    try:
        info = await loop.run_in_executor(None, _extract, query, _YDL_AUTOPLAY_OPTS)
    except Exception as exc:
        log.warning("Autoplay search failed for %r: %s", seed_title, exc)
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

    # Shuffle and pick the first one not yet played
    random.shuffle(candidates)
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
            log.info("Autoplay track found: %s", track.title)
            return track
        except Exception as exc:
            log.warning("Failed to build autoplay track: %s", exc)
            continue

    # All candidates already played — generic fallback
    fallback_queries = ["trending music", "top hits", "new music mix", "popular songs"]
    fallback_q = random.choice(fallback_queries)
    try:
        info = await loop.run_in_executor(
            None, _extract, fallback_q, _YDL_AUTOPLAY_OPTS
        )
    except Exception:
        return None

    if not info:
        return None

    entries = []
    if "entries" in info:
        entries = [e for e in (info.get("entries") or []) if e]
    else:
        entries = [info]

    random.shuffle(entries)
    for entry in entries:
        url = entry.get("url") or entry.get("webpage_url") or ""
        if url and url in played:
            continue
        try:
            track = _build_track(entry)
            track.is_autoplay = True
            track.requester_name = "Autoplay"
            track.requester_id = 0
            track.source = "autoplay"
            return track
        except Exception:
            continue

    return None
