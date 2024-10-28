
import anyio
import pytest

from runner_with_api.helpers import AnyioDeque


@pytest.mark.asyncio
async def test_deque():
    deque = AnyioDeque[int](1)

    async def put_latest():
        for i in range(10):
            await deque.put(i)
            await anyio.sleep(0.1)

    async with anyio.create_task_group() as tg:
        tg.start_soon(put_latest)
        assert 0 == await deque.get()
        assert 1 == await deque.get()
        await anyio.sleep(1)
        assert 9 == await deque.get()
