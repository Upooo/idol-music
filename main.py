"""IDOL Music — Entry Point (V1.1.0 Clean).

Slim wiring only. All logic lives in its own module.
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
from db.models import clear_stale_sessions
from utils import log_group
import strings

# --- Logging ---
_FMT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=_FMT,
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            "idol_music.log", maxBytes=5_000_000, backupCount=3, encoding="utf-8"
        ),
    ],
)
log = logging.getLogger(__name__)


def _cookies_exist() -> bool:
    from pathlib import Path
    return (Path(__file__).parent / "cookies.txt").is_file()


async def main() -> None:
    # --- Create clients ---
    assistant = create_assistant()
    bot = create_bot()
    calls = create_calls(assistant)

    # --- MongoDB ---
    await db_client.connect()

    # --- Auto-leave callback ---
    async def on_auto_leave(chat_id: int) -> None:
        from db.models import get_group_lang
        lang = await get_group_lang(chat_id)
        try:
            await bot.send_message(chat_id, strings.get("AUTO_LEAVE", lang))
        except Exception:
            pass
        await log_group.send(
            strings.get("LOG_SESSION_LEAVE", "en", chat_id=chat_id)
        )

    # --- Session manager ---
    sessions = SessionManager(calls, assistant=assistant, on_auto_leave=on_auto_leave)

    # --- Stream end (proven pattern) ---
    @calls.on_update(pf.stream_end)
    async def on_stream_end(client, update: StreamEnded) -> None:
        session = sessions.get_existing(update.chat_id)
        if session:
            await session.handle_track_end()

    # --- Error handler ---
    @bot.on_error()
    async def on_error(client, update, err):
        tb = "".join(traceback.format_exception(type(err), err, err.__traceback__))[-1500:]
        location = type(update).__name__ if update else "unknown"
        await log_group.send(strings.get("LOG_ERROR", "en", location=location, error=tb))

    # --- Register handlers ---
    system.register(bot, sessions)
    music.register(bot, sessions)
    developer.register(bot, sessions=sessions, assistant=assistant, calls=calls)

    # --- Start ---
    await assistant.start()
    await bot.start()
    await calls.start()
    log_group.init(bot)
    await clear_stale_sessions()

    # --- Startup log: bot ---
    me = await bot.get_me()
    await log_group.send(strings.get(
        "LOG_STARTED", "en",
        username=me.username or "unknown",
        sessions=len(sessions),
        mongo="Connected" if db_client.is_connected() else "Disabled",
        cookies="Loaded" if _cookies_exist() else "Not found",
    ))
    log.info("IDOL Music started as @%s", me.username)

    # --- Startup log: assistant ---
    try:
        ass_me = await assistant.get_me()
        await log_group.send(strings.get(
            "LOG_ASSISTANT_STARTED", "en",
            name=ass_me.first_name or "Assistant",
            user_id=ass_me.id,
        ))
    except Exception as exc:
        log.warning("Could not get assistant info: %s", exc)

    # --- Keep alive ---
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
