from typing import Optional
import struct
import logging

from .handler import ProtocolHandler

logger = logging.getLogger(__name__)


class ModuleConfigHandler(ProtocolHandler):
    QUERY_CONFIG_DOWN = 0x01
    UPLOAD_CONFIG_UP = 0x01
    DOWNLOAD_CONFIG_DOWN = 0x02
    CONFIG_RESULT_UP = 0x02

    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager

    def get_function_code(self) -> int:
        return self.DOWNLOAD_CONFIG_DOWN

    def handle(self, payload: bytes) -> Optional[bytes]:
        if not payload or len(payload) < 1:
            return None

        func_code = payload[0]

        if func_code == self.QUERY_CONFIG_DOWN:
            return self._handle_query_config(payload)
        elif func_code == self.UPLOAD_CONFIG_UP:
            return self._handle_upload_config(payload)
        elif func_code == self.DOWNLOAD_CONFIG_DOWN:
            return self._handle_download_config(payload)
        elif func_code == self.CONFIG_RESULT_UP:
            return self._handle_config_result(payload)

        return self._handle_next(payload)

    def _handle_query_config(self, payload: bytes) -> Optional[bytes]:
        logger.info("[DOWNLINK] Module config query received")
        return None

    def _handle_upload_config(self, payload: bytes) -> Optional[bytes]:
        logger.info("[DOWNLINK] Module config upload received")
        return None

    def _handle_download_config(self, payload: bytes) -> Optional[bytes]:
        if len(payload) < 4:
            logger.warning("Invalid module config payload: too short")
            return None

        try:
            send_mode = payload[1]
            config_data = struct.unpack('>H', payload[2:4])[0]
            baud = payload[4] if len(payload) > 4 else 0

            logger.info(f"[DOWNLINK] Download module config: send_mode={send_mode}, config_data={config_data:#x}, baud={baud}")

            if self.config_manager:
                self.config_manager.update_module_config(send_mode, config_data, baud)

            response = bytes([self.CONFIG_RESULT_UP, 0x00])
            logger.info(f"[UPLINK] Module config result: success")
            return response

        except struct.error as e:
            logger.error(f"Failed to parse module config: {e}")
            return None

    def _handle_config_result(self, payload: bytes) -> Optional[bytes]:
        if len(payload) < 2:
            return None

        result = payload[1]

        if result == 0x00:
            logger.info(f"[UPLINK] Module config result: success")
        else:
            logger.warning(f"[UPLINK] Module config result: failure (result={result})")

        return None

    def create_upload_config(self, send_mode: int, config_data: int, baud: int) -> bytes:
        payload = bytes([self.UPLOAD_CONFIG_UP, send_mode]) + struct.pack('>H', config_data) + bytes([baud])
        return payload

    def create_query_config(self) -> bytes:
        return bytes([self.QUERY_CONFIG_DOWN])