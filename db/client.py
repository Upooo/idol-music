"""MongoDB client \u2014 async connection via Motor."""
from __future__ import annotations

import logging
from typing import Optional

from config import config

log = logging.getLogger(__name__)

_client = None
_db = None


async def connect() -> None:
    """Connect to MongoDB. No-op if MONGO_URI is not set."""
    global _client, _db
    if not config.mongo_uri:
        log.info("MONGO_URI not set \u2014 database features disabled.")
        return
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        _client = AsyncIOMotorClient(config.mongo_uri, serverSelectionTimeoutMS=5000)
        await _client.admin.command("ping")
        _db = _client.get_default_database(default="idol_music")
        log.info("MongoDB connected: %s", _db.name)
    except Exception as exc:
        log.error("MongoDB connection failed: %s", exc)
        _client = None
        _db = None


async def disconnect() -> None:
    """Close the MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        log.info("MongoDB disconnected.")


def get_db():
    """Get the database instance, or None if not connected."""
    return _db


def is_connected() -> bool:
    return _db is not None
