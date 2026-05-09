"""
Sandbox Virtual Device - Generates mock data for sandbox variables
"""

import logging
import random
import struct
from typing import Dict, List, Optional, Tuple


logger = logging.getLogger(__name__)


class DataConfig:
    """Sandbox data configuration"""
    def __init__(self, slave_id: int, func_code: int, start_addr: int, quantity: int):
        self.slave_id = slave_id
        self.func_code = func_code
        self.start_addr = start_addr
        self.quantity = quantity

    def __repr__(self):
        return f"SandboxDataConfig(slave={self.slave_id}, func={self.func_code}, addr={self.start_addr}, qty={self.quantity})"


class SandboxVirtualDevice:
    """
    Sandbox virtual device - generates mock data without real Modbus hardware
    
    Supports multiple mock strategies:
    - random: random values each read
    - increment: incrementing counters
    - constant: fixed values
    """

    def __init__(self, strategy: str = "random"):
        self._strategy = strategy
        self._configs: List[DataConfig] = []
        self._counters: Dict[str, int] = {}
        self._step = 0

    def update_configs(self, configs: List[DataConfig]):
        """Update sandbox data configurations"""
        self._configs = configs
        logger.info(f"Sandbox device: updated to {len(configs)} configs")
        for cfg in configs:
            logger.debug(f"  Sandbox config: {cfg}")

    def clear_configs(self):
        """Clear all sandbox configurations"""
        self._configs = []
        logger.info("Sandbox device: all configs cleared")

    def get_configs(self) -> List[DataConfig]:
        return list(self._configs)

    def has_configs(self) -> bool:
        return len(self._configs) > 0

    def read_holding_registers(self, start_addr: int, quantity: int) -> bytes:
        """Read mock holding registers (func 0x03)"""
        data = bytearray()
        for i in range(quantity):
            addr = start_addr + i
            val = self._generate_register_value(addr)
            data.extend(struct.pack('>H', val & 0xFFFF))
        return bytes(data)

    def read_input_registers(self, start_addr: int, quantity: int) -> bytes:
        """Read mock input registers (func 0x04)"""
        return self.read_holding_registers(start_addr, quantity)

    def read_coils(self, start_addr: int, quantity: int) -> bytes:
        """Read mock coils (func 0x01)"""
        byte_count = (quantity + 7) // 8
        data = bytearray(byte_count)
        for i in range(quantity):
            addr = start_addr + i
            val = self._generate_coil_value(addr)
            if val:
                byte_idx = i // 8
                bit_idx = i % 8
                data[byte_idx] |= (1 << bit_idx)
        return bytes(data)

    def read_discrete_inputs(self, start_addr: int, quantity: int) -> bytes:
        """Read mock discrete inputs (func 0x02)"""
        return self.read_coils(start_addr, quantity)

    def simulate_changes(self):
        """Advance simulation step to generate varying data"""
        self._step += 1

    def _generate_register_value(self, addr: int) -> int:
        """Generate a mock register value"""
        key = f"reg_{addr}"
        if self._strategy == "constant":
            return 100 + (addr % 1000)
        elif self._strategy == "increment":
            if key not in self._counters:
                self._counters[key] = addr
            self._counters[key] = (self._counters[key] + 1) % 65536
            return self._counters[key]
        else:
            return random.randint(0, 10000)

    def _generate_coil_value(self, addr: int) -> bool:
        """Generate a mock coil value"""
        key = f"coil_{addr}"
        if self._strategy == "constant":
            return addr % 2 == 0
        elif self._strategy == "increment":
            return (self._step + addr) % 3 != 0
        else:
            return random.random() > 0.3
