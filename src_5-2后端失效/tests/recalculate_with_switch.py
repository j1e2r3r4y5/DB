#!/usr/bin/env python3
"""
重新精确计算 - 包含开关（6个数据项）
"""


def calculate_0x05_packet_size():
    """
    计算完整的6个数据项的0x05数据包
    """
    
    # 6个数据项配置
    data_items = [
        # (name, slave_id, modbus_type, addr, quantity, data_bytes)
        ("温度", 1, 4, 0, 2, 4),        # 保持寄存器 0-1
        ("湿度", 1, 4, 2, 1, 2),        # 保持寄存器 2
        ("功率", 1, 4, 3, 4, 8),        # 保持寄存器 3-6
        ("电能", 1, 4, 7, 2, 4),        # 保持寄存器 7-8
        ("设备描述", 1, 4, 10, 10, 20),  # 保持寄存器 10-19
        ("开关", 1, 0, 0, 1, 1),        # 线圈 0
    ]
    
    print("=" * 80)
    print("📦 6个数据项的精确数据包计算")
    print("=" * 80)
    
    # 计算每个数据项的大小
    packet_size = 0
    packet_size += 1  # 功能码
    packet_size += 2  # 数据项数量
    
    print(f"\n功能码 (0x05): 1 字节")
    print(f"数据项数量: 2 字节")
    print(f"\n{'数据项':<12} | {'头部':<6} | {'数据':<6} | {'小计':<6}")
    print("-" * 50)
    
    total_header = 0
    total_data = 0
    
    for name, slave_id, modbus_type, addr, quantity, data_bytes in data_items:
        header_size = 1 + 1 + 2 + 2  # slave_id + type + addr + len
        item_total = header_size + data_bytes
        
        total_header += header_size
        total_data += data_bytes
        packet_size += item_total
        
        print(f"{name:<12} | {header_size:<6} | {data_bytes:<6} | {item_total:<6}")
    
    print("-" * 50)
    print(f"{'总计':<12} | {total_header:<6} | {total_data:<6} | {packet_size:<6}")
    
    print(f"\n✅ 完整数据包大小: {packet_size} 字节")
    
    # 日流量计算
    heartbeat_interval = 30
    data_interval = 30
    
    heartbeat_count = 86400 // heartbeat_interval
    data_count = 86400 // data_interval
    
    heartbeat_total = heartbeat_count * 1
    data_total = data_count * packet_size
    
    uplink_total = heartbeat_total + data_total
    
    print("\n" + "=" * 80)
    print("📅 日流量计算（6个数据项）")
    print("=" * 80)
    print(f"💓 心跳包: {heartbeat_count}次 × 1B = {heartbeat_total:,}B ({heartbeat_total/1024:.2f}KB)")
    print(f"📊 数据上报: {data_count}次 × {packet_size}B = {data_total:,}B ({data_total/1024:.2f}KB)")
    print(f"\n📤 上行总计: {uplink_total:,}B ({uplink_total/1024:.2f}KB)")
    print(f"   ≈ {uplink_total/1024/1024:.3f}MB/天")
    print(f"   ≈ {uplink_total*30/1024/1024:.2f}MB/月")
    print(f"   ≈ {uplink_total*365/1024/1024:.2f}MB/年")
    
    return packet_size


if __name__ == "__main__":
    calculate_0x05_packet_size()
