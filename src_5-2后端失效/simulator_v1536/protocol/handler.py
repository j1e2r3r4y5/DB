from abc import ABC, abstractmethod
from typing import Optional, Dict, Callable
import logging

logger = logging.getLogger(__name__)


class ProtocolHandler(ABC):
    def __init__(self):
        self._next_handler: Optional['ProtocolHandler'] = None

    @abstractmethod
    def handle(self, payload: bytes) -> Optional[bytes]:
        pass

    @abstractmethod
    def get_function_code(self) -> int:
        pass

    def set_next(self, handler: 'ProtocolHandler') -> 'ProtocolHandler':
        self._next_handler = handler
        return handler

    def _handle_next(self, payload: bytes) -> Optional[bytes]:
        if self._next_handler:
            return self._next_handler.handle(payload)
        return None


class HandlerRegistry:
    def __init__(self):
        self._handlers: Dict[int, ProtocolHandler] = {}
        self._default_handler: Optional[ProtocolHandler] = None

    def register(self, handler: ProtocolHandler) -> bool:
        code = handler.get_function_code()
        self._handlers[code] = handler
        logger.debug(f"Registered handler for function code: {code:#x}")
        return True

    def unregister(self, function_code: int) -> bool:
        if function_code in self._handlers:
            del self._handlers[function_code]
            return True
        return False

    def get(self, function_code: int) -> Optional[ProtocolHandler]:
        return self._handlers.get(function_code)

    def set_default(self, handler: ProtocolHandler):
        self._default_handler = handler

    def handle(self, payload: bytes) -> Optional[bytes]:
        if not payload or len(payload) < 1:
            logger.warning("Empty payload received")
            return None

        function_code = payload[0]
        handler = self._handlers.get(function_code)

        if handler:
            return handler.handle(payload)

        if self._default_handler:
            return self._default_handler.handle(payload)

        logger.warning(f"No handler found for function code: {function_code:#x}")
        return None

    @property
    def handlers(self) -> Dict[int, ProtocolHandler]:
        return self._handlers.copy()