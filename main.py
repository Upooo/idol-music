"""IDOL Music — Entry Point.
Starts both Pyrogram clients (bot + assistant) and PyTgCalls.
"""
from __future__ import annotations

import asyncio
import logging

from pytgcalls import filters as pf
from pytgcalls.types import ChatUpdate, StreamEnded

from bot.clients import create_bot, create_assistant, create_calls
from music.manager import SessionManager
from handlers import system, music, developer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
log = logging.getLogger(__name__)


async def main() -> None:
    assistant = create_assistant()
    bot = create_bot()
    calls = create_calls(assistant)
    sessions = SessionManager(calls)

    # --- PyTgCalls event handlers ---
    @calls.on_update(filters=pf.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT))
    async def on_vc_closed(client, update: ChatUpdate):
        log.info("VC closed in %d", update.chat_id)
        sess = sessions.get(update.chat_id)
        await sess.stop()
        sessions.remove(update.chat_id)

    @calls.on_update(filters=pf.stream_end())
    async def on_stream_end(client, update: StreamEnded):
        log.info("Stream ended in %d", update.chat_id)
        sess = sessions.get(update.chat_id)
        await sess.player.handle_stream_end()

    # --- Pyrogram bot handlers ---
    system.register(bot)
    music.register(bot, sessions)
    developer.register(bot, sessions)

    # --- Startup sequence ---
    log.info("Starting IDOL Music v1.0.0...")
    try:
        await assistant.start()
        log.info("Assistant started.")
    except Exception as e:
        log.error("Failed to start assistant: %s", e)
        raise

    try:
        await bot.start()
        me = await bot.get_me()
        log.info("Bot started as @%s (id=%d)", me.username, me.id)
    except Exception as e:
        log.error("Failed to start bot: %s", e)
        await assistant.stop()
        raise

    try:
        await calls.start()
        log.info("PyTgCalls started.")
    except Exception as e:
        log.error("Failed to start PyTgCalls: %s", e)
        await bot.stop()
        await assistant.stop()
        raise

    log.info("IDOL Music is running.")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
