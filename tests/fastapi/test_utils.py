from __future__ import annotations

import pytest
from anyio import sleep
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI

from runner_with_api.fastapi.utils import LongPollingResponse



app = FastAPI()


@app.get('/polling', response_model=bool)
async def polling():
    async def func():
        await sleep(0.3)
        return True

    return LongPollingResponse(func(), keepalive=0.1)

###################################################################################################
@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://fastapi.local') as client:
        yield client


@pytest.mark.anyio
async def test_polling(client: AsyncClient):
    r = await client.get('/polling')
    assert r.json() is True
