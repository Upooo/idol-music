"""System handlers \u2014 /start, m!help, m!ping."""
import time
from pyrogram import Client, filters
from pyrogram.types import Message

from filters.prefix import command
from db.models import get_group_lang
import strings


def register(bot: Client) -> None:
    @bot.on_message(filters.command("start"))
    async def start_handler(client: Client, message: Message) -> None:
        lang = await get_group_lang(message.chat.id)
        await message.reply(strings.get("START", lang))

    @bot.on_message(command("help") | filters.command("help"))
    async def help_handler(client: Client, message: Message) -> None:
        lang = await get_group_lang(message.chat.id)
        await message.reply(strings.get("HELP", lang))

    @bot.on_message(command("ping") | filters.command("ping"))
    async def ping_handler(client: Client, message: Message) -> None:
        lang = await get_group_lang(message.chat.id)
        start = time.perf_counter()
        msg = await message.reply("\u2026")
        latency = (time.perf_counter() - start) * 1000
        await msg.edit(strings.get("PING", lang, latency=latency))
