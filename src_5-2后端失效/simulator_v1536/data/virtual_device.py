from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import random
import threading
import struct
import logging

from modbus.areas import CoilArea, DiscreteInputArea, HoldingRegisterArea, InputRegisterArea
from .address_segment import AddressSegmentManager, AddressSegment, GeneratedVariable

logger = logging.getLogger(__name__)


@dataclass
class VirtualDevice:
    slave_id: int
    coils: CoilArea = field(default_factory=CoilArea)
    discrete_inputs: DiscreteInputArea = field(default_factory=DiscreteInputArea)
    holding_registers: HoldingRegisterArea = field(default_factory=HoldingRegisterArea)
    input_registers: InputRegisterArea = field(default_factory=InputRegisterArea)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _address_manager: Optional[AddressSegmentManager] = None
    _variables: Dict[str, GeneratedVariable] = field(default_factory=dict)

    def __post_init__(self):
        self._initialize_default_data()

    def _initialize_default_data(self):
        # 完全禁用旧的默认数据初始化！
        logger.debug(f"Skipping old default data initialization")

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
        # 如果有地址段配置，使用地址段的方式
        self.simulate_from_address_segments()
        
        logger.debug(f"Updated simulated data for slave_id={self.slave_id}")

    def load_address_segments(self, manager: AddressSegmentManager):
        """从地址段管理器加载配置并初始化寄存器"""
        with self._lock:
            self._address_manager = manager
            self._variables = manager.get_variables()
            
            # 强制清空所有寄存器，确保没有旧数据残留！
            logger.info(f"Clearing ALL registers before loading address segments")
            self.coils._data.clear()
            self.discrete_inputs._data.clear()
            self.holding_registers._data.clear()
            self.input_registers._data.clear()

            # 现在初始化新变量
            for var_id, variable in self._variables.items():
                self._initialize_variable_to_registers(variable)

            logger.info(f"Loaded {len(self._variables)} variables from address segments")

    def _initialize_variable_to_registers(self, variable: GeneratedVariable):
        """将变量初始值写入对应的寄存器/线圈"""
        segment = variable.segment
        value = segment.init_value

        if value is None:
            return

        if segment.region == 0:
            # 线圈区域
            self._write_coils(segment.start_addr, segment.length, value)
        elif segment.region == 1:
            # 离散输入区域
            self._write_discrete_inputs(segment.start_addr, segment.length, value)
        elif segment.region == 3:
            # 输入寄存器
            self._write_input_registers(segment.start_addr, segment.length, value, segment.data_type)
        elif segment.region == 4:
            # 保持寄存器
            self._write_holding_registers(segment.start_addr, segment.length, value, segment.data_type)

    def _write_coils(self, start_addr: int, length: int, value):
        """写入线圈值"""
        if isinstance(value, (list, tuple)):
            for i, v in enumerate(value[:length]):
                self.coils._data[start_addr + i] = 1 if v else 0
        elif isinstance(value, bool):
            for i in range(length):
                self.coils._data[start_addr + i] = 1 if value else 0
        elif isinstance(value, int):
            # 按位写入
            for i in range(length):
                bit_val = (value >> i) & 0x01
                self.coils._data[start_addr + i] = bit_val

    def _write_discrete_inputs(self, start_addr: int, length: int, value):
        """写入离散输入值"""
        if isinstance(value, (list, tuple)):
            for i, v in enumerate(value[:length]):
                self.discrete_inputs._data[start_addr + i] = 1 if v else 0
        elif isinstance(value, bool):
            for i in range(length):
                self.discrete_inputs._data[start_addr + i] = 1 if value else 0
        elif isinstance(value, int):
            for i in range(length):
                bit_val = (value >> i) & 0x01
                self.discrete_inputs._data[start_addr + i] = bit_val

    def _write_holding_registers(self, start_addr: int, length: int, value, data_type: str):
        """写入保持寄存器"""
        self._write_registers_to_area(self.holding_registers, start_addr, length, value, data_type)

    def _write_input_registers(self, start_addr: int, length: int, value, data_type: str):
        """写入输入寄存器"""
        self._write_registers_to_area(self.input_registers, start_addr, length, value, data_type)

    def _write_registers_to_area(self, area, start_addr: int, length: int, value, data_type: str):
        """通用寄存器写入方法"""
        try:
            if data_type == "string":
                # 字符串处理 - 必须先清零所有寄存器！
                for i in range(length):
                    area._data[start_addr + i] = 0
                
                if isinstance(value, str):
                    bytes_data = value.encode('utf-8')
                    for i in range(length):
                        byte_offset = i * 2
                        reg_val = 0
                        if byte_offset < len(bytes_data):
                            reg_val = (bytes_data[byte_offset] << 8) & 0xFF00
                        if byte_offset + 1 < len(bytes_data):
                            reg_val |= bytes_data[byte_offset + 1] & 0x00FF
                        area._data[start_addr + i] = reg_val & 0xFFFF
            elif data_type == "float32":
                # float32 (大端序)
                bytes_data = struct.pack('>f', float(value))
                reg0 = (bytes_data[0] << 8) | bytes_data[1]
                reg1 = (bytes_data[2] << 8) | bytes_data[3]
                if length >= 1:
                    area._data[start_addr] = reg0 & 0xFFFF
                if length >= 2:
                    area._data[start_addr + 1] = reg1 & 0xFFFF
            elif data_type == "float64":
                # float64 (大端序)
                bytes_data = struct.pack('>d', float(value))
                for i in range(min(4, length)):
                    byte_offset = i * 2
                    reg_val = (bytes_data[byte_offset] << 8) | bytes_data[byte_offset + 1]
                    area._data[start_addr + i] = reg_val & 0xFFFF
            elif data_type in ["int32", "uint32"]:
                # int32/uint32 (大端序)
                bytes_data = struct.pack('>i', int(value))
                reg0 = (bytes_data[0] << 8) | bytes_data[1]
                reg1 = (bytes_data[2] << 8) | bytes_data[3]
                if length >= 1:
                    area._data[start_addr] = reg0 & 0xFFFF
                if length >= 2:
                    area._data[start_addr + 1] = reg1 & 0xFFFF
            elif data_type in ["int16", "uint16"]:
                # int16/uint16
                area._data[start_addr] = int(value) & 0xFFFF
            elif data_type == "bool":
                # 布尔值
                area._data[start_addr] = 1 if value else 0
            else:
                # 默认作为 uint16 处理
                area._data[start_addr] = int(value) & 0xFFFF
        except Exception as e:
            logger.warning(f"Failed to write registers: {e}")

    def simulate_from_address_segments(self):
        """根据地址段配置模拟数据变化"""
        if not self._address_manager:
            return

        with self._lock:
            for var_id, variable in self._variables.items():
                segment = variable.segment
                self._simulate_single_variable(variable)

    def _simulate_single_variable(self, variable: GeneratedVariable):
        """模拟单个变量的变化"""
        segment = variable.segment
        sim_type = segment.simulation_type

        if sim_type == "constant":
            # 即使是 constant 类型，也要强制重写初始值到寄存器，确保没有旧数据残留！
            self._write_value_to_registers(segment, segment.init_value)
            return

        # 获取当前值
        current_value = self._read_value_from_registers(segment)

        # 计算新值
        new_value = current_value
        if sim_type == "random":
            new_value = self._calculate_random_value(segment, current_value)
        elif sim_type == "increment":
            new_value = self._calculate_increment_value(segment, current_value)

        # 更新变量
        variable.current_value = new_value

        # 写入寄存器
        self._write_value_to_registers(segment, new_value)

    def _read_value_from_registers(self, segment: AddressSegment) -> Any:
        """从寄存器读取当前值"""
        if segment.region == 0:
            return self._read_coils_value(segment.start_addr, segment.length, segment.data_type)
        elif segment.region == 1:
            return self._read_discrete_inputs_value(segment.start_addr, segment.length, segment.data_type)
        elif segment.region == 3:
            return self._read_registers_value(self.input_registers, segment.start_addr, segment.length, segment.data_type)
        elif segment.region == 4:
            return self._read_registers_value(self.holding_registers, segment.start_addr, segment.length, segment.data_type)
        return None

    def _write_value_to_registers(self, segment: AddressSegment, value: Any):
        """写入值到寄存器"""
        if segment.region == 0:
            self._write_coils(segment.start_addr, segment.length, value)
        elif segment.region == 1:
            self._write_discrete_inputs(segment.start_addr, segment.length, value)
        elif segment.region == 3:
            self._write_input_registers(segment.start_addr, segment.length, value, segment.data_type)
        elif segment.region == 4:
            self._write_holding_registers(segment.start_addr, segment.length, value, segment.data_type)

    def _read_coils_value(self, start_addr: int, length: int, data_type: str) -> Any:
        """读取线圈值"""
        if data_type == "bool":
            return bool(self.coils._data.get(start_addr, 0))
        elif length == 1:
            return self.coils._data.get(start_addr, 0)
        else:
            # 读取多个位
            value = 0
            for i in range(length):
                bit_val = self.coils._data.get(start_addr + i, 0)
                value |= (bit_val & 0x01) << i
            return value

    def _read_discrete_inputs_value(self, start_addr: int, length: int, data_type: str) -> Any:
        """读取离散输入值"""
        if data_type == "bool":
            return bool(self.discrete_inputs._data.get(start_addr, 0))
        elif length == 1:
            return self.discrete_inputs._data.get(start_addr, 0)
        else:
            value = 0
            for i in range(length):
                bit_val = self.discrete_inputs._data.get(start_addr + i, 0)
                value |= (bit_val & 0x01) << i
            return value

    def _read_registers_value(self, area, start_addr: int, length: int, data_type: str) -> Any:
        """读取寄存器值"""
        try:
            if data_type == "float32":
                reg0 = area._data.get(start_addr, 0)
                reg1 = area._data.get(start_addr + 1, 0)
                bytes_data = bytes([
                    (reg0 >> 8) & 0xFF, reg0 & 0xFF,
                    (reg1 >> 8) & 0xFF, reg1 & 0xFF
                ])
                return struct.unpack('>f', bytes_data)[0]
            elif data_type == "float64":
                bytes_list = []
                for i in range(min(4, length)):
                    reg = area._data.get(start_addr + i, 0)
                    bytes_list.append((reg >> 8) & 0xFF)
                    bytes_list.append(reg & 0xFF)
                while len(bytes_list) < 8:
                    bytes_list.append(0)
                return struct.unpack('>d', bytes(bytes_list))[0]
            elif data_type in ["int32", "uint32"]:
                reg0 = area._data.get(start_addr, 0)
                reg1 = area._data.get(start_addr + 1, 0)
                bytes_data = bytes([
                    (reg0 >> 8) & 0xFF, reg0 & 0xFF,
                    (reg1 >> 8) & 0xFF, reg1 & 0xFF
                ])
                return struct.unpack('>i', bytes_data)[0]
            elif data_type in ["int16", "uint16"]:
                return area._data.get(start_addr, 0)
            elif data_type == "bool":
                return bool(area._data.get(start_addr, 0))
            elif data_type == "string":
                bytes_list = []
                for i in range(length):
                    reg = area._data.get(start_addr + i, 0)
                    bytes_list.append((reg >> 8) & 0xFF)
                    bytes_list.append(reg & 0xFF)
                # 去除末尾的零字节
                result = bytes(bytes_list).rstrip(b'\x00').decode('utf-8', errors='ignore')
                return result
            else:
                return area._data.get(start_addr, 0)
        except Exception as e:
            logger.warning(f"Failed to read registers: {e}")
            return None

    def _calculate_random_value(self, segment: AddressSegment, current_value: Any) -> Any:
        """计算随机变化的值"""
        data_type = segment.data_type
        min_val = segment.min_value
        max_val = segment.max_value

        if data_type in ["float32", "float64"]:
            base = current_value if current_value is not None else segment.init_value
            if base is None:
                base = 0.0
            delta = random.uniform(-0.5, 0.5)
            new_val = base + delta
            if min_val is not None:
                new_val = max(new_val, min_val)
            if max_val is not None:
                new_val = min(new_val, max_val)
            return new_val
        elif data_type in ["int16", "uint16", "int32", "uint32"]:
            base = current_value if current_value is not None else segment.init_value
            if base is None:
                base = 0
            delta = random.randint(-1, 1)
            new_val = base + delta
            if min_val is not None:
                new_val = max(new_val, min_val)
            if max_val is not None:
                new_val = min(new_val, max_val)
            return new_val
        elif data_type == "bool":
            return random.choice([True, False]) if random.random() < 0.1 else current_value
        else:
            return current_value

    def _calculate_increment_value(self, segment: AddressSegment, current_value: Any) -> Any:
        """计算递增的值"""
        base = current_value if current_value is not None else segment.init_value
        if base is None:
            base = 0
        if segment.data_type in ["float32", "float64"]:
            increment = random.uniform(0.1, 1.0)
        else:
            increment = random.randint(1, 10)
        new_val = base + increment
        if segment.max_value is not None:
            if new_val > segment.max_value:
                new_val = segment.min_value if segment.min_value is not None else 0
        return new_val

    def get_address_manager(self) -> Optional[AddressSegmentManager]:
        """获取地址段管理器"""
        return self._address_manager

    def get_data_configs_from_segments(self) -> List[Dict]:
        """从地址段生成数据采集配置（用于上报）"""
        configs = []
        if self._address_manager:
            for segment in self._address_manager.get_segments():
                func_code = AddressSegmentManager.REGION_TO_FUNC_CODE.get(segment.region, 0x03)
                configs.append({
                    'slave_id': self.slave_id,
                    'func_code': func_code,
                    'start_addr': segment.start_addr,
                    'quantity': segment.length,
                    'name': segment.name
                })
        return configs
