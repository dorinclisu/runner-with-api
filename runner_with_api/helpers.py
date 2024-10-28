from collections import deque
from typing import Deque, Generic, TypeVar
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
        """Does not really block, but needs to be async for the internal synchronization primitives."""
        async with self.condition:
            self.deque.append(data)
            self.condition.notify_all()


    async def get(self) -> T:
        """Wait for producer if deque is empty."""
        async with self.condition:
            while not self.deque:
                await self.condition.wait()

            data = self.deque.popleft()
            return data
