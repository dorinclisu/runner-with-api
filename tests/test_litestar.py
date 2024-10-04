import logging

import pytest
from anyio import sleep
from litestar import Litestar, get, put
from litestar.testing import TestClient

from runner_with_api import AsyncRunnerWithAPI



class MyRunner(AsyncRunnerWithAPI):
    def __init__(self):
        self.initialized = False
        self.running = False


    async def init(self):
        logging.info('Initializing process ...')
        await sleep(1)
        self.config = {}
        self.initialized = True


    async def run(self) -> None:
        logging.info('Running ...')
        self.running = True
        try:
            while True:
                await sleep(1)
                logging.debug('looping ...')
        finally:
            self.running = False


    @put('/config')
    async def configure(self, data: dict) -> None:
        logging.info('Configuring process')
        self.config = data


    @get('/config')
    async def get_config(self) -> dict:
        return self.config


runner = MyRunner()

api = Litestar(runner.litestar_handlers(),
    lifespan=[runner.lifespan],
    debug=True
)


###################################################################################################
@pytest.mark.asyncio
async def test_configure():
    assert runner.initialized is False
    assert runner.running is False

    with TestClient(api) as client:
        assert runner.initialized is True

        config = {'a': 1, 'b': 2}

        r = client.put('/config', json=config)
        assert r.status_code == 200

        r = client.get('/config')
        assert r.status_code == 200
        assert r.json() == config

        assert runner.running is True

    assert runner.running is False
