import logging
import types
from functools import cached_property

from fastapi.routing import APIRouter, APIRoute

from .. import ASGIRunner



logger = logging.getLogger(__name__)
runner_router = APIRouter()


class FastapiAsyncRunner(ASGIRunner):
    """Async process runner bound to FastAPI"""

    def __new__(cls):
        """Ensure singleton to avoid mixed bindings of the module scope router."""
        if hasattr(cls, 'instance'):
            raise ValueError(f'{cls} is a singleton')
        cls.instance = super().__new__(cls)
        return cls.instance


    def bind_router(self, router: APIRouter):
        """Patch the FastAPI router (used for decorating the methods) to bind the decorated methods to the class instance."""
        route: APIRoute
        for route in router.routes:  # type: ignore[assignment]
            if isinstance(route.endpoint, types.MethodType):
                raise ValueError(f'{route} endpoint already bound to self')

            route.endpoint = types.MethodType(route.endpoint, self)


    @cached_property
    def router(self) -> APIRouter:
        """Return module-level runner_router with bound methods.
        This is just a convenience property equivalent to `FastapiAsyncRunner.bind_router(runner_router)`."""
        self.bind_router(runner_router)
        return runner_router
