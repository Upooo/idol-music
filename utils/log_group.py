"""Telegram log group \u2014 send operational messages to a designated group."""
from __future__ import annotations

import logging
from typing import Optional

from config import config

log = logging.getLogger(__name__)

_bot = None


def init(bot) -> None:
    """Initialize with the bot client."""
    global _bot
    _bot = bot


async def send(text: str) -> None:
    """Send a message to the log group. No-op if LOG_GROUP_ID is not set."""
    if not config.log_group_id or _bot is None:
        return
    try:
        await _bot.send_message(config.log_group_id, text)
    except Exception as exc:
        log.warning("Failed to send log to group: %s", exc)
