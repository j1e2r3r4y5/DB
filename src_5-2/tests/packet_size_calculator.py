#!/usr/bin/env python3
"""
精确计算数据包大小
基于 simulator_v3 的实际代码逻辑
"""

import sys
sys.path.insert(0, '../simulator_v3')

from config import config


def calculate_0x05_packet_size(configs):
    """
    计算 0x05 数据包大小
    
    结构:
    - 功能码 (1)
    - 数据项数量 (2)
    - 每个数据项:
      - 从站地址 (1)
      - 数据类型 (1)
      - 起始地址 (2)
      - 数据长度 (2)
      - 实际数据 (N)
    """
    total_size = 1 + 2  # 功能码 + 数量
    
    for cfg in configs:
        # 数据项头部
        total_size += 1 + 1 + 2 + 2  # slave_id + type + addr + len
        
        # 实际数据
        if cfg['func_code'] in (1, 2):
            # 线圈/离散输入: quantity个位，需要 (quantity + 7) // 8 字节
            data_len = (cfg['quantity'] + 7) // 8
        elif cfg['func_code'] in (3, 4):
            # 寄存器: quantity个寄存器，每个2字节
            data_len = cfg['quantity'] * 2
        else:
            data_len = 0
        
        total_size += data_len
    
    return total_size


def analyze_default_config():
    """分析默认配置的数据包大小"""
    print("=" * 70)
    print("📦 数据包大小精确计算")
    print("=" * 70)
    
    # 默认配置 (来自 main.py:100-135)
    default_configs = [
        {'slave_id': 1, 'func_code': 3, 'start_addr': 0, 'quantity': 2},   # 温度
        {'slave_id': 1, 'func_code': 3, 'start_addr': 2, 'quantity': 1},   # 湿度
        {'slave_id': 1, 'func_code': 3, 'start_addr': 3, 'quantity': 4},   # 功率
        {'slave_id': 1, 'func_code': 3, 'start_addr': 7, 'quantity': 2},   # 电能
        {'slave_id': 1, 'func_code': 3, 'start_addr': 10, 'quantity': 10}, # 设备描述
    ]
    
    print("\n📋 默认数据配置:")
    for i, cfg in enumerate(default_configs):
        if cfg['func_code'] in (3, 4):
            data_len = cfg['quantity'] * 2
        else:
            data_len = (cfg['quantity'] + 7) // 8
        print(f"   [{i+1}] 从站={cfg['slave_id']}, 类型={cfg['func_code']}, "
              f"地址={cfg['start_addr']}, 数量={cfg['quantity']} → 数据={data_len}字节")
    
    packet_size = calculate_0x05_packet_size(default_configs)
    print(f"\n📊 单次 0x05 数据包大小: {packet_size} 字节")
    
    # 详细分解
    print("\n🔍 数据包结构分解:")
    print(f"   功能码 (0x05): 1 字节")
    print(f"   数据项数量: 2 字节")
    
    data_part = packet_size - 3
    print(f"   数据部分: {data_part} 字节")
    
    per_item = (data_part) // len(default_configs)
    print(f"   平均每个数据项: {per_item} 字节")
    
    # 心跳包
    print("\n💓 心跳包 (0x00): 1 字节")
    
    # 配置响应包
    print("✅ 配置响应包 (0x02/04/06): 2 字节")
    
    # 日流量估算
    print("\n" + "=" * 70)
    print("📅 日流量详细估算 (默认配置)")
    print("=" * 70)
    
    heartbeat_interval = config.HEARTBEAT_INTERVAL  # 30s
    data_interval = config.DATA_UPLOAD_INTERVAL    # 30s
    
    heartbeat_count = 86400 // heartbeat_interval
    data_count = 86400 // data_interval
    
    heartbeat_total = heartbeat_count * 1
    data_total = data_count * packet_size
    
    print(f"\n📤 上行流量:")
    print(f"   心跳包: {heartbeat_count} 次 × 1 字节 = {heartbeat_total:,} 字节 ({heartbeat_total/1024:.2f} KB)")
    print(f"   数据上报: {data_count} 次 × {packet_size} 字节 = {data_total:,} 字节 ({data_total/1024:.2f} KB)")
    
    uplink_total = heartbeat_total + data_total
    print(f"   上行总计: {uplink_total:,} 字节 ({uplink_total/1024:.2f} KB)")
    
    # 下行估算
    print(f"\n📥 下行流量 (估算):")
    print(f"   假设日均: 10 次配置操作 × 20 字节 = 200 字节")
    print(f"   假设日均: 5 次远程置数 × 10 字节 = 50 字节")
    print(f"   下行总计: 250 字节")
    
    total = uplink_total + 250
    print(f"\n📈 日总流量: {total:,} 字节 ({total/1024:.2f} KB, {total/1024/1024:.3f} MB)")
    
    # 月度估算
    print(f"\n📅 月流量 (30天): {total*30:,} 字节 ({total*30/1024/1024:.2f} MB)")
    
    print("\n" + "=" * 70)
    print("⚠️  注意事项:")
    print("=" * 70)
    print("1. 上述估算不包含 MQTT 协议头、TCP/IP 头")
    print("2. QoS 2 会有额外的确认流量 (PUBREC, PUBREL, PUBCOMP)")
    print("3. 下行流量取决于用户操作频率")
    print("4. 实际流量可能因数据配置不同而变化")
    print("=" * 70)


def compare_with_previous():
    """与之前的估算对比"""
    print("\n" + "=" * 70)
    print("🔄 估算值对比")
    print("=" * 70)
    
    # 之前的估算
    previous = {
        'packet': 133,
        'daily_uplink': 386 * 1024,  # 386 KB
    }
    
    # 实际计算
    default_configs = [
        {'slave_id': 1, 'func_code': 3, 'start_addr': 0, 'quantity': 2},
        {'slave_id': 1, 'func_code': 3, 'start_addr': 2, 'quantity': 1},
        {'slave_id': 1, 'func_code': 3, 'start_addr': 3, 'quantity': 4},
        {'slave_id': 1, 'func_code': 3, 'start_addr': 7, 'quantity': 2},
        {'slave_id': 1, 'func_code': 3, 'start_addr': 10, 'quantity': 10},
    ]
    actual_packet = calculate_0x05_packet_size(default_configs)
    data_count = 86400 // 30
    heartbeat_count = 86400 // 30
    actual_daily = data_count * actual_packet + heartbeat_count * 1
    
    print(f"\n📦 单次数据包:")
    print(f"   之前估算: {previous['packet']} 字节")
    print(f"   实际计算: {actual_packet} 字节")
    print(f"   差异: {actual_packet - previous['packet']} 字节 ({((actual_packet/previous['packet'])-1)*100:.1f}%)")
    
    print(f"\n📅 日上行流量:")
    print(f"   之前估算: {previous['daily_uplink']:,} 字节 ({previous['daily_uplink']/1024:.1f} KB)")
    print(f"   实际计算: {actual_daily:,} 字节 ({actual_daily/1024:.1f} KB)")
    print(f"   差异: {actual_daily - previous['daily_uplink']:,} 字节 ({((actual_daily/previous['daily_uplink'])-1)*100:.1f}%)")


if __name__ == "__main__":
    analyze_default_config()
    compare_with_previous()
