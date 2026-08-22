"""Developer-only commands: restart, pull, broadcast, status, logs."""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import time

from pyrogram import Client
from pyrogram.types import Message

from filters.prefix import command, get_args
from filters.permissions import is_developer
from db.client import is_connected as db_connected
from utils import log_group
import strings

log = logging.getLogger(__name__)

_start_time = time.time()


def register(bot: Client, sessions=None, assistant=None, calls=None) -> None:
    """sessions, assistant, calls optional \u2014 used for graceful shutdown."""

    async def _graceful_shutdown() -> None:
        """Stop all active sessions and clients before restarting."""
        await log_group.send(strings.get("LOG_STOPPED", "en"))

        if sessions is not None:
            for chat_id in list(sessions.active_chats):
                try:
                    sess = sessions.get(chat_id)
                    await sess.stop()
                    sessions.remove(chat_id)
                except Exception as exc:
                    log.warning("Failed to stop session %s: %s", chat_id, exc)

        if calls is not None:
            try:
                await calls.stop()
                log.info("PyTgCalls stopped.")
            except Exception as exc:
                log.warning("Failed to stop PyTgCalls: %s", exc)

        try:
            await bot.stop()
            log.info("Bot stopped.")
        except Exception as exc:
            log.warning("Failed to stop bot: %s", exc)

        if assistant is not None:
            try:
                await assistant.stop()
                log.info("Assistant stopped.")
            except Exception as exc:
                log.warning("Failed to stop assistant: %s", exc)

    @bot.on_message(command("restart"))
    async def restart_handler(client: Client, message: Message) -> None:
        if not message.from_user or not is_developer(message.from_user.id):
            await message.reply(strings.get("DEV_ONLY", "en"))
            return
        await message.reply(strings.get("DEV_RESTART", "en"))
        log.info("Restart requested by developer %s", message.from_user.id)
        await _graceful_shutdown()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    @bot.on_message(command("pull"))
    async def pull_handler(client: Client, message: Message) -> None:
        if not message.from_user or not is_developer(message.from_user.id):
            await message.reply(strings.get("DEV_ONLY", "en"))
            return
        await message.reply(strings.get("DEV_PULL", "en"))
        proc = await asyncio.create_subprocess_shell(
            "git pull",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        out = (stdout or b"").decode(errors="replace")
        err = (stderr or b"").decode(errors="replace")
        output = (out or err or "done")[:3500]
        await message.reply(strings.get("DEV_PULL_RESULT", "en", output=output))

    @bot.on_message(command("bc", aliases=["broadcast"]))
    async def broadcast_handler(client: Client, message: Message) -> None:
        if not message.from_user or not is_developer(message.from_user.id):
            await message.reply(strings.get("DEV_ONLY", "en"))
            return
        text = get_args(message).strip()
        if not text and message.reply_to_message:
            text = (
                message.reply_to_message.text
                or message.reply_to_message.caption
                or ""
            )
        if not text:
            await message.reply(strings.get("DEV_BC_USAGE", "en"))
            return

        targets = []
        if sessions is not None:
            targets = list(sessions.active_chats)

        if not targets:
            await message.reply(strings.get("DEV_BC_NO_TARGETS", "en"))
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
        await message.reply(strings.get("DEV_BC_DONE", "en", ok=ok, fail=fail))

    @bot.on_message(command("status"))
    async def status_handler(client: Client, message: Message) -> None:
        if not message.from_user or not is_developer(message.from_user.id):
            await message.reply(strings.get("DEV_ONLY", "en"))
            return

        uptime_secs = int(time.time() - _start_time)
        hours, remainder = divmod(uptime_secs, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime = f"{hours}h {minutes}m {seconds}s"

        active = sessions.active_count if sessions else 0
        python_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        mongo = "Connected" if db_connected() else "Not connected"

        await message.reply(
            strings.get(
                "DEV_STATUS", "en",
                uptime=uptime, sessions=active, python=python_ver, mongo=mongo,
            )
        )

    @bot.on_message(command("logs", aliases=["log"]))
    async def logs_handler(client: Client, message: Message) -> None:
        if not message.from_user or not is_developer(message.from_user.id):
            await message.reply(strings.get("DEV_ONLY", "en"))
            return

        args = get_args(message).strip()
        try:
            n = int(args) if args else 50
        except ValueError:
            n = 50
        n = min(n, 200)

        log_file = None
        for path in ["idol_music.log", "bot.log", "/tmp/idol_music.log"]:
            if os.path.isfile(path):
                log_file = path
                break

        if log_file is None:
            await message.reply(strings.get("DEV_LOGS_EMPTY", "en"))
            return

        try:
            with open(log_file, "r", errors="replace") as f:
                lines = f.readlines()
            tail = lines[-n:] if len(lines) > n else lines
            text = "".join(tail)[:4000]
            await message.reply(f"<code>{text}</code>")
        except Exception as exc:
            await message.reply(f"Error reading logs: <code>{exc}</code>")
