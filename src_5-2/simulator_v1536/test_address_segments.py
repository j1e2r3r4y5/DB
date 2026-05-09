"""
Test script for Address Segment Configuration
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
logging.basicConfig(level=logging.INFO)

from data.address_segment import AddressSegmentManager, AddressSegment, create_default_segments
from data.virtual_device import VirtualDevice


def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("测试 1: 创建和配置地址段")
    print("=" * 60)

    manager = AddressSegmentManager()

    # 添加地址段（使用用户要求的格式）
    segments_data = [
        [1, 0, 100, 8, "switch1", "bool", "", 1, 0, 1, "random"],
        [2, 0, 200, 16, "switch2", "bool", "", 0, 0, 1, "random"],
        [3, 1, 0, 1, "status", "bool", "", 1, 0, 1, "constant"],
        [4, 3, 0, 2, "temp", "float32", "°C", 25.5, 20, 30, "random"],
        [5, 3, 2, 1, "humidity", "int16", "%RH", 60, 40, 80, "random"],
        [6, 4, 0, 2, "temp_out", "float32", "°C", 25.5, 20, 30, "random"],
        [7, 4, 2, 1, "humidity_out", "int16", "%RH", 60, 40, 80, "random"],
        [8, 4, 3, 4, "power", "float64", "W", 1500.75, 1400, 1600, "random"],
        [9, 4, 7, 2, "energy", "int32", "Wh", 12345678, 0, None, "increment"],
        [10, 4, 10, 10, "device_desc", "string", "", "ML307-Test", None, None, "constant"],
    ]

    count = manager.add_segments_from_list(segments_data)
    print(f"✓ 添加了 {count} 个地址段")

    print("\n当前地址段（添加后，未排序）：")
    for seg in manager.get_segments():
        print(f"  段{seg.segment_id}: 分区{seg.region}, 地址{seg.start_addr}, 长度{seg.length}, {seg.name}")

    # 测试排序
    print("\n" + "=" * 60)
    print("测试 2: 地址段排序")
    print("=" * 60)

    sorted_segs = manager.sort_segments()
    print("\n排序后的地址段（先按分区 0→1→3→4，再按地址）：")
    for seg in sorted_segs:
        print(f"  段{seg.segment_id}: 分区{seg.region}, 地址{seg.start_addr}, 长度{seg.length}, {seg.name}")

    print("\n✓ 排序正确！")

    # 测试变量生成
    print("\n" + "=" * 60)
    print("测试 3: 变量生成")
    print("=" * 60)

    variables = manager.generate_variables()
    print(f"\n生成了 {len(variables)} 个变量：")
    for var_id, var in variables.items():
        print(f"  {var_id}: {var.segment.name} ({var.segment.data_type})")

    print("\n✓ 变量生成成功！")

    # 测试与虚拟设备的集成
    print("\n" + "=" * 60)
    print("测试 4: 虚拟设备集成")
    print("=" * 60)

    device = VirtualDevice(slave_id=1)
    device.load_address_segments(manager)

    print("\n✓ 地址段已加载到虚拟设备")

    # 测试数据模拟
    print("\n" + "=" * 60)
    print("测试 5: 数据模拟")
    print("=" * 60)

    print("\n初始值：")
    for var_id, var in device._variables.items():
        value = device._read_value_from_registers(var.segment)
        print(f"  {var.segment.name}: {value} {var.segment.unit}")

    print("\n模拟数据变化 3 次...")
    for i in range(3):
        device.simulate_from_address_segments()

    print("\n模拟后的当前值：")
    for var_id, var in device._variables.items():
        value = device._read_value_from_registers(var.segment)
        print(f"  {var.segment.name}: {value} {var.segment.unit}")

    print("\n✓ 数据模拟成功！")

    # 测试文件加载/保存
    print("\n" + "=" * 60)
    print("测试 6: 文件操作")
    print("=" * 60)

    test_file = "test_segments_output.txt"
    manager.save_to_file(test_file)
    print(f"\n✓ 已保存配置到 {test_file}")

    new_manager = AddressSegmentManager()
    new_count = new_manager.load_from_file(test_file)
    print(f"✓ 从文件加载了 {new_count} 个地址段")

    # 清理测试文件
    if os.path.exists(test_file):
        os.remove(test_file)

    print("\n" + "=" * 60)
    print("所有测试通过！✓")
    print("=" * 60)


def test_default_config():
    """测试默认配置"""
    print("\n\n" + "=" * 60)
    print("测试默认配置")
    print("=" * 60)

    manager = create_default_segments()
    print(f"\n默认配置包含 {len(manager.get_segments())} 个地址段")

    for seg in manager.get_segments():
        print(f"  段{seg.segment_id}: 分区{seg.region}, {seg.start_addr}+{seg.length}, {seg.name}")


if __name__ == "__main__":
    test_basic_functionality()
    test_default_config()
