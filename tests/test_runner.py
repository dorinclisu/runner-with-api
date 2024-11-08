from unittest.mock import Mock

import pytest
from anyio import sleep, get_cancelled_exc_class

from runner_with_api import ASGIRunner



@pytest.mark.anyio
async def test_lifespan() -> None:
    class MyRunner(ASGIRunner):
        def __init__(self):
            self.initialized = False
            self.running = False
            self.cancelled = False

        async def init(self):
            await sleep(0.1)
            self.initialized = True

        async def run(self):
            self.running = True
            try:
                while True:
                    await sleep(0.1)
            except get_cancelled_exc_class():
                self.cancelled = True
            finally:
                self.running = False

    runner = MyRunner()

    async with runner.lifespan(Mock()):
        initialized = runner.initialized
        await sleep(0)
        running = runner.running
        cancelled = runner.cancelled

    assert initialized
    assert running
    assert not cancelled

    assert runner.cancelled
    assert not runner.running


@pytest.mark.anyio
async def test_lifespan_error() -> None:
    class ErrorRunner(ASGIRunner):
        def __init__(self):
            self.shutdown = False

        def _shutdown(self):
            self.shutdown = True

    class ErrorInit(ErrorRunner):
        async def init(self):
            raise RuntimeError

    class ErrorRun(ErrorRunner):
        async def run(self):
            raise RuntimeError

    error_init = ErrorInit()
    error_run = ErrorRun()

    with pytest.raises(RuntimeError):
        async with error_init.lifespan(Mock()):
            await sleep(0)
    assert error_init.shutdown

    async with error_run.lifespan(Mock()):
        await sleep(0)
    assert error_run.shutdown
