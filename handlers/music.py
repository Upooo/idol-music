"""Music handlers — m! prefix commands (V1.0.0).

Permission model (V1 practical):
- m!p / m!play : any group member
- m!np         : anyone
- pause/resume/skip/stop/autoplay : group admin or developer
"""
from __future__ import annotations

import logging

from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.types import Message

from filters.prefix import command, get_args
from filters.permissions import can_play, can_control
from music.manager import SessionManager
from music.queue import QueueFull
from music.source import search, TrackNotFound, ExtractionFailed, SourceError

log = logging.getLogger(__name__)


def register(bot: Client, sessions: SessionManager) -> None:

    # ------------------------------------------------------------------
    # m!p / m!play  — any member
    # ------------------------------------------------------------------
    @bot.on_message(command("p", aliases=["play"]))
    async def play_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            await message.reply("This command works in groups only.")
            return
        if not message.from_user:
            return

        chat_id = message.chat.id
        user_id = message.from_user.id
        user_name = message.from_user.first_name or "User"
        query = get_args(message).strip()

        if not query:
            await message.reply(
                "Please provide a song name or URL.\n"
                "Example: <code>m!p never gonna give you up</code>"
            )
            return

        allowed, _ = await can_play(client, chat_id, user_id)
        if not allowed:
            await message.reply("You are not allowed to play music.")
            return

        session = sessions.get(chat_id)
        status = await message.reply("Searching…")
        try:
            track = await search(query, requester_id=user_id, requester_name=user_name)
            position = await session.add_and_play(track)
        except TrackNotFound:
            await status.edit("Couldn't find that track. Try a different query.")
            return
        except ExtractionFailed:
            await status.edit(
                "Failed to extract the track. It may be private, deleted, or unsupported."
            )
            return
        except QueueFull as qf:
            await status.edit(str(qf))
            return
        except SourceError as se:
            await status.edit(str(se) or "Something went wrong.")
            return
        except Exception as exc:
            log.exception("Play failed in %s: %s", chat_id, exc)
            await status.edit(
                "Couldn't start playback.\n"
                "<i>Make sure a voice chat is active and the assistant can join.</i>"
            )
            return

        if position == 0:
            await status.edit(
                f"<b>Now Playing</b>\n"
                f"<code>{track.title}</code>\n"
                f"Duration: <code>{track.duration_str}</code> · "
                f"By: <code>{track.requester_name}</code>"
            )
        else:
            ap = "On" if session.autoplay_enabled else "Off"
            await status.edit(
                f"<b>Added to queue</b>\n"
                f"<code>{track.title}</code>\n"
                f"Position: <code>{position}</code> · Autoplay: <code>{ap}</code>"
            )

    # ------------------------------------------------------------------
    # m!s / m!skip  — admin only
    # ------------------------------------------------------------------
    @bot.on_message(command("s", aliases=["skip"]))
    async def skip_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE or not message.from_user:
            return
        chat_id = message.chat.id
        session = sessions.get(chat_id)
        allowed, _ = await can_control(client, chat_id, message.from_user.id)
        if not allowed:
            await message.reply("Only group admins can skip.")
            return
        if not session.is_active:
            await message.reply("Nothing is currently playing.")
            return
        next_track = await session.skip()
        if next_track:
            await message.reply(
                f"Skipped. Now playing: <code>{next_track.title}</code>"
            )
        else:
            await message.reply("Skipped. Nothing left in queue.")
            sessions.remove(chat_id)

    # ------------------------------------------------------------------
    # m!pause — admin only
    # ------------------------------------------------------------------
    @bot.on_message(command("pause"))
    async def pause_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE or not message.from_user:
            return
        chat_id = message.chat.id
        session = sessions.get(chat_id)
        allowed, _ = await can_control(client, chat_id, message.from_user.id)
        if not allowed:
            await message.reply("Only group admins can pause.")
            return
        if await session.pause():
            await message.reply("Playback paused.")
        else:
            await message.reply("Nothing is currently playing.")

    # ------------------------------------------------------------------
    # m!resume — admin only
    # ------------------------------------------------------------------
    @bot.on_message(command("resume"))
    async def resume_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE or not message.from_user:
            return
        chat_id = message.chat.id
        session = sessions.get(chat_id)
        allowed, _ = await can_control(client, chat_id, message.from_user.id)
        if not allowed:
            await message.reply("Only group admins can resume.")
            return
        if await session.resume():
            await message.reply("Playback resumed.")
        else:
            await message.reply("Nothing is currently paused.")

    # ------------------------------------------------------------------
    # m!np — anyone
    # ------------------------------------------------------------------
    @bot.on_message(command("np"))
    async def np_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            return
        session = sessions.get(message.chat.id)
        track = session.current
        if track is None:
            await message.reply("Nothing is currently playing.")
            return
        source = "Autoplay" if track.is_autoplay else track.requester_name
        await message.reply(
            f"<b>Now Playing</b>\n"
            f"<code>{track.title}</code>\n"
            f"Duration: <code>{track.duration_str}</code> · By: <code>{source}</code>"
        )

    # ------------------------------------------------------------------
    # m!stop — admin only
    # ------------------------------------------------------------------
    @bot.on_message(command("stop"))
    async def stop_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE or not message.from_user:
            return
        chat_id = message.chat.id
        session = sessions.get(chat_id)
        allowed, reason = await can_control(client, chat_id, message.from_user.id)
        if not allowed:
            await message.reply("Only group admins can stop.")
            return
        await session.stop()
        sessions.remove(chat_id)
        await message.reply("Stopped. Queue cleared and left the voice chat.")

    # ------------------------------------------------------------------
    # m!autoplay — admin only
    # ------------------------------------------------------------------
    @bot.on_message(command("autoplay"))
    async def autoplay_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE or not message.from_user:
            return
        chat_id = message.chat.id
        session = sessions.get(chat_id)
        allowed, _ = await can_control(client, chat_id, message.from_user.id)
        if not allowed:
            await message.reply("Only group admins can enable autoplay.")
            return
        newly = await session.enable_autoplay()
        if newly:
            await message.reply("Autoplay enabled for this session.")
        else:
            await message.reply("Autoplay is already enabled.")
