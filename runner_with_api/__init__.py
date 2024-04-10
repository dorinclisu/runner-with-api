import logging
import signal
import types
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from anyio import create_task_group
from uvicorn._types import ASGIApplication

try:
    from fastapi import APIRouter
except ImportError:
    class APIRouter:  # type: ignore[no-redef]
        ...

try:
    from litestar.handlers import BaseRouteHandler
except ImportError:
    class BaseRouteHandler:  # type: ignore[no-redef]
        ...


logger = logging.getLogger(__name__)


class AsyncRunnerWithAPI:
    """Base class for creating an async runner bound to an ASGI (FastAPI, Litestar, etc.)"""

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
        """Lifespan context manager for the ASGIApplication (FastAPI, Litestar, etc.).
        It uses a closure to capture self for calling the user methods: init() and run().
        The user methods are canceled when the ASGI app is shutting down.
        The shutdown is also triggered if an exception is raised by the user methods.
        """
        @asynccontextmanager
        async def _lifespan(app: ASGIApplication):
            try:
                await self.init()

                async with create_task_group() as tg:
                    tg.start_soon(self.run)  # type: ignore[arg-type]
                    yield
                    logger.info('Canceling tasks')
                    tg.cancel_scope.cancel()
            except:
                logger.error('Unexpected error, will request shutdown!', exc_info=True)
                self._shutdown()

        return _lifespan


    def run_with_api(self, app: ASGIApplication | Any, host='127.0.0.1', port=8000):
        """Run the API listener on host:port while the runner lifespan is managed.
        Unix signal handlers are installed by uvicorn for graceful shutdown.
        """
        uvicorn.run(app, log_config=None, host=host, port=port)


    def patch_fastapi_router(self, router: APIRouter):
        """Patch the FastAPI router (used for decorating the methods) to bind the decorated methods to the class instance."""
        for route in router.routes:
            route.endpoint = types.MethodType(route.endpoint, self)  # type: ignore[attr-defined]


    def litestar_handlers(self) -> list[BaseRouteHandler]:
        """Get all route handlers created by decorating the methods, to be plugged into Litestar."""
        handlers: list[BaseRouteHandler] = []
        for name in dir(self):
            method = getattr(self, name)

            if isinstance(method, BaseRouteHandler):
                method._fn = types.MethodType(method._fn, self)
                handlers.append(method)

        handlers.sort(key=lambda h: h.handler_id)
        return handlers
