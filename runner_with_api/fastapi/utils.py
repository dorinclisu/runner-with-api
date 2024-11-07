from __future__ import annotations
import json
from typing import Awaitable, Generic, Mapping, TypeVar

from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

from ..utils import http_long_polling



T = TypeVar('T')

class LongPollingResponse(StreamingResponse, Generic[T]):
    """Subclass of StreamingResponse"""

    def __init__(self, func: Awaitable[T], keepalive=1.,
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        background: BackgroundTask | None = None
    ):
        """Keep the connection alive until awaitable func returns the final response.
        The function must return a pydantic model or a json serializable object.
        """
        async def response_serialized() -> str:
            response = await func

            if isinstance(response, BaseModel):
                return response.model_dump_json()

            return json.dumps(jsonable_encoder(response))

        super().__init__(
            http_long_polling(response_serialized(), '\n', keepalive),
            media_type='application/json',
            status_code=status_code,
            headers=headers,
            background=background
        )
