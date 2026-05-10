"""
Address Segment Configuration Manager
支持地址段配置、排序和自动变量生成
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import logging
import random
import struct

logger = logging.getLogger(__name__)


@dataclass
class AddressSegment:
    """地址段数据结构"""
    segment_id: int  # 段序号
    region: int  # 所属分区 (0/1/3/4)
    start_addr: int  # 起始地址
    length: int  # 地址长度
    name: str = ""  # 变量名称
    data_type: str = "uint16"  # 数据类型
    unit: str = ""  # 单位
    init_value: Any = None  # 初始值
    min_value: Any = None  # 最小值（用于模拟）
    max_value: Any = None  # 最大值（用于模拟）
    simulation_type: str = "random"  # 模拟类型: random/increment/constant

    def __post_init__(self):
        if not self.name:
            self.name = f"seg_{self.segment_id}_reg{self.region}_{self.start_addr}"


@dataclass
class GeneratedVariable:
    """自动生成的变量"""
    var_id: str
    segment: AddressSegment
    slave_id: int = 1
    current_value: Any = None
    _lock: Any = field(default_factory=lambda: __import__('threading').Lock(), repr=False)

    def __post_init__(self):
        if self.segment.init_value is not None:
            self.current_value = self.segment.init_value


class AddressSegmentManager:
    """地址段管理器"""

    # 分区优先级排序（0→1→3→4）
    REGION_PRIORITY = {0: 0, 1: 1, 3: 2, 4: 3}

    # 分区到功能码的映射
    REGION_TO_FUNC_CODE = {
        0: 0x01,  # 线圈
        1: 0x02,  # 离散输入
        3: 0x04,  # 输入寄存器
        4: 0x03,  # 保持寄存器
    }

    def __init__(self):
        self._segments: List[AddressSegment] = []
        self._variables: Dict[str, GeneratedVariable] = {}
        self._lock = __import__('threading').Lock()

    def add_segment(self, segment: AddressSegment) -> bool:
        """添加地址段"""
        with self._lock:
            # 检查段序号是否已存在
            if any(s.segment_id == segment.segment_id for s in self._segments):
                logger.warning(f"Segment ID {segment.segment_id} already exists")
                return False
            self._segments.append(segment)
            logger.info(f"Added segment: {segment}")
            return True

    def add_segments_from_list(self, segment_list: List[List]) -> int:
        """
        从列表批量添加地址段
        格式: [[段序号, 所属分区, 起始地址, 地址长度, ...], ...]
        """
        count = 0
        for item in segment_list:
            if len(item) >= 4:
                # 默认名称：seg + 段序号
                default_name = f"seg{int(item[0])}"
                
                segment = AddressSegment(
                    segment_id=int(item[0]),
                    region=int(item[1]),
                    start_addr=int(item[2]),
                    length=int(item[3]),
                    name=default_name,  # 默认名称
                    simulation_type="constant"  # 默认常量，不变化
                )
                
                # 可选字段映射
                # item[4]=name, item[5]=data_type, item[6]=unit, item[7]=init_value,
                # item[8]=min_value, item[9]=max_value, item[10]=simulation_type
                if len(item) > 4 and str(item[4]).strip() not in ['', '-', 'None']:
                    segment.name = str(item[4])
                if len(item) > 5 and str(item[5]).strip() not in ['', '-', 'None']:
                    segment.data_type = str(item[5])
                if len(item) > 6 and str(item[6]).strip() not in ['', '-', 'None']:
                    segment.unit = str(item[6])
                if len(item) > 7 and str(item[7]).strip() not in ['', '-', 'None']:
                    val_str = str(item[7])
                    if segment.data_type == 'bool':
                        segment.init_value = val_str.lower() in ['1', 'true', 'yes', 'on']
                    elif segment.data_type in ['float32', 'float64']:
                        try:
                            segment.init_value = float(val_str)
                        except:
                            segment.init_value = val_str
                    elif segment.data_type in ['int16', 'uint16', 'int32', 'uint32']:
                        try:
                            segment.init_value = int(val_str)
                        except:
                            segment.init_value = val_str
                    else:
                        segment.init_value = val_str
                if len(item) > 8 and str(item[8]).strip() not in ['', '-', 'None']:
                    try:
                        segment.min_value = float(item[8])
                    except:
                        segment.min_value = item[8]
                if len(item) > 9 and str(item[9]).strip() not in ['', '-', 'None']:
                    try:
                        segment.max_value = float(item[9])
                    except:
                        segment.max_value = item[9]
                if len(item) > 10 and str(item[10]).strip() not in ['', '-', 'None']:
                    segment.simulation_type = str(item[10])
                
                if self.add_segment(segment):
                    count += 1
        return count

    def sort_segments(self) -> List[AddressSegment]:
        """
        按规则排序地址段：
        1. 先按分区值排序（0→1→3→4）
        2. 每区内再按起始地址升序
        """
        with self._lock:
            sorted_segments = sorted(
                self._segments,
                key=lambda s: (
                    self.REGION_PRIORITY.get(s.region, 999),
                    s.start_addr
                )
            )
            # 重新分配段序号
            for i, seg in enumerate(sorted_segments, 1):
                seg.segment_id = i
            self._segments = sorted_segments
            logger.info(f"Sorted {len(sorted_segments)} segments")
            return sorted_segments.copy()

    def generate_variables(self, slave_id: int = 1) -> Dict[str, GeneratedVariable]:
        """根据地址段自动生成变量"""
        with self._lock:
            self._variables.clear()
            for segment in self._segments:
                var_id = f"var_{segment.segment_id}"
                variable = GeneratedVariable(
                    var_id=var_id,
                    segment=segment,
                    slave_id=slave_id
                )
                self._variables[var_id] = variable
                logger.info(f"Generated variable: {var_id} for segment {segment.segment_id}")
            return self._variables.copy()

    def get_segments(self) -> List[AddressSegment]:
        """获取所有地址段"""
        with self._lock:
            return self._segments.copy()

    def get_variables(self) -> Dict[str, GeneratedVariable]:
        """获取所有生成的变量"""
        with self._lock:
            return self._variables.copy()

    def get_segment_by_id(self, segment_id: int) -> Optional[AddressSegment]:
        """根据段ID获取地址段"""
        with self._lock:
            return next((s for s in self._segments if s.segment_id == segment_id), None)

    def get_variable_by_id(self, var_id: str) -> Optional[GeneratedVariable]:
        """根据变量ID获取变量"""
        with self._lock:
            return self._variables.get(var_id)

    def clear(self):
        """清空所有配置"""
        with self._lock:
            self._segments.clear()
            self._variables.clear()
            logger.info("Cleared all address segments and variables")

    def load_from_file(self, filepath: str) -> int:
        """从文件加载地址段配置（支持简单文本格式）"""
        import os
        if not os.path.exists(filepath):
            logger.error(f"Config file not found: {filepath}")
            return 0

        segments = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split()
                    if len(parts) >= 4:
                        segments.append(parts)
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            return 0

        return self.add_segments_from_list(segments)

    def save_to_file(self, filepath: str):
        """保存地址段配置到文件"""
        with self._lock:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write("# Address Segment Configuration\n")
                    f.write("# Format: segment_id region start_addr length [name] [data_type] [unit] [init_value]\n")
                    f.write("# Regions: 0=Coil, 1=Discrete Input, 3=Input Register, 4=Holding Register\n\n")
                    for seg in self._segments:
                        line = f"{seg.segment_id} {seg.region} {seg.start_addr} {seg.length}"
                        if seg.name:
                            line += f" {seg.name}"
                        if seg.data_type != "uint16":
                            line += f" {seg.data_type}"
                        if seg.unit:
                            line += f" {seg.unit}"
                        if seg.init_value is not None:
                            line += f" {seg.init_value}"
                        f.write(line + "\n")
                logger.info(f"Saved {len(self._segments)} segments to {filepath}")
            except Exception as e:
                logger.error(f"Error saving config file: {e}")


def create_default_segments() -> AddressSegmentManager:
    """创建默认的地址段配置（示例）"""
    manager = AddressSegmentManager()

    # 示例地址段列表
    default_segments = [
        # [段序号, 分区, 起始地址, 长度, 名称, 数据类型, 单位, 初始值, 最小值, 最大值, 模拟类型]
        [1, 0, 100, 8, "switch_group_1", "bool", "", 1, 0, 1, "random"],
        [2, 0, 200, 16, "switch_group_2", "bool", "", 0, 0, 1, "random"],
        [3, 1, 0, 1, "status_input", "bool", "", 1, 0, 1, "constant"],
        [4, 3, 0, 2, "temperature", "float32", "°C", 25.5, 20.0, 30.0, "random"],
        [5, 3, 2, 1, "humidity", "int16", "%RH", 60, 40, 80, "random"],
        [6, 4, 0, 2, "temperature_out", "float32", "°C", 25.5, 20.0, 30.0, "random"],
        [7, 4, 2, 1, "humidity_out", "int16", "%RH", 60, 40, 80, "random"],
        [8, 4, 3, 4, "power", "float64", "W", 1500.75, 1400.0, 1600.0, "random"],
        [9, 4, 7, 2, "energy", "int32", "Wh", 12345678, 0, None, "increment"],
        [10, 4, 10, 10, "device_desc", "string", "", "ML307-Smart-Meter-001", None, None, "constant"],
    ]

    manager.add_segments_from_list(default_segments)
    manager.sort_segments()
    manager.generate_variables()

    return manager
