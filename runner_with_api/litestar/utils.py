from __future__ import annotations
from types import MethodType
from typing import Awaitable, Generic, TypeVar

from litestar.background_tasks import BackgroundTask, BackgroundTasks
from litestar.response import Response, Stream
from litestar.serialization import encode_json
from litestar.types import ResponseHeaders
try:
    from pydantic import BaseModel
except ImportError:
    class BaseModel: ...  # type: ignore[no-redef]

from ..utils import http_long_polling



T = TypeVar('T')

class LongPollingResponse(Response[T], Generic[T]):
    """Subclass of Response"""

    def __init__(self, func: Awaitable[T], keepalive=1.,
        status_code: int = 200,
        headers: "ResponseHeaders | None" = None,
        background: BackgroundTask | BackgroundTasks | None = None
    ):
        """Keep the connection alive until awaitable func returns the final response.
        The function must return a msgspec, pydantic model or a json serializable object.
        """
        async def response_serialized() -> bytes:
            response = await func
            return LongPollingResponse.serialize(response)

        # for Stream()
        # super().__init__(
        #     http_long_polling(response_serialized(), b'\n', keepalive),
        #     media_type='application/json',
        #     status_code=status_code,
        #     headers=headers,
        #     background=background
        # )

        super().__init__(
            b'',  # type: ignore[arg-type]
            background=background,
            headers=headers,
            media_type='application/json',
            status_code=status_code,
        )
        self.iterator = http_long_polling(response_serialized(), b'\n', keepalive)
        self.to_asgi_response = MethodType(Stream.to_asgi_response, self)  # type: ignore[method-assign]


    @staticmethod
    def serialize(response: T) -> bytes:
        if isinstance(response, BaseModel):
            return response.model_dump_json().encode()
        return encode_json(response)
