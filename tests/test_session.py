import pytest
from unittest.mock import AsyncMock, MagicMock
from music.session import MusicSession
from music.track import Track
from music.queue import QueueFull


class FakeCalls:
    pass


def _t(title: str, autoplay: bool = False) -> Track:
    return Track(title=title, url=f"https://ex/{title}", is_autoplay=autoplay)


@pytest.mark.asyncio
async def test_stop_clears():
    sess = MusicSession(-1001, FakeCalls())
    sess.player.play = AsyncMock()
    sess.player.stop = AsyncMock()
    sess.player.is_playing = True
    sess.player.current = _t("A")
    sess.autoplay_enabled = True
    await sess.queue.put(_t("B"))
    await sess.queue.put(_t("C"))

    await sess.stop()

    assert sess.autoplay_enabled is False
    assert await sess.queue.is_empty()
    sess.player.stop.assert_awaited()


@pytest.mark.asyncio
async def test_queue_limit():
    sess = MusicSession(-1002, FakeCalls())
    sess.player.is_playing = True
    sess.player.current = _t("Playing")
    sess.autoplay_enabled = True
    for i in range(5):
        await sess.queue.put(_t(f"M{i}"))
    with pytest.raises(QueueFull):
        await sess.add_and_play(_t("Extra"))
    assert sess.autoplay_enabled is False
