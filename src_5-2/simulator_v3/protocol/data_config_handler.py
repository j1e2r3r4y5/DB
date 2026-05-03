from typing import Optional, List
import struct
import logging

from .handler import ProtocolHandler

logger = logging.getLogger(__name__)


class DataConfig:
    def __init__(self, slave_id: int, func_code: int, start_addr: int, quantity: int):
        self.slave_id = slave_id
        self.func_code = func_code
        self.start_addr = start_addr
        self.quantity = quantity

    def __repr__(self):
        return f"DataConfig(slave={self.slave_id}, func={self.func_code}, addr={self.start_addr}, qty={self.quantity})"


class DataConfigHandler(ProtocolHandler):
    DATA_CONFIG_QUERY = 0x03
    DATA_CONFIG_UPLOAD = 0x03
    DOWNLOAD_DATA_CONFIG = 0x04
    CONFIG_RESULT = 0x04

    def __init__(self, config_manager=None):
        super().__init__()
        self.config_manager = config_manager
        self._pending_configs: List[DataConfig] = []

    def get_function_code(self) -> int:
        return self.DOWNLOAD_DATA_CONFIG

    def handle(self, payload: bytes) -> Optional[bytes]:
        if not payload or len(payload) < 1:
            return None

        func_code = payload[0]

        if func_code == self.DATA_CONFIG_QUERY:
            return self._handle_data_config_query(payload)
        elif func_code == self.DATA_CONFIG_UPLOAD:
            return self._handle_data_config_upload(payload)
        elif func_code == self.DOWNLOAD_DATA_CONFIG:
            return self._handle_download_data_config(payload)
        elif func_code == self.CONFIG_RESULT:
            return self._handle_config_result(payload)

        return self._handle_next(payload)

    def _handle_data_config_query(self, payload: bytes) -> Optional[bytes]:
        logger.info("[DOWNLINK] Data config query received")
        return None

    def _handle_data_config_upload(self, payload: bytes) -> Optional[bytes]:
        logger.info("[DOWNLINK] Data config upload received")
        return None

    def _handle_download_data_config(self, payload: bytes) -> Optional[bytes]:
        if len(payload) < 3:
            logger.warning("Invalid data config payload: too short")
            return None

        try:
            group_count = struct.unpack('>H', payload[1:3])[0]

            logger.info(f"[DOWNLINK] Download data config: {group_count} groups")

            config_groups = []
            offset = 3

            for i in range(group_count):
                if offset + 6 > len(payload):
                    logger.warning(f"Incomplete data config at group {i}")
                    break

                slave_id = payload[offset]
                data_type = payload[offset + 1]
                start_addr = struct.unpack('>H', payload[offset + 2:offset + 4])[0]
                quantity = struct.unpack('>H', payload[offset + 4:offset + 6])[0]

                config = DataConfig(slave_id, data_type, start_addr, quantity)
                config_groups.append(config)

                logger.debug(f"  Group {i}: slave={slave_id}, type={data_type}, addr={start_addr}, qty={quantity}")

                offset += 6

            if self.config_manager:
                for config in config_groups:
                    self.config_manager.add_data_config(config)

            response = self._build_config_result(0x00)
            logger.info(f"[UPLINK] Config result: success ({len(config_groups)} groups)")
            return response

        except struct.error as e:
            logger.error(f"Failed to parse data config: {e}")
            return None
        except Exception as e:
            logger.error(f"Error handling data config: {e}")
            return None

    def _handle_config_result(self, payload: bytes) -> Optional[bytes]:
        if len(payload) < 2:
            return None

        result = payload[1]

        if result == 0x00:
            logger.info(f"[UPLINK] Config result: success")
        else:
            logger.warning(f"[UPLINK] Config result: failure (result={result})")

        return None

    def _build_config_result(self, result: int) -> bytes:
        return bytes([self.CONFIG_RESULT, result])

    def create_data_config_upload(self, configs: List[DataConfig]) -> bytes:
        payload = bytes([self.DATA_CONFIG_UPLOAD])
        payload += struct.pack('>H', len(configs))

        for config in configs:
            payload += bytes([config.slave_id, config.func_code])
            payload += struct.pack('>HH', config.start_addr, config.quantity)

        return payload

    def create_data_config_query(self) -> bytes:
        return bytes([self.DATA_CONFIG_QUERY])

    @property
    def pending_configs(self) -> List[DataConfig]:
        return self._pending_configs.copy()

    def clear_pending_configs(self):
        self._pending_configs.clear()