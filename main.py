"""IDOL Music — Entry Point.

Starts both Pyrogram clients (bot + assistant) and PyTgCalls.
"""

import asyncio
import logging

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

    # Register stream-ended callback
    @calls.on_closed_voice_chat()
    async def on_closed(client, chat_id: int):
        log.info("VC closed in %d", chat_id)
        session = sessions.get(chat_id)
        await session.stop()
        sessions.remove(chat_id)

    @calls.on_stream_end()
    async def on_stream_end(client, update):
        chat_id = update.chat_id
        session = sessions.get(chat_id)
        await session.player.handle_stream_end()

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
