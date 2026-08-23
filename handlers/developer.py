"""Developer-only commands: restart, pull, broadcast, status, logs, cookie."""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from pathlib import Path

from pyrogram import Client
from pyrogram.types import Message

from filters.prefix import command, get_args
from filters.permissions import is_developer
from db.client import is_connected as db_connected
from db.models import get_play_count
from utils import log_group
import strings

log = logging.getLogger(__name__)

_start_time = time.time()
_COOKIES_PATH = Path(__file__).resolve().parent.parent / "cookies.txt"


def register(bot: Client, sessions=None, assistant=None, calls=None) -> None:
    """sessions, assistant, calls optional — used for graceful shutdown."""

    async def _graceful_shutdown() -> None:
        """Stop all active sessions and clients before restarting."""
        await log_group.send(strings.get("LOG_STOPPED", "en"))

        if sessions is not None:
            for cid in sessions.active_chat_ids():
                try:
                    session = sessions.get_existing(cid)
                    if session:
                        await session.stop()
                except Exception:
                    pass

        if calls is not None:
            try:
                await calls.stop()
            except Exception:
                pass
        if assistant is not None:
            try:
                await assistant.stop()
            except Exception:
                pass
        try:
            await bot.stop()
        except Exception:
            pass

    @bot.on_message(command("restart"))
    async def restart_handler(client: Client, message: Message) -> None:
        user = message.from_user
        if not user or not is_developer(user.id):
            lang = "en"
            await message.reply(strings.get("DEV_ONLY", lang))
            return
        await message.reply(strings.get("DEV_RESTART", "en"))
        await _graceful_shutdown()
        os.execl(sys.executable, sys.executable, *sys.argv)

    @bot.on_message(command("pull"))
    async def pull_handler(client: Client, message: Message) -> None:
        user = message.from_user
        if not user or not is_developer(user.id):
            return
        proc = await asyncio.create_subprocess_exec(
            "git", "pull",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode().strip() or "(no output)"
        await message.reply(
            strings.get("DEV_PULL_RESULT", "en", output=output)
        )

    @bot.on_message(command("bc", aliases=["broadcast"]))
    async def broadcast_handler(client: Client, message: Message) -> None:
        user = message.from_user
        if not user or not is_developer(user.id):
            return

        text = get_args(message)
        if not text and message.reply_to_message:
            text = message.reply_to_message.text or message.reply_to_message.caption
        if not text:
            await message.reply(strings.get("DEV_BC_USAGE", "en"))
            return

        if sessions is None:
            await message.reply(strings.get("DEV_BC_NO_TARGETS", "en"))
            return

        targets = sessions.active_chat_ids()
        if not targets:
            await message.reply(strings.get("DEV_BC_NO_TARGETS", "en"))
            return

        ok = fail = 0
        for cid in targets:
            try:
                await client.send_message(cid, text)
                ok += 1
            except Exception:
                fail += 1

        await message.reply(
            strings.get("DEV_BC_DONE", "en", ok=ok, fail=fail)
        )

    @bot.on_message(command("status"))
    async def status_handler(client: Client, message: Message) -> None:
        user = message.from_user
        if not user or not is_developer(user.id):
            return

        uptime_s = int(time.time() - _start_time)
        h, rem = divmod(uptime_s, 3600)
        m, s = divmod(rem, 60)
        uptime_str = f"{h}h {m}m {s}s"

        session_count = len(sessions) if sessions else 0
        mongo = "Connected" if db_connected() else "Disabled"
        total_plays = await get_play_count()
        cookies = "Loaded" if _COOKIES_PATH.is_file() else "Not found"

        await message.reply(
            strings.get(
                "DEV_STATUS", "en",
                uptime=uptime_str,
                sessions=session_count,
                python=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                mongo=mongo,
                total_plays=total_plays,
                cookies=cookies,
            )
        )

    @bot.on_message(command("logs"))
    async def logs_handler(client: Client, message: Message) -> None:
        user = message.from_user
        if not user or not is_developer(user.id):
            return

        args = get_args(message)
        lines = 50
        if args:
            try:
                lines = int(args)
            except ValueError:
                pass

        log_file = Path(__file__).resolve().parent.parent / "idol_music.log"
        if not log_file.is_file():
            await message.reply(strings.get("DEV_LOGS_EMPTY", "en"))
            return

        content = log_file.read_text(encoding="utf-8", errors="replace")
        tail = "\n".join(content.splitlines()[-lines:])
        if len(tail) > 4000:
            tail = tail[-4000:]

        await message.reply(f"<code>{tail}</code>")

    @bot.on_message(command("cookie", aliases=["cookies"]))
    async def cookie_handler(client: Client, message: Message) -> None:
        user = message.from_user
        if not user or not is_developer(user.id):
            return

        args = get_args(message)

        # If replying to a message, use that as cookie content
        cookie_text = ""
        if message.reply_to_message:
            cookie_text = message.reply_to_message.text or ""
        elif args:
            cookie_text = args

        if not cookie_text:
            # Show current status
            if _COOKIES_PATH.is_file():
                size = _COOKIES_PATH.stat().st_size
                lines_count = len(_COOKIES_PATH.read_text(errors="replace").splitlines())
                await message.reply(
                    strings.get("DEV_COOKIE_STATUS", "en",
                                size=size, lines=lines_count)
                )
            else:
                await message.reply(strings.get("DEV_COOKIE_NOT_FOUND", "en"))
            return

        # Write new cookies
        try:
            _COOKIES_PATH.write_text(cookie_text.strip() + "\n", encoding="utf-8")
            lines_count = len(cookie_text.strip().splitlines())
            await message.reply(
                strings.get("DEV_COOKIE_UPDATED", "en", lines=lines_count)
            )
            await log_group.send(
                strings.get("LOG_COOKIE_UPDATED", "en", lines=lines_count)
            )
        except Exception as exc:
            await message.reply(f"Failed to write cookies: {exc}")
