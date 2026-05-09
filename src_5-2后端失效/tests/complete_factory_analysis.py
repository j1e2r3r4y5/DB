#!/usr/bin/env python3
"""
完整工厂场景分析 - 包含所有工业物联网因素
基于单设备(6个数据项)扩展成工厂
"""


class FactoryTrafficAnalyzer:
    def __init__(self, name):
        self.name = name
        self.devices = []
        self.factors = {}
        self.base_single_device = {
            'data_items': 6,          # 6个数据项
            'packet_size': 78,         # 78字节/包
            'data_interval': 30,       # 30秒
            'heartbeat_interval': 30,  # 30秒
        }
    
    def add_device_group(self, name, count, from_config=None):
        """添加设备组"""
        device_config = from_config or self.base_single_device
        self.devices.append({
            'name': name,
            'count': count,
            'config': device_config
        })
    
    def set_factor(self, name, multiplier, description, category="general"):
        """设置影响因素"""
        self.factors[name] = {
            'multiplier': multiplier,
            'description': description,
            'category': category
        }
    
    def calculate_single_device_daily(self, config):
        """计算单设备日流量(纯应用层)"""
        data_count = 86400 // config['data_interval']
        heartbeat_count = 86400 // config['heartbeat_interval']
        
        data_traffic = data_count * config['packet_size']
        heartbeat_traffic = heartbeat_count * 1
        
        return {
            'data': data_traffic,
            'heartbeat': heartbeat_traffic,
            'total': data_traffic + heartbeat_traffic
        }
    
    def calculate_base_traffic(self):
        """计算基础流量(纯应用层，无额外因素)"""
        total_base = 0
        
        print(f"\n{'=' * 80}")
        print(f"🏭 {self.name} - 基础流量分析(纯应用层)")
        print(f"{'=' * 80}")
        
        for group in self.devices:
            single = self.calculate_single_device_daily(group['config'])
            group_total = single['total'] * group['count']
            total_base += group_total
            
            print(f"\n📦 {group['name']}: {group['count']}台")
            print(f"   单设备日流量: {self._format_bytes(single['total'])}")
            print(f"   设备组日流量: {self._format_bytes(group_total)}")
        
        print(f"\n📊 全厂基础日流量: {self._format_bytes(total_base)}")
        return total_base
    
    def analyze_all_factors(self, base_traffic):
        """分析所有影响因素"""
        print(f"\n{'=' * 80}")
        print(f"🔍 工业物联网因素影响分析")
        print(f"{'=' * 80}")
        
        categories = {}
        for name, factor in self.factors.items():
            cat = factor['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((name, factor))
        
        current_traffic = base_traffic
        factor_details = []
        
        for cat_name in ['network', 'reliability', 'operational', 'optimization']:
            if cat_name not in categories:
                continue
            
            cat_display = {
                'network': '🌐 网络协议层',
                'reliability': '🔗 可靠性保障',
                'operational': '⚙️ 运维管理',
                'optimization': '🚀 优化措施'
            }
            
            print(f"\n{cat_display.get(cat_name, cat_name)}:")
            print(f"{'-' * 50}")
            
            for name, factor in categories[cat_name]:
                old_traffic = current_traffic
                current_traffic *= factor['multiplier']
                change = current_traffic - old_traffic
                
                factor_details.append({
                    'name': name,
                    'multiplier': factor['multiplier'],
                    'description': factor['description'],
                    'traffic_change': change
                })
                
                sign = '+' if factor['multiplier'] >= 1 else ''
                print(f"   {name:15} ×{factor['multiplier']:<5} ({sign}{self._format_bytes(change)}) - {factor['description']}")
        
        return current_traffic, factor_details
    
    def run_complete_analysis(self):
        """运行完整分析"""
        # 计算基础流量
        base_traffic = self.calculate_base_traffic()
        
        # 分析因素影响
        final_traffic, factor_details = self.analyze_all_factors(base_traffic)
        
        # 汇总报告
        print(f"\n{'=' * 80}")
        print(f"📈 汇总报告")
        print(f"{'=' * 80}")
        
        print(f"\n📊 流量概览:")
        print(f"   基础流量: {self._format_bytes(base_traffic)}")
        print(f"   最终流量: {self._format_bytes(final_traffic)}")
        
        overhead = final_traffic - base_traffic
        overhead_pct = (overhead / base_traffic) * 100
        print(f"   额外开销: {self._format_bytes(overhead)} (+{overhead_pct:.1f}%)")
        
        print(f"\n📅 时间尺度:")
        print(f"   日流量: {self._format_bytes(final_traffic)}")
        print(f"   月流量: {self._format_bytes(final_traffic * 30)}")
        print(f"   年流量: {self._format_bytes(final_traffic * 365)}")
        
        # 因素影响排序
        print(f"\n📋 因素影响排序(从大到小):")
        factor_details.sort(key=lambda x: abs(x['traffic_change']), reverse=True)
        for f in factor_details[:5]:
            sign = '+' if f['multiplier'] >= 1 else '-'
            print(f"   {sign}{f['name']}: {self._format_bytes(abs(f['traffic_change']))}")
        
        return {
            'base': base_traffic,
            'final': final_traffic,
            'factors': factor_details
        }
    
    def _format_bytes(self, bytes_num):
        """格式化字节数"""
        if bytes_num < 1024:
            return f"{bytes_num:.0f}B"
        elif bytes_num < 1024 * 1024:
            return f"{bytes_num/1024:.2f}KB"
        elif bytes_num < 1024 * 1024 * 1024:
            return f"{bytes_num/1024/1024:.2f}MB"
        else:
            return f"{bytes_num/1024/1024/1024:.2f}GB"


def create_small_factory():
    """小型工厂场景"""
    factory = FactoryTrafficAnalyzer("小型零部件加工厂")
    
    # 设备配置
    factory.add_device_group("生产监测DTU", 8)    # 8台生产设备
    factory.add_device_group("环境监测DTU", 3)    # 3台环境监测
    factory.add_device_group("能源计量DTU", 2)    # 2台能源表计
    
    # 基础因素 - 增加
    factory.set_factor("MQTT协议头", 1.15, "MQTT固定头部2-5字节", "network")
    factory.set_factor("TCP/IP头", 1.12, "IP20字节 + TCP20字节", "network")
    factory.set_factor("QoS2确认", 1.18, "PUBREC/PUBREL/PUBCOMP", "reliability")
    factory.set_factor("设备重连", 1.05, "每日断线重连1-2次", "reliability")
    factory.set_factor("数据缓冲", 1.08, "网络抖动时的数据缓冲", "operational")
    factory.set_factor("日志上报", 1.10, "设备调试日志", "operational")
    
    # 优化因素 - 减少
    factory.set_factor("数据压缩", 0.85, "简单压缩算法", "optimization")
    
    return factory


def create_medium_factory():
    """中型工厂场景"""
    factory = FactoryTrafficAnalyzer("中型装备制造厂")
    
    # 设备配置
    factory.add_device_group("生产线DTU", 25)    # 5条线×5台
    factory.add_device_group("机器人DTU", 12)    # 12台工业机器人
    factory.add_device_group("AGV/DTU", 8)        # 8台AGV
    factory.add_device_group("质检DTU", 6)       # 6台质检设备
    factory.add_device_group("能源管理", 5)       # 5套能源系统
    factory.add_device_group("环境安全", 4)       # 4套环境监测
    
    # 基础因素
    factory.set_factor("MQTT协议头", 1.18, "MQTT头部 + 主题开销", "network")
    factory.set_factor("TCP/IP头", 1.15, "网络层协议开销", "network")
    factory.set_factor("QoS分级", 1.22, "关键数据QoS2 + 一般QoS1", "reliability")
    factory.set_factor("网络重传", 1.25, "丢包重传(假设1%丢包率)", "reliability")
    factory.set_factor("设备重连", 1.08, "断线重连 + 心跳", "reliability")
    factory.set_factor("告警数据", 1.15, "异常事件主动上报", "operational")
    factory.set_factor("远程诊断", 1.12, "定期诊断数据", "operational")
    factory.set_factor("日志上报", 1.18, "运行日志 + 错误日志", "operational")
    factory.set_factor("时间同步", 1.02, "NTP等时间同步", "operational")
    
    # 优化因素
    factory.set_factor("边缘压缩", 0.78, "边缘端数据压缩", "optimization")
    factory.set_factor("变化上报", 0.85, "只在数据变化时上报", "optimization")
    
    return factory


def create_large_factory():
    """大型工厂场景"""
    factory = FactoryTrafficAnalyzer("大型汽车整车制造厂")
    
    # 设备配置
    factory.add_device_group("冲压车间", 30)
    factory.add_device_group("焊接车间", 40)
    factory.add_device_group("涂装车间", 25)
    factory.add_device_group("总装车间", 45)
    factory.add_device_group("物流系统", 20)
    factory.add_device_group("质检系统", 15)
    factory.add_device_group("能源管理", 12)
    factory.add_device_group("环境安全", 10)
    factory.add_device_group("AGV车队", 18)
    factory.add_device_group("机器人集群", 28)
    
    # 全因素
    factory.set_factor("MQTT/TLS", 1.20, "TLS加密 + MQTT开销", "network")
    factory.set_factor("TCP/IP头", 1.18, "网络层完整开销", "network")
    factory.set_factor("Broker集群", 1.15, "多Broker同步", "network")
    factory.set_factor("QoS2保障", 1.25, "完整QoS2确认流", "reliability")
    factory.set_factor("网络重传", 1.35, "工业网络丢包(2-5%)", "reliability")
    factory.set_factor("断线重连", 1.12, "断线重连 + 状态同步", "reliability")
    factory.set_factor("告警风暴", 1.20, "异常事件爆发", "operational")
    factory.set_factor("远程诊断", 1.18, "诊断数据 + 抓包", "operational")
    factory.set_factor("日志全量", 1.22, "TRACE级日志", "operational")
    factory.set_factor("时间同步", 1.03, "精确时间同步", "operational")
    factory.set_factor("配置同步", 1.05, "配置参数同步", "operational")
    factory.set_factor("OTA更新", 1.10, "季度固件更新均摊", "operational")
    
    # 优化因素
    factory.set_factor("边缘计算", 0.70, "边缘数据预处理", "optimization")
    factory.set_factor("智能压缩", 0.68, "专门压缩算法", "optimization")
    factory.set_factor("批量上报", 0.85, "数据批量合并", "optimization")
    factory.set_factor("按需订阅", 0.92, "按需订阅而非全量", "optimization")
    
    return factory


def main():
    print("=" * 80)
    print("🏭 完整工厂场景分析 - 工业物联网总流量开销")
    print("=" * 80)
    
    # 三个场景分析
    scenarios = [
        create_small_factory(),
        create_medium_factory(),
        create_large_factory()
    ]
    
    results = []
    for scenario in scenarios:
        result = scenario.run_complete_analysis()
        results.append((scenario.name, result))
    
    # 横向对比
    print(f"\n{'=' * 80}")
    print(f"📊 场景横向对比")
    print(f"{'=' * 80}")
    print(f"\n{'场景':<20} | {'日流量':>15} | {'月流量':>15} | {'年流量':>15}")
    print(f"{'-' * 80}")
    
    def format_b(bytes_num):
        if bytes_num < 1024*1024*1024:
            return f"{bytes_num/1024/1024:>13.2f}MB"
        else:
            return f"{bytes_num/1024/1024/1024:>13.2f}GB"
    
    for name, result in results:
        print(f"{name:<20} | {format_b(result['final']):>15} | {format_b(result['final']*30):>15} | {format_b(result['final']*365):>15}")
    
    print(f"\n{'=' * 80}")
    print(f"💡 关键结论")
    print(f"{'=' * 80}")
    print(f"1. 工业物联网中，协议/可靠性开销可使基础流量×1.5-2.5")
    print(f"2. 运维管理类数据(日志/诊断/OTA)可增加+30-80%流量")
    print(f"3. 好的优化措施(边缘计算/压缩)可减少-30-50%流量")
    print(f"4. 实际监控1-2周的数据比理论估算准确10倍以上")
    print(f"5. 建议: 从小规模试点开始，收集数据后再精确规划")


if __name__ == "__main__":
    main()
