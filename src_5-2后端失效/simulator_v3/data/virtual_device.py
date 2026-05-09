from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import random
import threading
import struct
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
        
        # 变量5: 开关状态 (bool) - 线圈地址 0
        self.coils._data[config.SLAVE_1_COIL_SWITCH] = 1
        
        # 变量1: 温度 (float32) - 地址 0, 2个寄存器
        temp_value = 25.5  # 摄氏度
        temp_bytes = struct.pack('>f', temp_value)  # 大端序float32
        temp_reg0 = (temp_bytes[0] << 8) | temp_bytes[1]
        temp_reg1 = (temp_bytes[2] << 8) | temp_bytes[3]
        self.holding_registers._data[config.SLAVE_1_HOLDING_REG_TEMPERATURE] = temp_reg0
        self.holding_registers._data[config.SLAVE_1_HOLDING_REG_TEMPERATURE + 1] = temp_reg1
        
        # 变量2: 湿度 (int16) - 地址 2, 1个寄存器
        humidity_value = 60  # %RH
        self.holding_registers._data[config.SLAVE_1_HOLDING_REG_HUMIDITY] = humidity_value & 0xFFFF
        
        # 变量3: 功率 (float64) - 地址 3, 4个寄存器
        power_value = 1500.75  # W
        power_bytes = struct.pack('>d', power_value)  # 大端序float64
        power_reg0 = (power_bytes[0] << 8) | power_bytes[1]
        power_reg1 = (power_bytes[2] << 8) | power_bytes[3]
        power_reg2 = (power_bytes[4] << 8) | power_bytes[5]
        power_reg3 = (power_bytes[6] << 8) | power_bytes[7]
        self.holding_registers._data[config.SLAVE_1_HOLDING_REG_POWER] = power_reg0
        self.holding_registers._data[config.SLAVE_1_HOLDING_REG_POWER + 1] = power_reg1
        self.holding_registers._data[config.SLAVE_1_HOLDING_REG_POWER + 2] = power_reg2
        self.holding_registers._data[config.SLAVE_1_HOLDING_REG_POWER + 3] = power_reg3
        
        # 变量4: 累计电能 (int32) - 地址 7, 2个寄存器
        energy_value = 12345678  # Wh
        energy_bytes = struct.pack('>i', energy_value)  # 大端序int32
        energy_reg0 = (energy_bytes[0] << 8) | energy_bytes[1]
        energy_reg1 = (energy_bytes[2] << 8) | energy_bytes[3]
        self.holding_registers._data[config.SLAVE_1_HOLDING_REG_ENERGY] = energy_reg0
        self.holding_registers._data[config.SLAVE_1_HOLDING_REG_ENERGY + 1] = energy_reg1
        
        # 变量6: 设备描述 (string) - 地址 10, 10个寄存器 (20字节)
        device_desc = "ML307-Smart-Meter-001"
        desc_bytes = device_desc.encode('utf-8')[:20]  # 限制20字节
        # 按大端序填入寄存器，每个寄存器2字节
        for i in range(10):
            byte_offset = i * 2
            reg_value = 0
            if byte_offset < len(desc_bytes):
                reg_value = (desc_bytes[byte_offset] << 8)
            if byte_offset + 1 < len(desc_bytes):
                reg_value |= desc_bytes[byte_offset + 1]
            self.holding_registers._data[config.SLAVE_1_HOLDING_REG_DEVICE_DESC + i] = reg_value & 0xFFFF
        
        logger.debug(f"Initialized complete test data for slave_id={self.slave_id}")

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

    def simulate_all_data_changes(self):
        """模拟所有变量数据的动态变化"""
        from config import config
        import struct
        
        with self._lock:
            # 变量1: 温度 (float32) - 小幅度波动
            temp_base = 25.5
            temp_delta = random.uniform(-1.0, 1.0)
            temp_value = temp_base + temp_delta
            temp_bytes = struct.pack('>f', temp_value)
            temp_reg0 = (temp_bytes[0] << 8) | temp_bytes[1]
            temp_reg1 = (temp_bytes[2] << 8) | temp_bytes[3]
            self.holding_registers._data[config.SLAVE_1_HOLDING_REG_TEMPERATURE] = temp_reg0
            self.holding_registers._data[config.SLAVE_1_HOLDING_REG_TEMPERATURE + 1] = temp_reg1
            
            # 变量2: 湿度 (int16) - 小幅度波动
            humidity_base = 60
            humidity_delta = random.randint(-3, 3)
            humidity_value = max(0, min(100, humidity_base + humidity_delta))
            self.holding_registers._data[config.SLAVE_1_HOLDING_REG_HUMIDITY] = humidity_value & 0xFFFF
            
            # 变量3: 功率 (float64) - 小幅度波动
            power_base = 1500.75
            power_delta = random.uniform(-50.0, 50.0)
            power_value = max(0, power_base + power_delta)
            power_bytes = struct.pack('>d', power_value)
            power_reg0 = (power_bytes[0] << 8) | power_bytes[1]
            power_reg1 = (power_bytes[2] << 8) | power_bytes[3]
            power_reg2 = (power_bytes[4] << 8) | power_bytes[5]
            power_reg3 = (power_bytes[6] << 8) | power_bytes[7]
            self.holding_registers._data[config.SLAVE_1_HOLDING_REG_POWER] = power_reg0
            self.holding_registers._data[config.SLAVE_1_HOLDING_REG_POWER + 1] = power_reg1
            self.holding_registers._data[config.SLAVE_1_HOLDING_REG_POWER + 2] = power_reg2
            self.holding_registers._data[config.SLAVE_1_HOLDING_REG_POWER + 3] = power_reg3
            
            # 变量4: 累计电能 (int32) - 持续增长
            energy_addr = config.SLAVE_1_HOLDING_REG_ENERGY
            # 读取当前值
            current_reg0 = self.holding_registers._data.get(energy_addr, 0)
            current_reg1 = self.holding_registers._data.get(energy_addr + 1, 0)
            current_bytes = bytes([
                (current_reg0 >> 8) & 0xFF, current_reg0 & 0xFF,
                (current_reg1 >> 8) & 0xFF, current_reg1 & 0xFF
            ])
            try:
                current_energy = struct.unpack('>i', current_bytes)[0]
            except:
                current_energy = 12345678
            # 增加一点
            new_energy = current_energy + random.randint(1, 10)
            new_bytes = struct.pack('>i', new_energy)
            new_reg0 = (new_bytes[0] << 8) | new_bytes[1]
            new_reg1 = (new_bytes[2] << 8) | new_bytes[3]
            self.holding_registers._data[energy_addr] = new_reg0
            self.holding_registers._data[energy_addr + 1] = new_reg1
            
            # 变量5: 开关状态 (bool) - 偶尔变化
            if random.random() < 0.1:  # 10%的概率变化
                current = self.coils._data.get(config.SLAVE_1_COIL_SWITCH, 0)
                new_value = 0 if current else 1
                self.coils._data[config.SLAVE_1_COIL_SWITCH] = new_value
            
            logger.debug(f"Updated simulated data for slave_id={self.slave_id}")
