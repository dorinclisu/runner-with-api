import copy
import logging
import types
from functools import cached_property

from litestar.handlers import BaseRouteHandler

from .. import ASGIRunner



logger = logging.getLogger(__name__)


class LitestarAsyncRunner(ASGIRunner):
    """Async process runner bound to Litestar"""

    def _handlers(self) -> list[BaseRouteHandler]:
        handlers = []
        for name in dir(self):
            if name == 'handlers':  # avoid infinite recursion with the property
                continue
            method = getattr(self, name)

            if isinstance(method, BaseRouteHandler):
                handlers.append(method)

        handlers.sort(key=lambda h: h.handler_id)
        return handlers


    def _bind(self, handler: BaseRouteHandler) -> BaseRouteHandler:
        handler = copy.deepcopy(handler)
        handler._fn = types.MethodType(handler._fn, self)
        return handler


    @cached_property
    def handlers(self) -> list[BaseRouteHandler]:
        """Get all route handlers created by decorating the methods, bound to the runner."""
        return [self._bind(handler) for handler in self._handlers()]
