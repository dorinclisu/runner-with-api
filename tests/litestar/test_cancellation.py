import logging

import pytest
from anyio import get_cancelled_exc_class, move_on_after, sleep
from httpx import ASGITransport, AsyncClient
from litestar import Litestar, get
from litestar.background_tasks import BackgroundTask
from litestar.testing import AsyncTestClient

# nothing to import as Litestar seems to already implement handler cancellation


app = Litestar()


async def background_task() -> None:
    app.state.cancelled_background = False
    try:
        await sleep(1)
    except get_cancelled_exc_class():
        logging.info('Cancelled BackgroundTask')
        app.state.cancelled_background = True
        raise


@get('/test',
    background=BackgroundTask(background_task),
)
async def handler() -> bool:
    app.state.cancelled = False
    try:
        await sleep(0.5)
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
    assert app.state.cancelled_background is False


@pytest.mark.anyio
async def test_cancelled(client: AsyncTestClient | AsyncClient):
    app.state.cancelled_background = None

    with move_on_after(0.1) as scope:
        await client.get('/test')

    assert scope.cancelled_caught
    assert app.state.cancelled is True
    assert app.state.cancelled_background is None  # background was not even started
