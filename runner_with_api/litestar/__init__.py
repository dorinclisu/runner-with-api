import logging
import types

from litestar.handlers import BaseRouteHandler

from .. import ASGIRunner



logger = logging.getLogger(__name__)


class LitestarAsyncRunner(ASGIRunner):
    """Async process runner bound to Litestar"""

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
