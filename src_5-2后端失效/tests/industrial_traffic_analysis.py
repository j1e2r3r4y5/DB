#!/usr/bin/env python3
"""
工业生产环境传输量分析
考虑多设备、多从站、网络开销等实际因素
"""


class IndustrialScenario:
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.devices = []
        self.extra_factors = {}
    
    def add_device(self, serial, slave_count, data_points, interval_seconds=30):
        self.devices.append({
            'serial': serial,
            'slave_count': slave_count,
            'data_points': data_points,
            'interval': interval_seconds
        })
    
    def set_extra_factor(self, name, multiplier, description):
        self.extra_factors[name] = {
            'multiplier': multiplier,
            'description': description
        }
    
    def calculate_traffic(self):
        total_uplink = 0
        total_downlink = 0
        
        for dev in self.devices:
            # 单设备传输量计算
            data_points = dev['data_points']
            interval = dev['interval']
            
            # 单次数据包大小估算 (平均每个数据点15字节)
            packet_size = 3 + (6 + 10) * data_points  # 功能码+数量 + (头部+数据)*数据点数
            
            # 心跳包
            heartbeat_count = 86400 // interval
            heartbeat_total = heartbeat_count * 1
            
            # 数据上报
            data_count = 86400 // interval
            data_total = data_count * packet_size
            
            dev_uplink = heartbeat_total + data_total
            total_uplink += dev_uplink
            
            # 下行估算 (配置+远程置数)
            dev_downlink = (data_points * 10) + 100  # 配置下发 + 操作
            total_downlink += dev_downlink
        
        # 应用额外因素
        for name, factor in self.extra_factors.items():
            total_uplink *= factor['multiplier']
            total_downlink *= factor['multiplier']
        
        return {
            'uplink': total_uplink,
            'downlink': total_downlink,
            'total': total_uplink + total_downlink
        }


def create_small_factory():
    """小型工厂场景"""
    scenario = IndustrialScenario(
        "小型工厂",
        "5台设备，每台1-2个从站，基础监控"
    )
    
    for i in range(5):
        scenario.add_device(
            serial=f"DEV{i+1:02d}",
            slave_count=2,
            data_points=8,
            interval_seconds=30
        )
    
    scenario.set_extra_factor('network_overhead', 1.3, 'MQTT/TCP/IP协议头开销')
    scenario.set_extra_factor('qos_ack', 1.15, 'QoS 2确认流量')
    
    return scenario


def create_medium_factory():
    """中型工厂场景"""
    scenario = IndustrialScenario(
        "中型工厂",
        "20台设备，每台2-5个从站，完整监控"
    )
    
    for i in range(20):
        scenario.add_device(
            serial=f"DEV{i+1:02d}",
            slave_count=4,
            data_points=20,
            interval_seconds=15
        )
    
    scenario.set_extra_factor('network_overhead', 1.35, 'MQTT/TCP/IP协议头开销')
    scenario.set_extra_factor('qos_ack', 1.2, 'QoS 2确认流量')
    scenario.set_extra_factor('alarm_data', 1.1, '告警事件数据')
    
    return scenario


def create_large_factory():
    """大型工厂场景"""
    scenario = IndustrialScenario(
        "大型工厂",
        "50台设备，每台5-10个从站，高密度监控"
    )
    
    for i in range(50):
        scenario.add_device(
            serial=f"DEV{i+1:02d}",
            slave_count=8,
            data_points=40,
            interval_seconds=5
        )
    
    scenario.set_extra_factor('network_overhead', 1.4, 'MQTT/TCP/IP协议头开销')
    scenario.set_extra_factor('qos_ack', 1.25, 'QoS 2确认流量')
    scenario.set_extra_factor('alarm_data', 1.15, '告警事件数据')
    scenario.set_extra_factor('edge_processing', 0.8, '边缘计算数据压缩')
    
    return scenario


def format_bytes(bytes_num):
    """格式化字节数"""
    if bytes_num < 1024:
        return f"{bytes_num:.0f} B"
    elif bytes_num < 1024 * 1024:
        return f"{bytes_num / 1024:.2f} KB"
    elif bytes_num < 1024 * 1024 * 1024:
        return f"{bytes_num / 1024 / 1024:.2f} MB"
    else:
        return f"{bytes_num / 1024 / 1024 / 1024:.2f} GB"


def analyze_scenario(scenario):
    """分析场景并打印报告"""
    print("\n" + "=" * 80)
    print(f"🏭 {scenario.name}")
    print("=" * 80)
    print(f"📝 {scenario.description}")
    print(f"📦 设备数量: {len(scenario.devices)}")
    
    traffic = scenario.calculate_traffic()
    
    print("\n📊 日流量分析:")
    print(f"   📤 上行: {format_bytes(traffic['uplink'])}")
    print(f"   📥 下行: {format_bytes(traffic['downlink'])}")
    print(f"   📈 总计: {format_bytes(traffic['total'])}")
    
    print("\n📅 月流量 (30天):")
    print(f"   📤 上行: {format_bytes(traffic['uplink'] * 30)}")
    print(f"   📥 下行: {format_bytes(traffic['downlink'] * 30)}")
    print(f"   📈 总计: {format_bytes(traffic['total'] * 30)}")
    
    print("\n📅 年流量 (365天):")
    print(f"   📤 上行: {format_bytes(traffic['uplink'] * 365)}")
    print(f"   📥 下行: {format_bytes(traffic['downlink'] * 365)}")
    print(f"   📈 总计: {format_bytes(traffic['total'] * 365)}")
    
    if scenario.extra_factors:
        print("\n🔧 额外因素:")
        for name, factor in scenario.extra_factors.items():
            print(f"   {name}: ×{factor['multiplier']} ({factor['description']})")


def main():
    print("=" * 80)
    print("🏭 工业生产环境传输量分析")
    print("=" * 80)
    
    scenarios = [
        create_small_factory(),
        create_medium_factory(),
        create_large_factory()
    ]
    
    for scenario in scenarios:
        analyze_scenario(scenario)
    
    print("\n" + "=" * 80)
    print("💡 优化建议")
    print("=" * 80)
    print("1. 增加上报间隔：从5秒改为30秒可减少83%流量")
    print("2. 数据压缩：边缘端数据压缩可减少30-50%流量")
    print("3. 变化上报：只在数据变化时上报，而不是定时上报")
    print("4. QoS优化：非关键数据用QoS 0，减少确认流量")
    print("5. 批量传输：合并多个数据点，减少包数量")
    print("=" * 80)


if __name__ == "__main__":
    main()
