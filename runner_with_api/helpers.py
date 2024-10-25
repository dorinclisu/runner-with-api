
from typing import Generic, TypeVar
import anyio


T = TypeVar('T')


class AsyncLatest(Generic[T]):
    """
    Set generic value from one async task, get it from another.
    This provides a simple alternative to memory object streams with max_buffer_size=1 which cannot be overwritten
    with the latest value.
    """
    def __init__(self) -> None:
        self.data: T | None = None
        self.available = False
        self.condition = anyio.Condition()


    async def set(self, data: T) -> None:
        """Does not really block, but needs to be async for the internal synchronization primitives."""
        async with self.condition:
            self.data = data
            self.available = True
            self.condition.notify_all()


    async def get(self) -> T:
        """Wait for new data or return latest data if already available (since last get)."""
        async with self.condition:
            if not self.available:
                await self.condition.wait()

            data = self.data
            self.available = False

            assert data is not None
            return data
