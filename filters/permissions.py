"""Permission helpers — developer, group admin.

V1 practical model (VC participant API unreliable on this stack):
- m!p / m!play : any group member
- m!np         : anyone (read-only)
- pause/resume/skip/stop/autoplay : group admin or developer
- developer commands : developer only

VC membership helpers are kept for a future version but are NOT
used to gate control in V1.
"""
from __future__ import annotations

import logging
from typing import Tuple

from pyrogram import Client
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import ChatMember

from config import config

log = logging.getLogger(__name__)


def is_developer(user_id: int) -> bool:
    return user_id == config.developer_id


async def is_group_admin(client: Client, chat_id: int, user_id: int) -> bool:
    try:
        member: ChatMember = await client.get_chat_member(chat_id, user_id)
        return member.status in (
            ChatMemberStatus.OWNER,
            ChatMemberStatus.ADMINISTRATOR,
        )
    except Exception as exc:
        log.debug("is_group_admin failed: %s", exc)
        return False


async def can_play(client: Client, chat_id: int, user_id: int) -> Tuple[bool, str]:
    """Anyone in the group may request a track (V1)."""
    if is_developer(user_id):
        return True, ""
    return True, ""


async def can_control(client: Client, chat_id: int, user_id: int) -> Tuple[bool, str]:
    """pause / resume / skip / stop / autoplay — admin or developer."""
    if is_developer(user_id):
        return True, ""
    if await is_group_admin(client, chat_id, user_id):
        return True, "admin"
    return False, "admin_only"


async def can_stop(client: Client, chat_id: int, user_id: int) -> Tuple[bool, str]:
    return await can_control(client, chat_id, user_id)


# Backwards-compatible aliases used by older handler code
async def can_control_music(client, chat_id, user_id, bot_in_vc=False):
    return await can_control(client, chat_id, user_id)
