import pytest
from unittest.mock import MagicMock
from music.manager import SessionManager


@pytest.mark.asyncio
async def test_same_group_same_session():
    calls = MagicMock()
    mgr = SessionManager(calls)
    s1 = mgr.get(-1001)
    s2 = mgr.get(-1001)
    assert s1 is s2


@pytest.mark.asyncio
async def test_different_groups():
    calls = MagicMock()
    mgr = SessionManager(calls)
    a = mgr.get(-1001)
    b = mgr.get(-1002)
    assert a is not b
    assert a.chat_id == -1001
    assert b.chat_id == -1002
