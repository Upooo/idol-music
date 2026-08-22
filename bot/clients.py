"""Pyrogram clients — bot + assistant + PyTgCalls.

Factory functions to avoid module-level side effects.
"""

from pyrogram import Client
from pytgcalls import PyTgCalls

from config import config


def create_bot() -> Client:
    return Client(
        name="idol_bot",
        api_id=config.api_id,
        api_hash=config.api_hash,
        bot_token=config.bot_token,
    )


def create_assistant() -> Client:
    return Client(
        name="idol_assistant",
        api_id=config.api_id,
        api_hash=config.api_hash,
        session_string=config.assistant_session,
        no_updates=True,  # assistant doesn't need to receive messages
    )


def create_calls(assistant: Client) -> PyTgCalls:
    return PyTgCalls(assistant)
