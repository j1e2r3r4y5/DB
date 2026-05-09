from typing import Optional
import struct
import logging
import time

from .handler import ProtocolHandler

logger = logging.getLogger(__name__)


class RemoteWriteError(Exception):
    """Base exception for remote write errors"""
    def __init__(self, message: str, error_code: int, details: dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class PayloadParseError(RemoteWriteError):
    """Exception for payload parsing errors"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code=0xE1, details=details)


class ModbusWriteError(RemoteWriteError):
    """Exception for Modbus write operation errors"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, error_code=0xE2, details=details)


class UnsupportedDataTypeError(RemoteWriteError):
    """Exception for unsupported data type errors"""
    def __init__(self, data_type: int):
        details = {"data_type": data_type}
        super().__init__(f"Unsupported data type: {data_type}", error_code=0xE3, details=details)


class RemoteWriteHandler(ProtocolHandler):
    REMOTE_WRITE = 0x06
    ERROR_CODE_SUCCESS = 0
    ERROR_CODE_PARSE_FAILED = 1
    ERROR_CODE_WRITE_FAILED = 2
    ERROR_CODE_UNSUPPORTED_TYPE = 3

    def __init__(self, modbus_master=None):
        super().__init__()
        self.modbus_master = modbus_master

    def get_function_code(self) -> int:
        return self.REMOTE_WRITE

    def handle(self, payload: bytes) -> Optional[bytes]:
        if not payload or len(payload) < 1:
            return None

        func_code = payload[0]

        if func_code == self.REMOTE_WRITE:
            return self._handle_remote_write(payload)

        return self._handle_next(payload)

    def _handle_remote_write(self, payload: bytes) -> Optional[bytes]:
        if len(payload) < 7:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            logger.error(f"[{timestamp}] Invalid remote write payload: too short (length={len(payload) if payload else 0})")
            return self._build_error_response(self.ERROR_CODE_PARSE_FAILED, {"reason": "payload_too_short"})

        try:
            data_type = payload[1]
            address = struct.unpack('>H', payload[2:4])[0]
            quantity = struct.unpack('>H', payload[4:6])[0]

            if data_type not in (0, 4):
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                logger.warning(f"[{timestamp}] Unsupported data type: {data_type}")
                return self._build_error_response(
                    self.ERROR_CODE_UNSUPPORTED_TYPE,
                    {"data_type": data_type, "address": address}
                )

            if data_type == 0:
                value = payload[6]
            else:
                value = struct.unpack('>H', payload[6:8])[0]

            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"[{timestamp}] [DOWNLINK] Remote write: type={data_type}, addr={address}, qty={quantity}, value={value}")

            success = False
            write_error_details = {}

            if self.modbus_master:
                if data_type == 0:
                    success = self.modbus_master.write_single_coil(1, address, bool(value & 0x01))
                elif data_type == 4:
                    success = self.modbus_master.write_single_register(1, address, value)
            else:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                logger.warning(f"[{timestamp}] No Modbus master configured for remote write")
                write_error_details = {"reason": "modbus_master_not_configured"}

            if success:
                status = self.ERROR_CODE_SUCCESS
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"[{timestamp}] [UPLINK] Remote write result: success (status={status})")
            else:
                status = self.ERROR_CODE_WRITE_FAILED
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                logger.warning(f"[{timestamp}] [UPLINK] Remote write result: failure (status={status}), details={write_error_details}")

            response = bytes([self.REMOTE_WRITE, data_type]) + struct.pack('>H', address) + struct.pack('>H', quantity) + bytes([status])
            return response

        except struct.error as e:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            logger.error(f"[{timestamp}] Failed to parse remote write payload: {type(e).__name__}: {e}, payload={payload.hex() if payload else 'None'}")
            return self._build_error_response(self.ERROR_CODE_PARSE_FAILED, {"error": str(e), "error_type": type(e).__name__})

        except ModbusWriteError as e:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            logger.error(f"[{timestamp}] Modbus write error: error_code={e.error_code}, details={e.details}")
            return self._build_error_response(self.ERROR_CODE_WRITE_FAILED, e.details)

        except Exception as e:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            logger.error(f"[{timestamp}] Unexpected error handling remote write: {type(e).__name__}: {e}, payload={payload.hex() if payload else 'None'}")
            return self._build_error_response(self.ERROR_CODE_PARSE_FAILED, {"error": str(e), "error_type": type(e).__name__})

    def _build_error_response(self, error_code: int, details: dict) -> bytes:
        response = bytes([self.REMOTE_WRITE, 0xFF]) + struct.pack('>H', 0) + struct.pack('>H', 1) + bytes([error_code])
        return response

    def create_remote_write(self, slave_id: int, data_type: int, address: int, value: int) -> bytes:
        payload = bytes([self.REMOTE_WRITE, data_type])
        payload += struct.pack('>H', address)
        payload += struct.pack('>H', 1)
        if data_type == 0:
            payload += bytes([value & 0x01])
        else:
            payload += struct.pack('>H', value)
        return payload