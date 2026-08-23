"""Music handlers — m! prefix commands (V1.1.0 Clean).

Permission model:
- m!p / m!play : any group member
- m!np / m!q   : anyone (read-only)
- m!skip       : vote-based (anyone) / force (admin + developer)
- pause/resume/stop/leave/autoplay : group admin or developer

All method calls verified against:
- queue.py: put(), get(), clear(), snapshot()
- session.py: add_and_play(), skip(), pause(), resume(), stop()
- player.py: play(), pause(), resume(), stop(), is_active, current_track
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

    # ==================== Play ====================

    @bot.on_message(command("p", aliases=["play"]))
    async def play_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            lang = await get_group_lang(message.chat.id)
            await message.reply(strings.get("PLAY_GROUPS_ONLY", lang))
            return

        user = message.from_user
        if not user:
            return
        lang = await get_group_lang(message.chat.id)

        allowed, reason = await can_play(client, message.chat.id, user.id)
        if not allowed:
            await message.reply(strings.get("PLAY_NOT_ALLOWED", lang))
            return

        query = get_args(message)
        if not query:
            await message.reply(strings.get("PLAY_PROVIDE_QUERY", lang))
            return

        status_msg = await message.reply(strings.get("PLAY_SEARCHING", lang))

        try:
            track = await search(query)
        except TrackNotFound:
            await status_msg.edit_text(strings.get("PLAY_NOT_FOUND", lang))
            return
        except ExtractionFailed:
            await status_msg.edit_text(strings.get("PLAY_EXTRACTION_FAILED", lang))
            return
        except SourceError as e:
            await status_msg.edit_text(strings.get("PLAY_SOURCE_ERROR", lang, error=str(e)))
            return

        track.requester_id = user.id
        track.requester_name = user.first_name

        session = sessions.get(message.chat.id)

        try:
            position = await session.add_and_play(track)
        except QueueFull as e:
            await status_msg.edit_text(strings.get("PLAY_QUEUE_FULL", lang, error=str(e)))
            return
        except Exception as e:
            log.exception("Play failed in %d: %s", message.chat.id, e)
            await status_msg.edit_text(strings.get("PLAY_FAILED", lang))
            return

        if position == 0:
            await status_msg.edit_text(strings.get(
                "NOW_PLAYING", lang,
                title=track.title,
                duration=track.duration_str,
                requester=track.requester_name,
            ))
        else:
            await status_msg.edit_text(strings.get(
                "ADDED_TO_QUEUE", lang,
                title=track.title,
                position=position,
                autoplay="On" if session.autoplay else "Off",
            ))

    # ==================== Skip ====================

    @bot.on_message(command("s", aliases=["skip"]))
    async def skip_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            return
        user = message.from_user
        if not user:
            return
        lang = await get_group_lang(message.chat.id)

        session = sessions.get_existing(message.chat.id)
        if not session or not session.player.is_active:
            await message.reply(strings.get("SKIP_NOTHING", lang))
            return

        # Admin / developer: force skip
        if is_developer(user.id) or await is_group_admin(client, message.chat.id, user.id):
            nxt = await session.skip()
            if nxt:
                await message.reply(strings.get("SKIP_DONE", lang, title=nxt.title))
            else:
                await message.reply(strings.get("SKIP_EMPTY", lang))
            return

        # Vote skip
        threshold = 2
        if session.votes.has_voted(message.chat.id, user.id):
            await message.reply(strings.get("SKIP_VOTE_ALREADY", lang))
            return

        count = session.votes.add_vote(message.chat.id, user.id)
        if count >= threshold:
            await message.reply(strings.get("SKIP_VOTE_PASSED", lang))
            nxt = await session.skip()
            if nxt:
                await message.reply(strings.get("SKIP_DONE", lang, title=nxt.title))
            else:
                await message.reply(strings.get("SKIP_EMPTY", lang))
        else:
            await message.reply(strings.get(
                "SKIP_VOTE_ADDED", lang, votes=count, needed=threshold,
            ))

    # ==================== Pause / Resume ====================

    @bot.on_message(command("pause"))
    async def pause_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            return
        user = message.from_user
        if not user:
            return
        lang = await get_group_lang(message.chat.id)

        allowed, _ = await can_control(client, message.chat.id, user.id)
        if not allowed:
            await message.reply(strings.get("PAUSE_ADMIN_ONLY", lang))
            return

        session = sessions.get_existing(message.chat.id)
        if not session or not session.player.is_active:
            await message.reply(strings.get("PAUSE_NOTHING", lang))
            return

        await session.pause()
        await message.reply(strings.get("PAUSE_DONE", lang))

    @bot.on_message(command("resume"))
    async def resume_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            return
        user = message.from_user
        if not user:
            return
        lang = await get_group_lang(message.chat.id)

        allowed, _ = await can_control(client, message.chat.id, user.id)
        if not allowed:
            await message.reply(strings.get("RESUME_ADMIN_ONLY", lang))
            return

        session = sessions.get_existing(message.chat.id)
        if not session:
            await message.reply(strings.get("RESUME_NOTHING", lang))
            return

        await session.resume()
        await message.reply(strings.get("RESUME_DONE", lang))

    # ==================== Now Playing ====================

    @bot.on_message(command("np", aliases=["nowplaying"]))
    async def np_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            return
        lang = await get_group_lang(message.chat.id)

        session = sessions.get_existing(message.chat.id)
        if not session or not session.player.current_track:
            await message.reply(strings.get("NP_NOTHING", lang))
            return

        t = session.player.current_track
        await message.reply(strings.get(
            "NP_DISPLAY", lang,
            title=t.title,
            duration=t.duration_str,
            requester=t.requester_name,
        ))

    # ==================== Queue ====================

    @bot.on_message(command("q", aliases=["queue"]))
    async def queue_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            return
        lang = await get_group_lang(message.chat.id)

        session = sessions.get_existing(message.chat.id)
        if not session:
            await message.reply(strings.get("QUEUE_EMPTY", lang))
            return

        items = await session.queue.snapshot()
        if not items and not session.player.current_track:
            await message.reply(strings.get("QUEUE_EMPTY", lang))
            return

        text = ""
        if session.player.current_track:
            text += strings.get(
                "QUEUE_NOW_PLAYING", lang,
                title=session.player.current_track.title,
            )
        if items:
            text += strings.get("QUEUE_HEADER", lang, count=len(items))
            for i, t in enumerate(items, 1):
                text += strings.get(
                    "QUEUE_ITEM", lang,
                    pos=i, title=t.title, duration=t.duration_str,
                )
        elif not session.player.current_track:
            text = strings.get("QUEUE_EMPTY", lang)

        await message.reply(text)

    # ==================== Stop / Leave ====================

    @bot.on_message(command("stop"))
    async def stop_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            return
        user = message.from_user
        if not user:
            return
        lang = await get_group_lang(message.chat.id)

        allowed, _ = await can_control(client, message.chat.id, user.id)
        if not allowed:
            await message.reply(strings.get("STOP_ADMIN_ONLY", lang))
            return

        session = sessions.get_existing(message.chat.id)
        if session:
            await session.stop()  # stops player + leaves VC
            await sessions.remove(message.chat.id)  # cleanup from registry
        await message.reply(strings.get("STOP_DONE", lang))

    @bot.on_message(command("leave", aliases=["disconnect"]))
    async def leave_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            return
        user = message.from_user
        if not user:
            return
        lang = await get_group_lang(message.chat.id)

        allowed, _ = await can_control(client, message.chat.id, user.id)
        if not allowed:
            await message.reply(strings.get("LEAVE_ADMIN_ONLY", lang))
            return

        session = sessions.get_existing(message.chat.id)
        if not session:
            await message.reply(strings.get("LEAVE_NOT_ACTIVE", lang))
            return

        await session.stop()
        await sessions.remove(message.chat.id)
        await message.reply(strings.get("LEAVE_DONE", lang))

    # ==================== Autoplay (one-shot) ====================

    @bot.on_message(command("autoplay"))
    async def autoplay_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            return
        user = message.from_user
        if not user:
            return
        lang = await get_group_lang(message.chat.id)

        allowed, _ = await can_control(client, message.chat.id, user.id)
        if not allowed:
            await message.reply(strings.get("AUTOPLAY_ADMIN_ONLY", lang))
            return

        session = sessions.get(message.chat.id)
        if session.autoplay:
            await message.reply(strings.get("AUTOPLAY_ALREADY_ON", lang))
            return

        session.autoplay = True
        await message.reply(strings.get("AUTOPLAY_ENABLED", lang))
