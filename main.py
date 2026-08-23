"""IDOL Music — Entry Point.
Starts both Pyrogram clients (bot + assistant) and PyTgCalls.
"""
from __future__ import annotations

import asyncio
import logging
import traceback
from logging.handlers import RotatingFileHandler

from pytgcalls import filters as pf
from pytgcalls.types import StreamEnded

from bot.clients import create_bot, create_assistant, create_calls
from music.manager import SessionManager
from handlers import system, music, developer
from db import client as db_client
from db.models import get_group_lang, clear_stale_sessions
from utils import log_group
import strings

# --- Logging: console + file ---
_log_fmt = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
_file_handler = RotatingFileHandler(
    "idol_music.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8"
)
_file_handler.setFormatter(logging.Formatter(_log_fmt))

logging.basicConfig(
    level=logging.INFO,
    format=_log_fmt,
    handlers=[
        logging.StreamHandler(),
        _file_handler,
    ],
)
log = logging.getLogger(__name__)


async def main() -> None:
    assistant = create_assistant()
    bot = create_bot()
    calls = create_calls(assistant)

    # --- MongoDB ---
    await db_client.connect()

    # --- Global error handler for log group ---
    async def _global_error_handler(client, update, err):
        tb = traceback.format_exception(type(err), err, err.__traceback__)
        tb_str = "".join(tb)[-1500:]  # truncate
        location = type(update).__name__ if update else "unknown"
        await log_group.send(
            strings.get("LOG_ERROR", "en", location=location, error=tb_str)
        )

    bot.on_error()(_global_error_handler)

    # Auto-leave / track-end callback
    async def on_auto_leave(chat_id: int) -> None:
        lang = await get_group_lang(chat_id)
        try:
            await bot.send_message(chat_id, strings.get("AUTO_LEAVE", lang))
        except Exception:
            pass
        await log_group.send(
            strings.get("LOG_SESSION_LEAVE", "en", chat_id=chat_id)
        )

    sessions = SessionManager(
        calls, assistant=assistant, on_auto_leave=on_auto_leave
    )

    # Stream end callback
    @calls.on_stream_end()
    async def on_stream_end(client, update: StreamEnded) -> None:
        chat_id = update.chat_id
        session = sessions.get_existing(chat_id)
        if session:
            await session.handle_track_end()

    # Participant change — update listener count
    @calls.on_participant()
    async def on_participant_change(client, update) -> None:
        chat_id = update.chat_id
        session = sessions.get_existing(chat_id)
        if session:
            session.update_listeners(update)

    # --- Register handlers ---
    system.register(bot, sessions)
    music.register(bot, sessions)
    developer.register(bot, sessions=sessions, assistant=assistant, calls=calls)

    # --- Start clients ---
    await assistant.start()
    await bot.start()
    await calls.start()

    # Init log group
    log_group.init(bot)

    # Clear stale sessions from DB
    await clear_stale_sessions()

    # --- Startup notification ---
    me = await bot.get_me()
    mongo_status = "Connected" if db_client.is_connected() else "Disabled"
    cookies_status = "Loaded" if _cookies_exist() else "Not found"
    startup_msg = strings.get(
        "LOG_STARTED", "en",
        username=me.username or "unknown",
        sessions=len(sessions),
        mongo=mongo_status,
        cookies=cookies_status,
    )
    await log_group.send(startup_msg)
    log.info("IDOL Music started as @%s", me.username)

    await asyncio.Event().wait()


def _cookies_exist() -> bool:
    from pathlib import Path
    return (Path(__file__).parent / "cookies.txt").is_file()


if __name__ == "__main__":
    asyncio.run(main())
