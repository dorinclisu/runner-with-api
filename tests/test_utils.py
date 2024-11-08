
import pytest
from anyio import create_task_group, sleep

from runner_with_api.utils import AnyioDeque, http_long_polling


@pytest.mark.anyio
async def test_deque():
    deque = AnyioDeque[int](1)

    n = 5
    assert n > 3
    t = 0.1

    async def put_latest():
        for i in range(n):
            await deque.put(i)
            await sleep(t)

    async with create_task_group() as tg:
        tg.start_soon(put_latest)
        assert 0 == await deque.get()
        assert 1 == await deque.get()
        await sleep(n*t)
        assert n-1 == await deque.get()


@pytest.mark.anyio
async def test_long_polling():
    period = 0.1
    n = 2

    async def my_task():
        await sleep(period * (n + 0.5))
        return 42

    i = 0
    async for event in http_long_polling(my_task(), keepalive_yield='\n', keepalive_period=period):
        if i < n:
            assert event == '\n', i
        else:
            assert event == 42, i
        i += 1
