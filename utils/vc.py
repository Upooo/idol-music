"""Voice chat participant utilities using Pyrogram raw API."""
from __future__ import annotations

import logging

log = logging.getLogger(__name__)


async def get_vc_participant_count(assistant, chat_id: int) -> int:
    """Get the number of VC participants (excluding the assistant).

    Returns >= 0 on success, -1 if unknown.
    """
    try:
        from pyrogram.raw.functions.phone import GetGroupParticipants
        from pyrogram.raw.types import InputGroupCall

        peer = await assistant.resolve_peer(chat_id)

        if hasattr(peer, "channel_id"):
            from pyrogram.raw.functions.channels import GetFullChannel
            full = await assistant.invoke(GetFullChannel(channel=peer))
        elif hasattr(peer, "chat_id"):
            from pyrogram.raw.functions.messages import GetFullChat
            full = await assistant.invoke(GetFullChat(chat_id=peer.chat_id))
        else:
            return -1

        call = getattr(full.full_chat, "call", None)
        if call is None:
            return 0

        result = await assistant.invoke(
            GetGroupParticipants(
                call=InputGroupCall(id=call.id, access_hash=call.access_hash),
                ids=[],
                sources=[],
                offset="",
                limit=100,
            )
        )
        return max(0, result.count - 1)
    except Exception as exc:
        log.debug("Failed to get VC participants for %s: %s", chat_id, exc)
        return -1
