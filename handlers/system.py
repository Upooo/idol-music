"""System handlers — /start, /help, /ping."""

import time

from pyrogram import Client, filters
from pyrogram.types import Message


def register(bot: Client) -> None:
    @bot.on_message(filters.command("start") & filters.private)
    async def start_handler(client: Client, message: Message) -> None:
        await message.reply(
            "🎵 <b>IDOL Music</b>\n\n"
            "Telegram voice chat music bot.\n\n"
            "Add me to a group and use <code>m!p [title]</code> to play music.\n\n"
            "<code>/help</code> — Command list\n"
            "<code>/ping</code> — Check latency",
        )

    @bot.on_message(filters.command("help"))
    async def help_handler(client: Client, message: Message) -> None:
        await message.reply(
            "🎵 <b>IDOL Music — Commands</b>\n\n"
            "<b>Music</b>\n"
            "<code>m!p [title]</code> — Play or queue a track\n"
            "<code>m!s</code> — Skip current track\n"
            "<code>m!q</code> — View queue\n"
            "<code>m!np</code> — Now playing\n"
            "<code>m!pause</code> — Pause\n"
            "<code>m!resume</code> — Resume\n\n"
            "<b>Admin</b>\n"
            "<code>m!stop</code> — Stop and clear queue\n"
            "<code>m!leave</code> — Leave voice chat",
        )

    @bot.on_message(filters.command("ping"))
    async def ping_handler(client: Client, message: Message) -> None:
        start = time.perf_counter()
        msg = await message.reply("Pinging...")
        latency = (time.perf_counter() - start) * 1000
        await msg.edit(f"🏓 <code>{latency:.0f}ms</code>")
