from __future__ import annotations
import logging

import pytest
from anyio import get_cancelled_exc_class, move_on_after, sleep
from httpx import ASGITransport, AsyncClient
from litestar import Litestar, Request, get
from litestar.testing import AsyncTestClient

from runner_with_api.litestar.cancellation import cancel_on_disconnect



app = Litestar()


@get('/test')
async def handler(request: Request) -> bool:
    app.state.cancelled = False
    async with cancel_on_disconnect(request):
        try:
            await sleep(0.2)
        except get_cancelled_exc_class():
            logging.info('Cancelled Handler')
            app.state.cancelled = True
            raise

    return True


app.register(handler)

###################################################################################################
@pytest.fixture
async def client():
    #async with AsyncTestClient(app=app) as client:  # this does not propagate cancellation
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://litestar.local') as client:
        yield client


@pytest.mark.anyio
async def test_regular(client: AsyncTestClient | AsyncClient):
    r = await client.get('/test')

    assert r.json()
    assert app.state.cancelled is False


@pytest.mark.anyio
async def test_cancelled(client: AsyncTestClient | AsyncClient):
    app.state.cancelled_background = None

    with move_on_after(0.1) as scope:
        await client.get('/test')

    assert scope.cancelled_caught
    assert app.state.cancelled is True
