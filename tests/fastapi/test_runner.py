import logging

import pytest
from anyio import sleep
from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient

from runner_with_api.fastapi import FastapiAsyncRunner



router = APIRouter()


class MyRunner(FastapiAsyncRunner):
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


    @router.put('/config')
    async def configure(self, config: dict) -> None:
        logging.info('Configuring process')
        self.config = config.copy()


    @router.get('/config')
    async def get_config(self) -> dict:
        logging.info(self.config)
        return self.config


runner = MyRunner()
runner.patch_fastapi_router(router)

api = FastAPI(lifespan=runner.lifespan)
api.include_router(router)


###################################################################################################
def test_configure():
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
