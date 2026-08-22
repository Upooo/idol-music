"""Music handlers — m! prefix commands.

Phase 1: hardcoded test audio for stack verification.
"""

from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.types import Message

from filters.prefix import command, get_args
from music.manager import SessionManager
from music.track import Track

# Phase 1 test URL — public domain audio
# Replace with yt-dlp search in Phase 2
TEST_AUDIO_URL = "https://www.kozco.com/tech/LRMonoPhase4.wav"


def register(bot: Client, sessions: SessionManager) -> None:

    @bot.on_message(command("p", aliases=["play"]))
    async def play_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            await message.reply("This command works in groups only.")
            return

        args = get_args(message)
        user = message.from_user

        # Phase 1: use hardcoded URL for stack test
        # Phase 2: yt-dlp search with `args` as query
        track = Track(
            title=args if args else "Test Audio",
            url=TEST_AUDIO_URL,
            duration=10,
            requester_id=user.id if user else 0,
            requester_name=user.first_name if user else "Unknown",
        )

        session = sessions.get(message.chat.id)

        try:
            position = await session.add_and_play(track)
        except Exception as e:
            await message.reply(
                f"⚠️ Couldn't play.\n\n"
                f"<i>Make sure a voice chat is active and the assistant "
                f"has permission to join.</i>"
            )
            return

        if position == 0:
            await message.reply(
                f"🎵 <b>Now Playing</b>\n\n"
                f"{track.title}\n"
                f"Duration: {track.duration_str}\n"
                f"Requested by {track.requester_name}"
            )
        else:
            await message.reply(
                f"➕ <b>Added to Queue</b>\n\n"
                f"{track.title}\n"
                f"Position: #{position}\n"
                f"Requested by {track.requester_name}"
            )

    @bot.on_message(command("stop"))
    async def stop_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            return

        session = sessions.get(message.chat.id)
        await session.stop()
        sessions.remove(message.chat.id)
        await message.reply("⏹ Stopped and cleared queue.")

    @bot.on_message(command("leave"))
    async def leave_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            return

        session = sessions.get(message.chat.id)
        await session.stop()
        sessions.remove(message.chat.id)
        await message.reply("👋 Left voice chat.")

    @bot.on_message(command("pause"))
    async def pause_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            return

        session = sessions.get(message.chat.id)
        await session.pause()
        await message.reply("⏸ Paused.")

    @bot.on_message(command("resume"))
    async def resume_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            return

        session = sessions.get(message.chat.id)
        await session.resume()
        await message.reply("▶️ Resumed.")

    @bot.on_message(command("s", aliases=["skip"]))
    async def skip_handler(client: Client, message: Message) -> None:
        if message.chat.type == ChatType.PRIVATE:
            return

        session = sessions.get(message.chat.id)
        next_track = await session.skip()

        if next_track:
            await message.reply(
                f"⏭ <b>Skipped</b>\n\n"
                f"Now playing: {next_track.title}"
            )
        else:
            await message.reply("⏭ Skipped. Queue empty, leaving.")
            sessions.remove(message.chat.id)
