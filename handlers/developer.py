"""Developer-only commands: restart, pull, broadcast."""
from __future__ import annotations

import asyncio
import logging
import os
import sys

from pyrogram import Client
from pyrogram.types import Message

from filters.prefix import command, get_args
from filters.permissions import is_developer

log = logging.getLogger(__name__)


def register(bot: Client, sessions=None) -> None:
    """sessions optional — used later for broadcast targets if available."""

    @bot.on_message(command("restart"))
    async def restart_handler(client: Client, message: Message) -> None:
        if not message.from_user or not is_developer(message.from_user.id):
            await message.reply("This command is restricted to developers.")
            return
        await message.reply("Restarting…")
        log.info("Restart requested by developer %s", message.from_user.id)
        os.execv(sys.executable, [sys.executable] + sys.argv)

    @bot.on_message(command("pull"))
    async def pull_handler(client: Client, message: Message) -> None:
        if not message.from_user or not is_developer(message.from_user.id):
            await message.reply("This command is restricted to developers.")
            return
        await message.reply("Pulling latest changes…")
        proc = await asyncio.create_subprocess_shell(
            "git pull",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        out = (stdout or b"").decode(errors="replace")
        err = (stderr or b"").decode(errors="replace")
        text = f"<b>git pull</b>\n<code>{(out or err or 'done')[:3500]}</code>"
        await message.reply(text)

    @bot.on_message(command("bc", aliases=["broadcast"]))
    async def broadcast_handler(client: Client, message: Message) -> None:
        if not message.from_user or not is_developer(message.from_user.id):
            await message.reply("This command is restricted to developers.")
            return
        text = get_args(message).strip()
        if not text and message.reply_to_message:
            text = (
                message.reply_to_message.text
                or message.reply_to_message.caption
                or ""
            )
        if not text:
            await message.reply(
                "Usage: <code>m!bc &lt;message&gt;</code> or reply to a message."
            )
            return

        # Minimal V1: broadcast to currently known active sessions
        targets = []
        if sessions is not None:
            targets = list(sessions.active_chats)

        if not targets:
            await message.reply(
                "No registered/active chats to broadcast to yet.\n"
                "(Chats appear after music sessions start.)"
            )
            log.info("Broadcast requested (no targets): %s", text[:80])
            return

        ok, fail = 0, 0
        for chat_id in targets:
            try:
                await client.send_message(chat_id, text)
                ok += 1
            except Exception as exc:
                log.warning("Broadcast failed for %s: %s", chat_id, exc)
                fail += 1
        await message.reply(f"Broadcast done. Success: {ok} · Failed: {fail}")
