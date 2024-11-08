from __future__ import annotations
import logging
import signal
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from anyio import create_task_group
from uvicorn._types import ASGIApplication



logger = logging.getLogger(__name__)


class ASGIRunner:
    """Base class for creating an async process runner bound to an ASGI application"""

    async def init(self) -> None:
        """Initialize the runner. The ASGI app will not service requests until this method is finished."""
        ...


    async def run(self) -> None:
        """Long running task. This should generally never return.
        Gets canceled by the lifespan function."""
        ...


    def _shutdown(self):
        """Request the process to shutdown.
        This is normally invoked by the lifespan function and does not need to be called by the user."""
        logger.debug('Sending SIGTERM to self')
        signal.raise_signal(signal.SIGTERM)  # currently the only way to shutdown uvicorn from code   # https://github.com/encode/uvicorn/discussions/1103


    @property
    def lifespan(self):
        """Lifespan context manager for the ASGIApplication (FastAPI, Litestar, Starlette, etc.).
        It uses a closure to capture self for calling the user methods: init() and run().
        The user methods are canceled when the ASGI app is shutting down.
        The shutdown is also triggered if an exception is raised by the user methods.
        """
        @asynccontextmanager
        async def _lifespan(app: ASGIApplication):
            try:
                await self.init()

                async with create_task_group() as tg:
                    tg.start_soon(self.run)
                    yield
                    logger.info('Canceling tasks')
                    tg.cancel_scope.cancel()
            except:
                logger.exception('Unexpected error, will request shutdown!')
                self._shutdown()

        return _lifespan


    def run_with_api(self, app: ASGIApplication | Any, **uvicorn_kwargs):
        """Run the API server while the runner lifespan is managed.
        Unix signal handlers are installed by uvicorn for graceful shutdown.
        Can pass uvicorn kwargs such as host, port, log_config.
        """
        uvicorn.run(app, **uvicorn_kwargs)
