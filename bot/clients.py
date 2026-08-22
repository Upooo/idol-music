"""Pyrogram clients — bot + assistant + PyTgCalls."""

from pyrogram import Client
from pytgcalls import PyTgCalls

from config import config

# Bot client — handles commands and messages
bot = Client(
    name="idol_bot",
    api_id=config.api_id,
    api_hash=config.api_hash,
    bot_token=config.bot_token,
)

# Assistant client — joins voice chats (userbot)
assistant = Client(
    name="idol_assistant",
    api_id=config.api_id,
    api_hash=config.api_hash,
    session_string=config.assistant_session,
)

# PyTgCalls — voice chat engine, bound to assistant
calls = PyTgCalls(assistant)
