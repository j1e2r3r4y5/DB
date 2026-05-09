from typing import Optional, Tuple
import struct
import logging

logger = logging.getLogger(__name__)


class ModbusRequestHandler:
    FUNCTION_CODES = {
        0x01: 'read_coils',
        0x02: 'read_discrete_inputs',
        0x03: 'read_holding_registers',
        0x04: 'read_input_registers',
        0x05: 'write_single_coil',
        0x06: 'write_single_register',
        0x07: 'read_exception_status',
        0x08: 'diagnostics',
    }

    def __init__(self, device):
        self.device = device

    def parse_request(self, data: bytes) -> Optional[Tuple[int, int, bytes]]:
        if len(data) < 9:
            return None

        try:
            transaction_id = struct.unpack('>H', data[0:2])[0]
            protocol_id = struct.unpack('>H', data[2:4])[0]
            length = struct.unpack('>H', data[4:6])[0]
            unit_id = data[6]
            func_code = data[7]
            pdu_data = data[8:]

            return (transaction_id, unit_id, func_code, pdu_data)
        except struct.error as e:
            logger.error(f"Failed to parse request: {e}")
            return None

    def handle(self, data: bytes) -> Optional[bytes]:
        result = self.parse_request(data)
        if not result:
            return None

        transaction_id, unit_id, func_code, pdu_data = result

        if func_code == 0x01:
            return self._handle_read_coils(transaction_id, unit_id, pdu_data)
        elif func_code == 0x02:
            return self._handle_read_discrete_inputs(transaction_id, unit_id, pdu_data)
        elif func_code == 0x03:
            return self._handle_read_holding_registers(transaction_id, unit_id, pdu_data)
        elif func_code == 0x04:
            return self._handle_read_input_registers(transaction_id, unit_id, pdu_data)
        elif func_code == 0x05:
            return self._handle_write_single_coil(transaction_id, unit_id, pdu_data)
        elif func_code == 0x06:
            return self._handle_write_single_register(transaction_id, unit_id, pdu_data)
        elif func_code == 0x07:
            return self._handle_read_exception_status(transaction_id, unit_id)
        elif func_code == 0x08:
            return self._handle_diagnostics(transaction_id, unit_id, pdu_data)
        else:
            logger.warning(f"Unsupported function code: {func_code:#x}")
            return self._build_exception(transaction_id, unit_id, func_code, 0x01)

    def _handle_read_coils(self, transaction_id: int, unit_id: int, data: bytes) -> bytes:
        if len(data) < 4:
            return self._build_exception(transaction_id, unit_id, 0x01, 0x03)

        try:
            start_addr = struct.unpack('>H', data[0:2])[0]
            quantity = struct.unpack('>H', data[2:4])[0]

            if quantity < 1 or quantity > 2000:
                return self._build_exception(transaction_id, unit_id, 0x01, 0x02)

            coil_data = self.device.read_coils(start_addr, quantity)
            byte_count = len(coil_data)

            pdu = bytes([0x01, byte_count]) + coil_data
            header = struct.pack('>HHH', transaction_id, 0, len(pdu) + 1)
            return header + bytes([unit_id]) + pdu
        except Exception as e:
            logger.error(f"Error reading coils: {e}")
            return self._build_exception(transaction_id, unit_id, 0x01, 0x04)

    def _handle_read_discrete_inputs(self, transaction_id: int, unit_id: int, data: bytes) -> bytes:
        if len(data) < 4:
            return self._build_exception(transaction_id, unit_id, 0x02, 0x03)

        try:
            start_addr = struct.unpack('>H', data[0:2])[0]
            quantity = struct.unpack('>H', data[2:4])[0]

            if quantity < 1 or quantity > 2000:
                return self._build_exception(transaction_id, unit_id, 0x02, 0x02)

            input_data = self.device.read_discrete_inputs(start_addr, quantity)
            byte_count = len(input_data)

            pdu = bytes([0x02, byte_count]) + input_data
            header = struct.pack('>HHH', transaction_id, 0, len(pdu) + 1)
            return header + bytes([unit_id]) + pdu
        except Exception as e:
            logger.error(f"Error reading discrete inputs: {e}")
            return self._build_exception(transaction_id, unit_id, 0x02, 0x04)

    def _handle_read_holding_registers(self, transaction_id: int, unit_id: int, data: bytes) -> bytes:
        if len(data) < 4:
            return self._build_exception(transaction_id, unit_id, 0x03, 0x03)

        try:
            start_addr = struct.unpack('>H', data[0:2])[0]
            quantity = struct.unpack('>H', data[2:4])[0]

            if quantity < 1 or quantity > 125:
                return self._build_exception(transaction_id, unit_id, 0x03, 0x02)

            register_data = self.device.read_holding_registers(start_addr, quantity)
            byte_count = len(register_data)

            pdu = bytes([0x03, byte_count]) + register_data
            header = struct.pack('>HHH', transaction_id, 0, len(pdu) + 1)
            return header + bytes([unit_id]) + pdu
        except Exception as e:
            logger.error(f"Error reading holding registers: {e}")
            return self._build_exception(transaction_id, unit_id, 0x03, 0x04)

    def _handle_read_input_registers(self, transaction_id: int, unit_id: int, data: bytes) -> bytes:
        if len(data) < 4:
            return self._build_exception(transaction_id, unit_id, 0x04, 0x03)

        try:
            start_addr = struct.unpack('>H', data[0:2])[0]
            quantity = struct.unpack('>H', data[2:4])[0]

            if quantity < 1 or quantity > 125:
                return self._build_exception(transaction_id, unit_id, 0x04, 0x02)

            register_data = self.device.read_input_registers(start_addr, quantity)
            byte_count = len(register_data)

            pdu = bytes([0x04, byte_count]) + register_data
            header = struct.pack('>HHH', transaction_id, 0, len(pdu) + 1)
            return header + bytes([unit_id]) + pdu
        except Exception as e:
            logger.error(f"Error reading input registers: {e}")
            return self._build_exception(transaction_id, unit_id, 0x04, 0x04)

    def _handle_write_single_coil(self, transaction_id: int, unit_id: int, data: bytes) -> bytes:
        if len(data) < 4:
            return self._build_exception(transaction_id, unit_id, 0x05, 0x03)

        try:
            address = struct.unpack('>H', data[0:2])[0]
            value = struct.unpack('>H', data[2:4])[0]

            coil_value = 1 if value == 0xFF00 else 0 if value == 0x0000 else None
            if coil_value is None:
                return self._build_exception(transaction_id, unit_id, 0x05, 0x03)

            self.device.write_single_coil(address, coil_value)

            pdu = bytes([0x05]) + data[0:4]
            header = struct.pack('>HHH', transaction_id, 0, len(pdu) + 1)
            return header + bytes([unit_id]) + pdu
        except Exception as e:
            logger.error(f"Error writing single coil: {e}")
            return self._build_exception(transaction_id, unit_id, 0x05, 0x04)

    def _handle_write_single_register(self, transaction_id: int, unit_id: int, data: bytes) -> bytes:
        if len(data) < 4:
            return self._build_exception(transaction_id, unit_id, 0x06, 0x03)

        try:
            address = struct.unpack('>H', data[0:2])[0]
            value = struct.unpack('>H', data[2:4])[0]

            self.device.write_single_register(address, value)

            pdu = bytes([0x06]) + data[0:4]
            header = struct.pack('>HHH', transaction_id, 0, len(pdu) + 1)
            return header + bytes([unit_id]) + pdu
        except Exception as e:
            logger.error(f"Error writing single register: {e}")
            return self._build_exception(transaction_id, unit_id, 0x06, 0x04)

    def _handle_read_exception_status(self, transaction_id: int, unit_id: int) -> bytes:
        pdu = bytes([0x07, 0x00])
        header = struct.pack('>HHH', transaction_id, 0, len(pdu) + 1)
        return header + bytes([unit_id]) + pdu

    def _handle_diagnostics(self, transaction_id: int, unit_id: int, data: bytes) -> bytes:
        if len(data) < 2:
            return self._build_exception(transaction_id, unit_id, 0x08, 0x03)

        sub_func = struct.unpack('>H', data[0:2])[0]
        pdu = bytes([0x08]) + data[0:2]
        header = struct.pack('>HHH', transaction_id, 0, len(pdu) + 1)
        return header + bytes([unit_id]) + pdu

    def _build_exception(self, transaction_id: int, unit_id: int, func_code: int, exception_code: int) -> bytes:
        pdu = bytes([func_code | 0x80, exception_code])
        header = struct.pack('>HHH', transaction_id, 0, len(pdu) + 1)
        return header + bytes([unit_id]) + pdu