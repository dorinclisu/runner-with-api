
import anyio
import pytest

from runner_with_api.helpers import AsyncLatest


@pytest.mark.asyncio
async def test_latest():
    latest = AsyncLatest[int]()

    async def set_latest():
        for i in range(10):
            await latest.set(i)
            await anyio.sleep(0.1)

    async with anyio.create_task_group() as tg:
        tg.start_soon(set_latest)
        assert 0 == await latest.get()
        assert 1 == await latest.get()
        await anyio.sleep(1)
        assert 9 == await latest.get()
