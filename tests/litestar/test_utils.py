from __future__ import annotations

import msgspec
import pytest
from anyio import sleep
from litestar import Litestar, get
from litestar.testing import AsyncTestClient
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import RapidocRenderPlugin
from pydantic import BaseModel

from runner_with_api.litestar.utils import LongPollingResponse



@get('/polling')
async def polling() -> LongPollingResponse[bool]:
    async def func() -> bool:
        await sleep(0.3)
        return True

    return LongPollingResponse(func(), keepalive=0.1)


app = Litestar(
    [polling],
    openapi_config=OpenAPIConfig(
        title="Litestar Long Polling",
        version="0.1.0",
        render_plugins=[RapidocRenderPlugin()],
    ),
)

###################################################################################################
@pytest.fixture
async def client():
    async with AsyncTestClient(app=app) as client:
        yield client


@pytest.mark.anyio
async def test_polling(client: AsyncTestClient):
    r = await client.get('/polling')
    assert r.json() is True


def test_polling_serialization() -> None:
    class MsgspecModel(msgspec.Struct):
        data: list[int] = msgspec.field(default_factory=list)

    class PydanticModel(BaseModel):
        data: list[int] = []

    serialized = b'{"data":[]}'
    assert LongPollingResponse.serialize(MsgspecModel()) == serialized
    assert LongPollingResponse.serialize(PydanticModel()) == serialized
