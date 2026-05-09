from typing import Optional
import logging
import time

from .handler import ProtocolHandler

logger = logging.getLogger(__name__)


class HeartbeatHandler(ProtocolHandler):
    HEARTBEAT_FUNCTION_CODE = 0x00

    def __init__(self):
        super().__init__()
        self._last_heartbeat_time: Optional[float] = None
        self._heartbeat_count = 0

    def get_function_code(self) -> int:
        return self.HEARTBEAT_FUNCTION_CODE

    def handle(self, payload: bytes) -> Optional[bytes]:
        if len(payload) < 1:
            return None

        func_code: int = payload[0]

        if func_code == self.HEARTBEAT_FUNCTION_CODE:
            return self._handle_heartbeat(payload)

        return self._handle_next(payload)

    def _handle_heartbeat(self, payload: bytes) -> bytes:
        self._last_heartbeat_time = time.time()
        self._heartbeat_count += 1
        logger.info(f"[UPLINK] Heartbeat sent: {self._heartbeat_count:02d}")
        return bytes([self.HEARTBEAT_FUNCTION_CODE])

    def get_last_heartbeat_time(self) -> Optional[float]:
        return self._last_heartbeat_time

    def get_heartbeat_count(self) -> int:
        return self._heartbeat_count

    def reset_count(self):
        self._heartbeat_count = 0
        logger.debug("Heartbeat count reset")

    @property
    def time_since_last_heartbeat(self) -> Optional[float]:
        if self._last_heartbeat_time is None:
            return None
        return time.time() - self._last_heartbeat_time