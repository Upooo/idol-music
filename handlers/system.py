"""System handlers \u2014 /start, m!help, m!ping, m!lang."""
import time

from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.types import Message

from filters.prefix import command, get_args
from filters.permissions import can_control
from db.models import get_group_lang, set_group_lang
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

    @bot.on_message(command("lang", aliases=["language"]))
    async def lang_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE or not message.from_user:
            return
        chat_id = message.chat.id
        lang = await get_group_lang(chat_id)
        args = get_args(message).strip().lower()

        if not args:
            await message.reply(strings.get("LANG_CURRENT", lang, lang=lang))
            return

        allowed, _ = await can_control(client, chat_id, message.from_user.id)
        if not allowed:
            await message.reply(strings.get("LANG_ADMIN_ONLY", lang))
            return

        available = strings.available_languages()
        if args not in available:
            await message.reply(
                strings.get("LANG_INVALID", lang, languages=", ".join(available))
            )
            return

        await set_group_lang(chat_id, args)
        await message.reply(strings.get("LANG_SET", args, lang=args))
