"""Database models and CRUD operations."""
from __future__ import annotations

import logging

from db.client import get_db

log = logging.getLogger(__name__)

_DEFAULT_SETTINGS = {
    "lang": "en",
}


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
    """Get the language setting for a group."""
    settings = await get_group_settings(chat_id)
    return settings.get("lang", "en")


async def set_group_lang(chat_id: int, lang: str) -> None:
    """Set the language for a group."""
    await set_group_setting(chat_id, "lang", lang)
