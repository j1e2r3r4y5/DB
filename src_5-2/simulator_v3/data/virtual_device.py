from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import random
import threading
import logging

from modbus.areas import CoilArea, DiscreteInputArea, HoldingRegisterArea, InputRegisterArea

logger = logging.getLogger(__name__)


@dataclass
class VirtualDevice:
    slave_id: int
    coils: CoilArea = field(default_factory=CoilArea)
    discrete_inputs: DiscreteInputArea = field(default_factory=DiscreteInputArea)
    holding_registers: HoldingRegisterArea = field(default_factory=HoldingRegisterArea)
    input_registers: InputRegisterArea = field(default_factory=InputRegisterArea)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def __post_init__(self):
        self._initialize_default_data()

    def _initialize_default_data(self):
        from config import config
        self.coils._data[config.SLAVE_1_COIL_SWITCH] = 1
        self.holding_registers._data[config.SLAVE_1_HOLDING_REG_TEMPERATURE] = 250
        self.holding_registers._data[config.SLAVE_1_HOLDING_REG_HUMIDITY] = 600
        self.holding_registers._data[config.SLAVE_1_HOLDING_REG_POWER] = 1500
        self.input_registers._data[config.SLAVE_1_HOLDING_REG_TEMPERATURE] = 250
        self.input_registers._data[config.SLAVE_1_HOLDING_REG_HUMIDITY] = 600
        self.input_registers._data[config.SLAVE_1_HOLDING_REG_POWER] = 1500
        logger.debug(f"Initialized default data for slave_id={self.slave_id}")

    def read_coils(self, start_addr: int, quantity: int) -> bytes:
        with self._lock:
            return self.coils.read(start_addr, quantity)

    def read_discrete_inputs(self, start_addr: int, quantity: int) -> bytes:
        with self._lock:
            return self.discrete_inputs.read(start_addr, quantity)

    def read_holding_registers(self, start_addr: int, quantity: int) -> bytes:
        with self._lock:
            return self.holding_registers.read(start_addr, quantity)

    def read_input_registers(self, start_addr: int, quantity: int) -> bytes:
        with self._lock:
            return self.input_registers.read(start_addr, quantity)

    def write_single_coil(self, addr: int, value: bool) -> bool:
        with self._lock:
            self.coils._data[addr] = 1 if value else 0
            logger.info(f"Slave {self.slave_id}: Coil {addr} set to {value}")
            return True

    def write_single_register(self, addr: int, value: int) -> bool:
        with self._lock:
            self.holding_registers._data[addr] = value & 0xFFFF
            logger.info(f"Slave {self.slave_id}: Holding register {addr} set to {value}")
            return True

    def update_data(self, addr: int, value: Any, data_type: str = "holding"):
        with self._lock:
            if data_type == "coil":
                self.coils._data[addr] = 1 if value else 0
            elif data_type == "discrete":
                self.discrete_inputs._data[addr] = 1 if value else 0
            elif data_type == "input":
                self.input_registers._data[addr] = value & 0xFFFF
            else:
                self.holding_registers._data[addr] = value & 0xFFFF
            logger.debug(f"Slave {self.slave_id}: Updated {data_type} at {addr} to {value}")

    def set_register(self, addr: int, value: int):
        with self._lock:
            self.holding_registers._data[addr] = value & 0xFFFF

    def get_register(self, addr: int) -> int:
        with self._lock:
            return self.holding_registers._data.get(addr, 0)

    def set_coil(self, addr: int, value: bool):
        with self._lock:
            self.coils._data[addr] = 1 if value else 0

    def get_coil(self, addr: int) -> bool:
        with self._lock:
            return bool(self.coils._data.get(addr, 0))

    def simulate_temperature_change(self, base_value: int = 250, variance: int = 10) -> int:
        from config import config
        delta = random.randint(-variance, variance)
        new_value = max(0, min(1000, base_value + delta))
        self.holding_registers._data[config.SLAVE_1_HOLDING_REG_TEMPERATURE] = new_value
        self.input_registers._data[config.SLAVE_1_HOLDING_REG_TEMPERATURE] = new_value
        return new_value

    def simulate_humidity_change(self, base_value: int = 600, variance: int = 20) -> int:
        from config import config
        delta = random.randint(-variance, variance)
        new_value = max(0, min(1000, base_value + delta))
        self.holding_registers._data[config.SLAVE_1_HOLDING_REG_HUMIDITY] = new_value
        self.input_registers._data[config.SLAVE_1_HOLDING_REG_HUMIDITY] = new_value
        return new_value

    def simulate_power_change(self, base_value: int = 1500, variance: int = 500) -> int:
        from config import config
        delta = random.randint(-variance, variance)
        new_value = max(0, min(10000, base_value + delta))
        self.holding_registers._data[config.SLAVE_1_HOLDING_REG_POWER] = new_value
        self.input_registers._data[config.SLAVE_1_HOLDING_REG_POWER] = new_value
        return new_value

    def toggle_switch(self) -> bool:
        from config import config
        with self._lock:
            current = self.coils._data.get(config.SLAVE_1_COIL_SWITCH, 0)
            new_value = 0 if current else 1
            self.coils._data[config.SLAVE_1_COIL_SWITCH] = new_value
            return bool(new_value)