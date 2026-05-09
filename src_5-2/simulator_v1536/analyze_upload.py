#!/usr/bin/env python3
"""
分析模拟器的实际数据上传配置
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.address_segment import AddressSegmentManager

def main():
    print("=" * 80)
    print("模拟器实际数据上传配置分析")
    print("=" * 80)
    
    # 1. 加载地址段配置
    manager = AddressSegmentManager()
    config_file = os.path.join(os.path.dirname(__file__), "address_segments_final.txt")
    count = manager.load_from_file(config_file)
    print(f"\n1. 加载了 {count} 个地址段配置")
    
    # 2. 显示原始地址段
    print("\n" + "=" * 80)
    print("2. 原始地址段配置")
    print("=" * 80)
    
    segments = manager.get_segments()
    for seg in segments:
        print(f"  段{seg.segment_id}: 区域={seg.region}, 地址={seg.start_addr}, "
              f"长度={seg.length}, 名称={seg.name}, 类型={seg.data_type}, "
              f"初始值={seg.init_value}")
    
    # 3. 模拟合并过程
    print("\n" + "=" * 80)
    print("3. 合并数据配置（按区域）")
    print("=" * 80)
    
    segments_by_region = {}
    for segment in segments:
        if segment.region not in segments_by_region:
            segments_by_region[segment.region] = []
        segments_by_region[segment.region].append(segment)
    
    merged_configs = []
    region_names = {0: "线圈(0区)", 1: "离散输入(1区)", 3: "输入寄存器(3区)", 4: "保持寄存器(4区)"}
    func_code_map = {0: 0x01, 1: 0x02, 3: 0x04, 4: 0x03}
    
    for region, segs in segments_by_region.items():
        print(f"\n  区域 {region} ({region_names.get(region, '未知')}):")
        
        # 计算地址范围
        addrs = []
        for seg in segs:
            addrs.append(seg.start_addr)
            addrs.append(seg.start_addr + seg.length - 1)
        
        start_addr = min(addrs)
        end_addr = max(addrs)
        length = end_addr - start_addr + 1
        
        print(f"    包含段: {[s.segment_id for s in segs]}")
        print(f"    地址范围: {start_addr} - {end_addr}")
        print(f"    总长度: {length} {'位' if region in [0, 1] else '寄存器'}")
        print(f"    功能码: 0x{func_code_map.get(region, '03'):02X}")
        
        merged_configs.append({
            'region': region,
            'name': region_names.get(region, '未知'),
            'func_code': func_code_map.get(region, 0x03),
            'start_addr': start_addr,
            'quantity': length
        })
    
    # 4. 显示最终上传配置
    print("\n" + "=" * 80)
    print("4. 最终数据上传配置（0x05 数据包）")
    print("=" * 80)
    print(f"\n  上传组数: {len(merged_configs)} 组")
    print(f"  上传间隔: 默认 30 秒")
    print(f"  MQTT 主题: /dtu/A1B2C3D4/up")
    
    total_bytes = 0
    for i, cfg in enumerate(merged_configs, 1):
        data_len = cfg['quantity'] if cfg['region'] in [0, 1] else cfg['quantity'] * 2
        group_bytes = 1 + 1 + 2 + 2 + data_len  # slave_id + data_type + addr + len + data
        total_bytes += group_bytes
        
        print(f"\n  组{i}:")
        print(f"    区域: {cfg['name']}")
        print(f"    功能码: 0x{cfg['func_code']:02X}")
        print(f"    起始地址: {cfg['start_addr']}")
        print(f"    数量: {cfg['quantity']}")
        print(f"    数据长度: {data_len} 字节")
    
    total_payload = 1 + 2 + total_bytes  # func_code + group_count + groups
    print(f"\n  总数据包大小: {total_payload} 字节")
    
    # 5. 显示数据包结构
    print("\n" + "=" * 80)
    print("5. 0x05 数据包结构示例")
    print("=" * 80)
    
    payload_hex = "05"
    payload_hex += f"{len(merged_configs):04X}"
    
    for cfg in merged_configs:
        data_type_map = {0x01: 0x00, 0x02: 0x01, 0x03: 0x04, 0x04: 0x03}
        data_type = data_type_map.get(cfg['func_code'], cfg['func_code'])
        data_len = cfg['quantity'] if cfg['region'] in [0, 1] else cfg['quantity'] * 2
        
        payload_hex += f"01{data_type:02X}{cfg['start_addr']:04X}{data_len:04X}"
        # 添加模拟数据
        payload_hex += "00" * data_len
    
    print(f"\n  {payload_hex}")
    
    # 结构说明
    print("\n  结构解析:")
    offset = 0
    print(f"  [{offset:2d}] 0x05                          - 功能码")
    offset += 1
    print(f"  [{offset:2d}] 0x{len(merged_configs):04X}                      - 组数 ({len(merged_configs)})")
    offset += 2
    
    for i, cfg in enumerate(merged_configs, 1):
        data_type_map = {0x01: 0x00, 0x02: 0x01, 0x03: 0x04, 0x04: 0x03}
        data_type = data_type_map.get(cfg['func_code'], cfg['func_code'])
        data_len = cfg['quantity'] if cfg['region'] in [0, 1] else cfg['quantity'] * 2
        
        print(f"\n  --- 组{i} ---")
        print(f"  [{offset:2d}] 0x01                          - 从站ID")
        offset += 1
        print(f"  [{offset:2d}] 0x{data_type:02X}                          - 数据类型 ({cfg['name']})")
        offset += 1
        print(f"  [{offset:2d}] 0x{cfg['start_addr']:04X}                      - 起始地址")
        offset += 2
        print(f"  [{offset:2d}] 0x{data_len:04X}                      - 数据长度 ({data_len} 字节)")
        offset += 2
        print(f"  [{offset:2d}] {'...':26s} - 数据 ({data_len} 字节)")
        offset += data_len
    
    print(f"\n  总计: {offset} 字节")
    
    print("\n" + "=" * 80)
    print("分析完成")
    print("=" * 80)

if __name__ == "__main__":
    main()

