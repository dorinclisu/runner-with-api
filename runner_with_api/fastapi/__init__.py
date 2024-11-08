import logging
import types

from fastapi import APIRouter

from .. import ASGIRunner



logger = logging.getLogger(__name__)


class FastapiAsyncRunner(ASGIRunner):
    """Async process runner bound to FastAPI"""

    def patch_fastapi_router(self, router: APIRouter):
        """Patch the FastAPI router (used for decorating the methods) to bind the decorated methods to the class instance."""
        for route in router.routes:
            route.endpoint = types.MethodType(route.endpoint, self)  # type: ignore[attr-defined]
