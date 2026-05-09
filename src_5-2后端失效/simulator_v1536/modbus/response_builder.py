from typing import Optional
import struct
import logging

logger = logging.getLogger(__name__)


class ModbusResponseBuilder:
    @staticmethod
    def build_read_response(
        func_code: int,
        slave_id: int,
        transaction_id: int,
        data: bytes
    ) -> bytes:
        header = struct.pack('>HHH', transaction_id, 0, len(data) + 3)
        unit_id = slave_id
        byte_count = len(data)

        response = header + bytes([unit_id, func_code + 0x80, byte_count]) + data
        return response

    @staticmethod
    def build_read_coils_response(
        slave_id: int,
        transaction_id: int,
        data: bytes
    ) -> bytes:
        return ModbusResponseBuilder.build_read_response(0x01, slave_id, transaction_id, data)

    @staticmethod
    def build_read_discrete_inputs_response(
        slave_id: int,
        transaction_id: int,
        data: bytes
    ) -> bytes:
        return ModbusResponseBuilder.build_read_response(0x02, slave_id, transaction_id, data)

    @staticmethod
    def build_read_holding_registers_response(
        slave_id: int,
        transaction_id: int,
        data: bytes
    ) -> bytes:
        return ModbusResponseBuilder.build_read_response(0x03, slave_id, transaction_id, data)

    @staticmethod
    def build_read_input_registers_response(
        slave_id: int,
        transaction_id: int,
        data: bytes
    ) -> bytes:
        return ModbusResponseBuilder.build_read_response(0x04, slave_id, transaction_id, data)

    @staticmethod
    def build_write_single_coil_response(
        slave_id: int,
        transaction_id: int,
        address: int,
        value: int
    ) -> bytes:
        pdu = struct.pack('>BBHH', 0x05, slave_id, address, 0xFF00 if value else 0x0000)
        length = len(pdu)
        header = struct.pack('>HHH', transaction_id, 0, length)
        return header + pdu

    @staticmethod
    def build_write_single_register_response(
        slave_id: int,
        transaction_id: int,
        address: int,
        value: int
    ) -> bytes:
        pdu = struct.pack('>BBHH', 0x06, slave_id, address, value)
        length = len(pdu)
        header = struct.pack('>HHH', transaction_id, 0, length)
        return header + pdu

    @staticmethod
    def build_exception_response(
        func_code: int,
        slave_id: int,
        transaction_id: int,
        exception_code: int
    ) -> bytes:
        pdu = bytes([func_code | 0x80, exception_code])
        header = struct.pack('>HHH', transaction_id, 0, len(pdu) + 1)
        return header + bytes([slave_id]) + pdu

    @staticmethod
    def build_read_exception_status(
        slave_id: int,
        transaction_id: int,
        data: int
    ) -> bytes:
        pdu = bytes([0x07, data])
        header = struct.pack('>HHH', transaction_id, 0, len(pdu))
        return header + bytes([slave_id]) + pdu

    @staticmethod
    def build_diagnostics(
        slave_id: int,
        transaction_id: int,
        sub_func: int,
        data: bytes
    ) -> bytes:
        pdu = struct.pack('>BH', 0x08, sub_func) + data
        header = struct.pack('>HHH', transaction_id, 0, len(pdu) + 1)
        return header + bytes([slave_id]) + pdu