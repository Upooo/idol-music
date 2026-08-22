"""Music handlers \u2014 m! prefix commands (V1.0.0).

Permission model:
- m!p / m!play : any group member
- m!np / m!q   : anyone (read-only)
- m!skip       : vote-based (anyone) / force (admin + developer)
- pause/resume/stop/leave/autoplay : group admin or developer
"""
from __future__ import annotations

import logging

from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.types import Message

from filters.prefix import command, get_args
from filters.permissions import can_play, can_control, is_developer, is_group_admin
from music.manager import SessionManager
from music.queue import QueueFull
from music.source import search, TrackNotFound, ExtractionFailed, SourceError
from db.models import get_group_lang
import strings

log = logging.getLogger(__name__)


def register(bot: Client, sessions: SessionManager) -> None:

    # ----------------------------------------------------------------
    # m!p / m!play
    # ----------------------------------------------------------------
    @bot.on_message(command("p", aliases=["play"]))
    async def play_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            lang = await get_group_lang(message.chat.id)
            await message.reply(strings.get("PLAY_GROUPS_ONLY", lang))
            return
        if not message.from_user:
            return

        chat_id = message.chat.id
        user_id = message.from_user.id
        user_name = message.from_user.first_name or "User"
        query = get_args(message).strip()
        lang = await get_group_lang(chat_id)

        if not query:
            await message.reply(strings.get("PLAY_PROVIDE_QUERY", lang))
            return

        allowed, _ = await can_play(client, chat_id, user_id)
        if not allowed:
            await message.reply(strings.get("PLAY_NOT_ALLOWED", lang))
            return

        session = sessions.get(chat_id)
        status = await message.reply(strings.get("PLAY_SEARCHING", lang))
        try:
            track = await search(query, requester_id=user_id, requester_name=user_name)
            position = await session.add_and_play(track)
        except TrackNotFound:
            await status.edit(strings.get("PLAY_NOT_FOUND", lang))
            return
        except ExtractionFailed:
            await status.edit(strings.get("PLAY_EXTRACTION_FAILED", lang))
            return
        except QueueFull as qf:
            await status.edit(strings.get("PLAY_QUEUE_FULL", lang, error=str(qf)))
            return
        except SourceError as se:
            await status.edit(
                strings.get("PLAY_SOURCE_ERROR", lang, error=str(se) or "Something went wrong.")
            )
            return
        except Exception as exc:
            log.exception("Play failed in %s: %s", chat_id, exc)
            await status.edit(strings.get("PLAY_FAILED", lang))
            return

        if position == 0:
            requester = "Autoplay" if track.is_autoplay else track.requester_name
            await status.edit(
                strings.get("NOW_PLAYING", lang,
                             title=track.title, duration=track.duration_str,
                             requester=requester)
            )
        else:
            ap = "On" if session.autoplay_enabled else "Off"
            await status.edit(
                strings.get("ADDED_TO_QUEUE", lang,
                             title=track.title, position=position, autoplay=ap)
            )

    # ----------------------------------------------------------------
    # m!s / m!skip  \u2014 vote-based / force for admin+dev
    # ----------------------------------------------------------------
    @bot.on_message(command("s", aliases=["skip"]))
    async def skip_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE or not message.from_user:
            return
        chat_id = message.chat.id
        user_id = message.from_user.id
        lang = await get_group_lang(chat_id)
        session = sessions.get(chat_id)

        if not session.is_active:
            await message.reply(strings.get("SKIP_NOTHING", lang))
            return

        # Force skip: developer or group admin
        if is_developer(user_id) or await is_group_admin(client, chat_id, user_id):
            next_track = await session.skip()
            if next_track:
                await message.reply(strings.get("SKIP_DONE", lang, title=next_track.title))
            else:
                await message.reply(strings.get("SKIP_EMPTY", lang))
                sessions.remove(chat_id)
            return

        # Vote skip
        if session.votes.has_voted(chat_id, user_id):
            await message.reply(strings.get("SKIP_VOTE_ALREADY", lang))
            return

        votes = session.votes.add_vote(chat_id, user_id)
        needed = await session.get_skip_threshold()

        if votes >= needed:
            await message.reply(strings.get("SKIP_VOTE_PASSED", lang))
            next_track = await session.skip()
            if next_track:
                await message.reply(strings.get("SKIP_DONE", lang, title=next_track.title))
            else:
                await message.reply(strings.get("SKIP_EMPTY", lang))
                sessions.remove(chat_id)
        else:
            await message.reply(
                strings.get("SKIP_VOTE_ADDED", lang, votes=votes, needed=needed)
            )

    # ----------------------------------------------------------------
    # m!pause
    # ----------------------------------------------------------------
    @bot.on_message(command("pause"))
    async def pause_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE or not message.from_user:
            return
        chat_id = message.chat.id
        lang = await get_group_lang(chat_id)
        session = sessions.get(chat_id)
        allowed, _ = await can_control(client, chat_id, message.from_user.id)
        if not allowed:
            await message.reply(strings.get("PAUSE_ADMIN_ONLY", lang))
            return
        if await session.pause():
            await message.reply(strings.get("PAUSE_DONE", lang))
        else:
            await message.reply(strings.get("PAUSE_NOTHING", lang))

    # ----------------------------------------------------------------
    # m!resume
    # ----------------------------------------------------------------
    @bot.on_message(command("resume"))
    async def resume_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE or not message.from_user:
            return
        chat_id = message.chat.id
        lang = await get_group_lang(chat_id)
        session = sessions.get(chat_id)
        allowed, _ = await can_control(client, chat_id, message.from_user.id)
        if not allowed:
            await message.reply(strings.get("RESUME_ADMIN_ONLY", lang))
            return
        if await session.resume():
            await message.reply(strings.get("RESUME_DONE", lang))
        else:
            await message.reply(strings.get("RESUME_NOTHING", lang))

    # ----------------------------------------------------------------
    # m!np
    # ----------------------------------------------------------------
    @bot.on_message(command("np"))
    async def np_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            return
        lang = await get_group_lang(message.chat.id)
        session = sessions.get(message.chat.id)
        track = session.current
        if track is None:
            await message.reply(strings.get("NP_NOTHING", lang))
            return
        requester = "Autoplay" if track.is_autoplay else track.requester_name
        await message.reply(
            strings.get("NP_DISPLAY", lang,
                         title=track.title, duration=track.duration_str,
                         requester=requester)
        )

    # ----------------------------------------------------------------
    # m!q / m!queue
    # ----------------------------------------------------------------
    @bot.on_message(command("q", aliases=["queue"]))
    async def queue_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            return
        lang = await get_group_lang(message.chat.id)
        session = sessions.get(message.chat.id)
        items = await session.queue.snapshot()

        text = ""
        track = session.current
        if track:
            text += strings.get("QUEUE_NOW_PLAYING", lang, title=track.title)

        if not items:
            if not track:
                await message.reply(strings.get("QUEUE_EMPTY", lang))
                return
            text += strings.get("QUEUE_EMPTY", lang)
        else:
            count = len(items)
            s = "s" if count != 1 else ""
            text += strings.get("QUEUE_HEADER", lang, count=count, s=s)
            for i, t in enumerate(items, 1):
                text += strings.get("QUEUE_ITEM", lang,
                                     pos=i, title=t.title, duration=t.duration_str)

        await message.reply(text)

    # ----------------------------------------------------------------
    # m!stop
    # ----------------------------------------------------------------
    @bot.on_message(command("stop"))
    async def stop_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE or not message.from_user:
            return
        chat_id = message.chat.id
        lang = await get_group_lang(chat_id)
        session = sessions.get(chat_id)
        allowed, _ = await can_control(client, chat_id, message.from_user.id)
        if not allowed:
            await message.reply(strings.get("STOP_ADMIN_ONLY", lang))
            return
        await session.stop()
        sessions.remove(chat_id)
        await message.reply(strings.get("STOP_DONE", lang))

    # ----------------------------------------------------------------
    # m!leave
    # ----------------------------------------------------------------
    @bot.on_message(command("leave"))
    async def leave_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE or not message.from_user:
            return
        chat_id = message.chat.id
        lang = await get_group_lang(chat_id)
        session = sessions.get(chat_id)
        allowed, _ = await can_control(client, chat_id, message.from_user.id)
        if not allowed:
            await message.reply(strings.get("LEAVE_ADMIN_ONLY", lang))
            return
        if not session.is_active:
            await message.reply(strings.get("LEAVE_NOT_ACTIVE", lang))
            return
        await session.stop()
        sessions.remove(chat_id)
        await message.reply(strings.get("LEAVE_DONE", lang))

    # ----------------------------------------------------------------
    # m!autoplay  \u2014 toggle
    # ----------------------------------------------------------------
    @bot.on_message(command("autoplay"))
    async def autoplay_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE or not message.from_user:
            return
        chat_id = message.chat.id
        lang = await get_group_lang(chat_id)
        session = sessions.get(chat_id)
        allowed, _ = await can_control(client, chat_id, message.from_user.id)
        if not allowed:
            await message.reply(strings.get("AUTOPLAY_ADMIN_ONLY", lang))
            return

        if session.autoplay_enabled:
            session.autoplay_enabled = False
            await message.reply(strings.get("AUTOPLAY_DISABLED", lang))
        else:
            newly = await session.enable_autoplay()
            if newly:
                await message.reply(strings.get("AUTOPLAY_ENABLED", lang))
            else:
                await message.reply(strings.get("AUTOPLAY_ALREADY_ON", lang))
