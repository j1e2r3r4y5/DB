from typing import Dict, List, Optional
import struct
import logging

logger = logging.getLogger(__name__)


class RegisterArea:
    def __init__(self, size: int = 65536):
        self.size = size
        self._data: Dict[int, int] = {}

    def read(self, start_addr: int, quantity: int) -> bytes:
        raise NotImplementedError

    def write(self, start_addr: int, quantity: int, values: bytes) -> bool:
        raise NotImplementedError

    def _validate_address(self, start_addr: int, quantity: int) -> bool:
        if start_addr < 0 or start_addr >= self.size:
            return False
        if start_addr + quantity > self.size:
            return False
        return True


class CoilArea(RegisterArea):
    def read(self, start_addr: int, quantity: int) -> bytes:
        if not self._validate_address(start_addr, quantity):
            raise ValueError(f"Invalid address range: {start_addr}-{start_addr + quantity}")

        result = []
        for i in range(quantity):
            addr = start_addr + i
            value = self._data.get(addr, 0)
            result.append(value & 0x01)

        byte_count = (quantity + 7) // 8
        response = bytearray(byte_count)

        for i, value in enumerate(result):
            byte_index = i // 8
            bit_index = i % 8
            if value:
                response[byte_index] |= (1 << bit_index)

        return bytes(response)

    def write(self, start_addr: int, quantity: int, values: bytes) -> bool:
        if not self._validate_address(start_addr, quantity):
            return False

        for i in range(quantity):
            addr = start_addr + i
            byte_index = i // 8
            bit_index = i % 8
            if byte_index < len(values):
                value = (values[byte_index] >> bit_index) & 0x01
                self._data[addr] = value
        return True


class DiscreteInputArea(RegisterArea):
    def read(self, start_addr: int, quantity: int) -> bytes:
        if not self._validate_address(start_addr, quantity):
            raise ValueError(f"Invalid address range: {start_addr}-{start_addr + quantity}")

        result = []
        for i in range(quantity):
            addr = start_addr + i
            value = self._data.get(addr, 0)
            result.append(value & 0x01)

        byte_count = (quantity + 7) // 8
        response = bytearray(byte_count)

        for i, value in enumerate(result):
            byte_index = i // 8
            bit_index = i % 8
            if value:
                response[byte_index] |= (1 << bit_index)

        return bytes(response)


class HoldingRegisterArea(RegisterArea):
    def read(self, start_addr: int, quantity: int) -> bytes:
        if not self._validate_address(start_addr, quantity):
            raise ValueError(f"Invalid address range: {start_addr}-{start_addr + quantity}")

        result = bytearray()
        for i in range(quantity):
            addr = start_addr + i
            value = self._data.get(addr, 0)
            result.extend(struct.pack('>H', value & 0xFFFF))

        return bytes(result)

    def write(self, start_addr: int, quantity: int, values: bytes) -> bool:
        if not self._validate_address(start_addr, quantity):
            return False

        expected_len = quantity * 2
        if len(values) < expected_len:
            return False

        for i in range(quantity):
            addr = start_addr + i
            value = struct.unpack('>H', values[i*2:i*2+2])[0]
            self._data[addr] = value
        return True


class InputRegisterArea(RegisterArea):
    def read(self, start_addr: int, quantity: int) -> bytes:
        if not self._validate_address(start_addr, quantity):
            raise ValueError(f"Invalid address range: {start_addr}-{start_addr + quantity}")

        result = bytearray()
        for i in range(quantity):
            addr = start_addr + i
            value = self._data.get(addr, 0)
            result.extend(struct.pack('>H', value & 0xFFFF))

        return bytes(result)