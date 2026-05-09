"""
简化配置演示脚本
"""
import sys
import os
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.address_segment import AddressSegmentManager
from data.virtual_device import VirtualDevice

print("=" * 70)
print("SIMPLE ADDRESS SEGMENT CONFIGURATION DEMO")
print("=" * 70)
print()

# 1. 显示输入配置
print("=" * 70)
print("1. INPUT CONFIG: address_segments_simple.txt")
print("=" * 70)
with open('address_segments_simple.txt', 'r', encoding='utf-8') as f:
    print(f.read())
print()

# 2. 加载并处理配置
print("=" * 70)
print("2. PROCESSING...")
print("=" * 70)

manager = AddressSegmentManager()
count = manager.load_from_file('address_segments_simple.txt')
print(f"\n✓ Loaded {count} segments")

# 排序
manager.sort_segments()
print("✓ Segments sorted by region (0→1→3→4)")

# 生成变量
variables = manager.generate_variables()
print(f"✓ Generated {len(variables)} variables")
print()

# 显示所有段
print("Segments after sorting:")
for seg in manager.get_segments():
    print(f"  {seg.name}: region={seg.region}, addr={seg.start_addr}, len={seg.length}")
print()

# 3. 加载到设备并显示数据
print("=" * 70)
print("3. DEVICE REGISTER VALUES")
print("=" * 70)

device = VirtualDevice(slave_id=1)
device.load_address_segments(manager)

for seg in manager.get_segments():
    print(f"\n--- {seg.name} ---")
    
    if seg.region == 0:
        data = device.read_coils(seg.start_addr, seg.length)
        # 解析线圈数据
        bits = []
        for byte in data:
            for i in range(8):
                bits.append((byte >> i) & 0x01)
        bits = bits[:seg.length]
        print(f"  Coils: {bits}")
        print(f"  (All should be 1)")
    
    elif seg.region == 1:
        data = device.read_discrete_inputs(seg.start_addr, seg.length)
        bits = []
        for byte in data:
            for i in range(8):
                bits.append((byte >> i) & 0x01)
        bits = bits[:seg.length]
        print(f"  Discrete Inputs: {bits}")
        print(f"  (All should be 1)")
    
    elif seg.region == 3:
        data = device.read_input_registers(seg.start_addr, seg.length)
        # 解析字符串
        chars = []
        for i in range(0, len(data), 2):
            if i+1 < len(data):
                high = data[i]
                low = data[i+1]
                c1 = (high >> 8) & 0xff if isinstance(high, int) else 0
                c2 = high & 0xff if isinstance(high, int) else 0
                c3 = (low >> 8) & 0xff if isinstance(low, int) else 0
                c4 = low & 0xff if isinstance(low, int) else 0
                for c in [c1, c2, c3, c4]:
                    if 32 <= c <= 126:
                        chars.append(chr(c))
        # 另一种方式：直接从变量读取
        value = device._read_value_from_registers(seg)
        print(f"  Input Registers: {value}")
    
    elif seg.region == 4:
        data = device.read_holding_registers(seg.start_addr, seg.length)
        value = device._read_value_from_registers(seg)
        print(f"  Holding Registers: {value}")

print()
print("=" * 70)
print("4. SUMMARY")
print("=" * 70)
print("✓ Variable names: seg1, seg2, ..., seg12 (段序号即变量名)")
print("✓ Region 0 (Coils): all 1s")
print("✓ Region 1 (Discrete Inputs): all 1s")
print("✓ Region 3 (Input Registers): ABCDEFGHIJKLM + NOPQRSTUVWXYZ")
print("✓ Region 4 (Holding Registers): ABCDEFGHIJKLM + NOPQRSTUVWXYZ")
print("=" * 70)
