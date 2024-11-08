
import pytest
from anyio import sleep, move_on_after, get_cancelled_exc_class
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI, Request

from runner_with_api.fastapi.cancellation import cancel_on_disconnect



app = FastAPI()


@app.get('/test')
async def cancellable(r: Request):
    app.state.cancelled = False
    async with cancel_on_disconnect(r):
        try:
            await sleep(0.2)
        except get_cancelled_exc_class():
            app.state.cancelled = True
            raise

###################################################################################################
#pytestmark = pytest.mark.anyio

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://fastapi.local') as client:
        yield client


@pytest.mark.anyio
async def test_cancelled(client: AsyncClient):
    r = await client.get('/test')

    assert not app.state.cancelled

    with move_on_after(0.1) as scope:
        await client.get('/test')

    assert scope.cancelled_caught
    assert app.state.cancelled
