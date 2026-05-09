"""
演示地址段配置功能的脚本
"""
import sys
import os
import time
import logging
from datetime import datetime

# 设置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

print("=" * 70)
print("DTU + MODBUS SIMULATOR - ADDRESS SEGMENT CONFIGURATION DEMO")
print("=" * 70)
print()

# 1. 显示输入配置文件
print("=" * 70)
print("1. INPUT CONFIGURATION FILE: address_segments.txt")
print("=" * 70)
with open('address_segments.txt', 'r', encoding='utf-8') as f:
    for line in f:
        print(f"   {line.rstrip()}")
print()

# 2. 导入并运行模拟器核心
print("=" * 70)
print("2. SIMULATOR INITIALIZATION & RUNNING OUTPUT")
print("=" * 70)

# 导入必要的模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from data.address_segment import AddressSegmentManager, create_default_segments
from data.virtual_device import VirtualDevice
from core.config_manager import ConfigManager, DataConfig

# 步骤1: 加载地址段配置
print("\n[Step 1] Loading address segments from file...")
manager = AddressSegmentManager()
count = manager.load_from_file('address_segments.txt')
print(f"   ✓ Loaded {count} address segments")

# 步骤2: 排序
print("\n[Step 2] Sorting address segments (0→1→3→4 order)...")
manager.sort_segments()
print("   ✓ Segments sorted:")
for seg in manager.get_segments():
    print(f"      Segment {seg.segment_id}: region={seg.region}, addr={seg.start_addr}, len={seg.length}, name={seg.name}")

# 步骤3: 生成变量
print("\n[Step 3] Generating variables from segments...")
variables = manager.generate_variables()
print(f"   ✓ Generated {len(variables)} variables")

# 步骤4: 加载到虚拟设备
print("\n[Step 4] Loading configuration to virtual device...")
device = VirtualDevice(slave_id=1)
device.load_address_segments(manager)
print("   ✓ Variables initialized in device registers")

# 步骤5: 生成数据采集配置
print("\n[Step 5] Generating data collection configs...")
data_configs = []
for seg in manager.get_segments():
    func_code = AddressSegmentManager.REGION_TO_FUNC_CODE.get(seg.region, 0x03)
    config = DataConfig(
        slave_id=1,
        func_code=func_code,
        start_addr=seg.start_addr,
        quantity=seg.length
    )
    data_configs.append(config)
print(f"   ✓ Generated {len(data_configs)} data collection configs")
for i, cfg in enumerate(data_configs):
    print(f"      Config {i}: slave={cfg.slave_id}, func={cfg.func_code}, addr={cfg.start_addr}, qty={cfg.quantity}")

# 步骤6: 模拟数据变化3次
print("\n[Step 6] Simulating data changes (3 cycles)...")
for i in range(3):
    print(f"\n   Cycle {i+1}:")
    device.simulate_from_address_segments()
    
    # 读取当前变量值
    for var_id, var in device._variables.items():
        value = device._read_value_from_registers(var.segment)
        print(f"      {var.segment.name}: {value} {var.segment.unit}")

print("\n" + "=" * 70)
print("3. UPLINK DATA PAYLOAD EXAMPLE (0x05 Data Upload)")
print("=" * 70)

# 构建数据上传帧（模拟）
def build_upload_frame(device, manager):
    """模拟构建数据上发帧"""
    from data.address_segment import AddressSegmentManager
    
    frame = bytearray([0x05])  # 功能码 0x05
    segments = manager.get_segments()
    frame.extend(len(segments).to_bytes(2, 'big'))
    
    for seg in segments:
        # 从站ID
        frame.append(1)
        # 分区类型
        func_code = AddressSegmentManager.REGION_TO_FUNC_CODE.get(seg.region, 0x03)
        type_map = {0x01: 0x00, 0x02: 0x01, 0x04: 0x03, 0x03: 0x04}
        region_type = type_map.get(func_code, func_code)
        frame.append(region_type)
        # 起始地址
        frame.extend(seg.start_addr.to_bytes(2, 'big'))
        # 数量
        frame.extend(seg.length.to_bytes(2, 'big'))
        
        # 读取数据
        if seg.region == 0:
            data = device.read_coils(seg.start_addr, seg.length)
        elif seg.region == 1:
            data = device.read_discrete_inputs(seg.start_addr, seg.length)
        elif seg.region == 3:
            data = device.read_input_registers(seg.start_addr, seg.length)
        elif seg.region == 4:
            data = device.read_holding_registers(seg.start_addr, seg.length)
        else:
            data = b''
        
        # 数据长度
        if seg.region in (0, 1):
            # 线圈/离散输入：每个字节8个点
            byte_len = (seg.length + 7) // 8
            frame.append(byte_len)
        else:
            # 寄存器：每个寄存器2字节
            frame.append(seg.length * 2)
        
        frame.extend(data)
    
    return bytes(frame)

upload_frame = build_upload_frame(device, manager)
print(f"   {upload_frame.hex()}")
print(f"   (Length: {len(upload_frame)} bytes)")
print()

print("=" * 70)
print("4. SUMMARY")
print("=" * 70)
print("   ✓ Input:  address_segments.txt with 10 address segments")
print("   ✓ Output: ")
print("      - 10 variables initialized in device registers")
print("      - 10 data collection configs created")
print("      - Modbus TCP server on 127.0.0.1:502 (if running)")
print("      - MQTT client connected to 127.0.0.1:1883 (if running)")
print("      - Heartbeat packets (0x00) sent every 30s")
print("      - Data upload packets (0x05) sent periodically")
print("=" * 70)
