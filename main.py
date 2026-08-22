"""IDOL Music — Entry Point.

Starts both Pyrogram clients (bot + assistant) and PyTgCalls.
"""

import asyncio
import logging

from pyrogram import Client, filters as pyro_filters
from pyrogram.types import Message
from pytgcalls import filters as pf
from pytgcalls.types import ChatUpdate, StreamEnded, Update

from bot.clients import bot, assistant, calls
from music.manager import SessionManager
from handlers import system, music

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
log = logging.getLogger(__name__)


async def main() -> None:
    sessions = SessionManager(calls)

    # Handle voice-chat closure (e.g. VC ended by an admin)
    @calls.on_update(filters=pf.chat_update(ChatUpdate.Status.CLOSED_VOICE_CHAT))
    async def on_vc_closed(client, update: ChatUpdate):
        log.info("VC closed in %d", update.chat_id)
        sess = sessions.get(update.chat_id)
        await sess.stop()
        sessions.remove(update.chat_id)

    # Handle stream-ended events (track finished playing)
    @calls.on_update(filters=pf.stream_end())
    async def on_stream_end(client, update: StreamEnded):
        chat_id = update.chat_id
        log.info("Stream ended in %d", chat_id)
        sess = sessions.get(chat_id)
        await sess.player.handle_stream_end()

    # Register handlers
    system.register(bot)
    music.register(bot, sessions)

    # DEBUG: catch-all handler to verify bot receives messages
    @bot.on_message(group=99)
    async def debug_all_messages(client: Client, message: Message):
        log.info(
            "[DEBUG] Received message: chat=%s type=%s text=%r from=%s",
            message.chat.id,
            message.chat.type,
            message.text,
            message.from_user.id if message.from_user else "N/A",
        )

    log.info("Starting IDOL Music...")

    # Start all clients
    await assistant.start()
    await bot.start()

    # Delete any stale webhook so polling works
    try:
        from pyrogram.raw.functions.bots import ResetBotCommands
        await bot.invoke(
            pyrogram.raw.functions.messages.DeleteHistory(
                peer=await bot.resolve_peer("me"),
                max_id=0,
                just_clear=False,
                revoke=False,
            )
        )
    except Exception:
        pass

    # Force-clear webhook via Bot API
    import aiohttp
    from config import config
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.telegram.org/bot{config.bot_token}/deleteWebhook"
            async with session.get(url) as resp:
                result = await resp.json()
                log.info("deleteWebhook result: %s", result)
    except Exception as e:
        log.warning("Failed to delete webhook: %s", e)

    await calls.start()

    log.info("IDOL Music is running.")

    # Keep alive
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
