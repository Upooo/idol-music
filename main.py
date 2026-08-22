"""IDOL Music — Entry Point.

Starts both Pyrogram clients (bot + assistant) and PyTgCalls.
"""

import asyncio
import logging

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

    log.info("Starting IDOL Music...")

    # Start all clients
    await assistant.start()
    await bot.start()
    await calls.start()

    log.info("IDOL Music is running.")

    # Keep alive
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
