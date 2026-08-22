"""Custom m! prefix filter for Pyrogram."""

from pyrogram import filters
from pyrogram.types import Message

PREFIX = "m!"


def command(cmd: str, aliases: list[str] | None = None):
    """Filter for m! prefix commands.

    Usage:
        @bot.on_message(command("p", aliases=["play"]))
        async def play_handler(client, message): ...

    Matches: m!p, m!play (case-insensitive)
    """
    commands = {cmd.lower()}
    if aliases:
        commands.update(a.lower() for a in aliases)

    async def func(flt, _, message: Message) -> bool:
        if not message.text:
            return False

        text = message.text.strip()
        if not text.lower().startswith(PREFIX):
            return False

        # Extract command part (after prefix, before space)
        after_prefix = text[len(PREFIX):]
        parts = after_prefix.split(None, 1)
        if not parts:
            return False

        matched_cmd = parts[0].lower()
        return matched_cmd in flt.commands

    return filters.create(func, commands=commands)


def get_args(message: Message) -> str:
    """Extract arguments after the command.

    m!p never gonna give you up → "never gonna give you up"
    m!skip → ""
    """
    if not message.text:
        return ""
    text = message.text.strip()
    if not text.lower().startswith(PREFIX):
        return ""
    after_prefix = text[len(PREFIX):]
    parts = after_prefix.split(None, 1)
    return parts[1] if len(parts) > 1 else ""
