from collections import deque
from typing import AsyncGenerator, Coroutine, Deque, Generic, TypeVar
import anyio



T = TypeVar('T')

class AnyioDeque(Generic[T]):
    """
    Based on collections.deque with anyio synchronization primitives.
    """
    def __init__(self, maxlen: int) -> None:
        self.deque: Deque[T] = deque(maxlen=maxlen)
        self.condition = anyio.Condition()


    async def put(self, data: T) -> None:
        """Append to the internal deque. If maxlen is reached, the oldest item is removed.
        Does not really block, but needs to be async for the internal synchronization primitives."""
        async with self.condition:
            self.deque.append(data)
            self.condition.notify_all()


    async def get(self) -> T:
        """Popleft from the internal deque. Wait for producer if deque is empty."""
        async with self.condition:
            while not self.deque:
                await self.condition.wait()

            data = self.deque.popleft()
            return data


T1 = TypeVar('T1')
T2 = TypeVar('T2')

async def http_long_polling(func: Coroutine[None, None, T1], keepalive_yield: T2, keepalive_period=1.
) -> AsyncGenerator[T1 | T2, None]:
    """Wait for the result of func, while yielding {keepalive_yield} every {keepalive_period} seconds.
    Once the result is available, yield it and return.
    """
    event = anyio.Event()

    async def func_wrapper() -> None:
        event.result = await func  # type: ignore[attr-defined]
        event.set()

    async with anyio.create_task_group() as tg:
        tg.start_soon(func_wrapper)

        while True:
            with anyio.move_on_after(keepalive_period):
                await event.wait()
                yield event.result  # type: ignore[attr-defined]
                return

            yield keepalive_yield
