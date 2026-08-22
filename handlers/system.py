"""System handlers — /start, m!help, m!ping."""
import time
from pyrogram import Client, filters
from pyrogram.types import Message

from filters.prefix import command


def register(bot: Client) -> None:
    @bot.on_message(filters.command("start"))
    async def start_handler(client: Client, message: Message) -> None:
        await message.reply(
            "<b>IDOL Music</b> <code>v1.0.0</code>\n\n"
            "Simple & stable music bot for Telegram voice chats.\n\n"
            "Use <code>m!help</code> to see available commands."
        )

    @bot.on_message(command("help") | filters.command("help"))
    async def help_handler(client: Client, message: Message) -> None:
        await message.reply(
            "<b>IDOL Music</b> <code>v1.0.0</code>\n\n"
            "<b>Music</b>\n"
            "<code>m!p &lt;query&gt;</code> / <code>m!play &lt;query&gt;</code> — play or queue\n"
            "<code>m!s</code> / <code>m!skip</code> — skip\n"
            "<code>m!pause</code> — pause\n"
            "<code>m!resume</code> — resume\n"
            "<code>m!np</code> — now playing\n"
            "<code>m!stop</code> — stop and leave\n"
            "<code>m!autoplay</code> — enable autoplay\n\n"
            "<b>System</b>\n"
            "<code>m!help</code> — this message\n"
            "<code>m!ping</code> — latency\n\n"
            "<b>Notes</b>\n"
            "• Manual requests always have priority over autoplay.\n"
            "• Max 5 pending manual requests while autoplay is active.\n"
            "• Only members inside the active voice chat can control music "
            "(group admins may use stop as override)."
        )

    @bot.on_message(command("ping") | filters.command("ping"))
    async def ping_handler(client: Client, message: Message) -> None:
        start = time.perf_counter()
        msg = await message.reply("…")
        latency = (time.perf_counter() - start) * 1000
        await msg.edit(f"Pong! <code>{latency:.0f}ms</code>")
