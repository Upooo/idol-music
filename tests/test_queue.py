import pytest
from music.queue import MusicQueue, QueueFull
from music.track import Track


def _t(title: str) -> Track:
    return Track(title=title, url=f"https://ex/{title}")


@pytest.mark.asyncio
async def test_fifo():
    q = MusicQueue(max_size=10)
    await q.put(_t("A"))
    await q.put(_t("B"))
    await q.put(_t("C"))
    assert (await q.get()).title == "A"
    assert (await q.get()).title == "B"
    assert (await q.get()).title == "C"
    assert await q.get() is None


@pytest.mark.asyncio
async def test_max_size():
    q = MusicQueue(max_size=2)
    await q.put(_t("A"))
    await q.put(_t("B"))
    with pytest.raises(QueueFull):
        await q.put(_t("C"))


@pytest.mark.asyncio
async def test_clear():
    q = MusicQueue()
    await q.put(_t("A"))
    await q.clear()
    assert await q.is_empty()
