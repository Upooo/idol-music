"""IDOL Music — Entry Point.

Starts both Pyrogram clients (bot + assistant) and PyTgCalls.
"""

import asyncio
import logging

from pytgcalls.types import Update

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

    # Register stream-ended callback (PyTgCalls 2.x API)
    @calls.on_update(filters=None)
    async def on_update(client: PyTgCalls, update: Update):
        # PyTgCalls 2.x fires Update with status for stream events
        # We check for stream end status
        if hasattr(update, 'chat_id') and hasattr(update, 'status'):
            from pytgcalls.types import ChatUpdate
            if isinstance(update, ChatUpdate):
                from pytgcalls.types import ChatUpdate as CU
                if update.status == CU.Status.CLOSED_VOICE_CHAT:
                    log.info("VC closed in %d", update.chat_id)
                    sess = sessions.get(update.chat_id)
                    await sess.stop()
                    sessions.remove(update.chat_id)
                elif update.status == CU.Status.PAUSED_STREAM:
                    pass  # handled by player
                elif update.status == CU.Status.RESUMED_STREAM:
                    pass  # handled by player

    @calls.on_stream_end()
    async def on_stream_end(client, update):
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
