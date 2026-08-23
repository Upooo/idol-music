"""Database models and CRUD operations."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from db.client import get_db

log = logging.getLogger(__name__)

_DEFAULT_SETTINGS = {
    "lang": "en",
}


# --- Group Settings ---

async def get_group_settings(chat_id: int) -> dict:
    """Get settings for a group, with defaults."""
    db = get_db()
    if db is None:
        return dict(_DEFAULT_SETTINGS)
    coll = db["group_settings"]
    doc = await coll.find_one({"_id": chat_id})
    if doc is None:
        return dict(_DEFAULT_SETTINGS)
    result = dict(_DEFAULT_SETTINGS)
    result.update({k: v for k, v in doc.items() if k != "_id"})
    return result


async def set_group_setting(chat_id: int, key: str, value) -> None:
    """Set a single setting for a group."""
    db = get_db()
    if db is None:
        return
    coll = db["group_settings"]
    await coll.update_one(
        {"_id": chat_id},
        {"$set": {key: value}},
        upsert=True,
    )


async def get_group_lang(chat_id: int) -> str:
    settings = await get_group_settings(chat_id)
    return settings.get("lang", "en")


async def set_group_lang(chat_id: int, lang: str) -> None:
    await set_group_setting(chat_id, "lang", lang)


# --- Play History ---

async def log_play(chat_id: int, track) -> None:
    """Log a track play to MongoDB."""
    db = get_db()
    if db is None:
        return
    coll = db["play_history"]
    await coll.insert_one({
        "chat_id": chat_id,
        "title": track.title,
        "url": track.url,
        "duration": track.duration,
        "requester_id": track.requester_id,
        "requester_name": track.requester_name,
        "source": track.source,
        "is_autoplay": track.is_autoplay,
        "played_at": datetime.now(timezone.utc),
    })


async def get_play_count(chat_id: int = None) -> int:
    """Get total play count, optionally filtered by chat."""
    db = get_db()
    if db is None:
        return 0
    coll = db["play_history"]
    query = {"chat_id": chat_id} if chat_id else {}
    return await coll.count_documents(query)


# --- Active Sessions ---

async def session_join(chat_id: int) -> None:
    """Record that bot joined a VC."""
    db = get_db()
    if db is None:
        return
    coll = db["active_sessions"]
    await coll.update_one(
        {"_id": chat_id},
        {"$set": {"joined_at": datetime.now(timezone.utc)}},
        upsert=True,
    )


async def session_leave(chat_id: int) -> None:
    """Record that bot left a VC."""
    db = get_db()
    if db is None:
        return
    coll = db["active_sessions"]
    await coll.delete_one({"_id": chat_id})


async def clear_stale_sessions() -> None:
    """Clear all active sessions on startup (stale from previous run)."""
    db = get_db()
    if db is None:
        return
    coll = db["active_sessions"]
    result = await coll.delete_many({})
    if result.deleted_count:
        log.info("Cleared %d stale sessions from DB", result.deleted_count)


async def get_active_session_count() -> int:
    db = get_db()
    if db is None:
        return 0
    return await db["active_sessions"].count_documents({})
