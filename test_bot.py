"""Minimal bot test — isolate whether bot receives messages.

Run this INSTEAD of main.py to test:
    python test_bot.py

If this doesn't receive messages either, the issue is:
- Bot token
- BotFather settings
- Network/firewall

If this works but main.py doesn't, the issue is:
- Assistant/PyTgCalls interference
- Handler registration order
"""

import asyncio
import logging

from pyrogram import Client, filters
from pyrogram.types import Message
from config import config

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
log = logging.getLogger(__name__)


async def main():
    bot = Client(
        name="test_bot",
        api_id=config.api_id,
        api_hash=config.api_hash,
        bot_token=config.bot_token,
    )

    @bot.on_message()
    async def on_any_message(client: Client, message: Message):
        log.info(
            "GOT MESSAGE: chat_id=%s type=%s text=%r from=%s",
            message.chat.id,
            message.chat.type,
            message.text,
            message.from_user.id if message.from_user else "N/A",
        )
        await message.reply("I'm alive!")

    log.info("Starting test bot...")
    await bot.start()

    me = await bot.get_me()
    log.info("Bot started as: @%s (id=%d)", me.username, me.id)

    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
