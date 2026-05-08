#!/usr/bin/env python3
"""
真实工业环境额外流量分析工具
基于1个DTU网关+8个Modbus从站的合理架构
"""

class RealIndustrialTrafficAnalyzer:
    def __init__(self, theoretic_traffic_mb):
        self.device_count = 1  # 只有1个DTU网关
        self.modbus_slave_count = 8  # 8个Modbus从站
        self.theoretic_traffic_mb = theoretic_traffic_mb
        
        # 可配置参数（可调整）
        self.config = {
            "packet_loss_rate": 0.03,  # 3%丢包率
            "avg_offline_duration_hours": 1,  # 日均离线1小时
            "mqtt_keepalive_seconds": 60,  # 60秒保活
            "tls_enabled": True,
            "ota_update_mode": "differential",  # "full" or "differential"
            "network_type": "4g",  # "4g", "5g", "vpn", "wired"
        }
        
        # 8个Modbus从站的详细配置
        self.slaves = [
            {
                "slave_id": 1,
                "device_type": "环境监测传感器",
                "data_config": "温度(float32), 湿度(int16), 设备描述(string)",
                "total_bytes": 28,
            },
            {
                "slave_id": 2,
                "device_type": "功率监测模块",
                "data_config": "功率(float64), 电能(int32), 设备描述(string)",
                "total_bytes": 32,
            },
            {
                "slave_id": 3,
                "device_type": "PLC控制器1 - 机床A",
                "data_config": "温度(float32), 开关状态(bool), 运行状态(int16), 设备描述(string)",
                "total_bytes": 33,
            },
            {
                "slave_id": 4,
                "device_type": "PLC控制器2 - 机床B",
                "data_config": "温度(float32), 开关状态(bool), 运行状态(int16), 设备描述(string)",
                "total_bytes": 33,
            },
            {
                "slave_id": 5,
                "device_type": "伺服驱动器1",
                "data_config": "功率(float64), 转速(int32), 设备描述(string)",
                "total_bytes": 32,
            },
            {
                "slave_id": 6,
                "device_type": "伺服驱动器2",
                "data_config": "功率(float64), 转速(int32), 设备描述(string)",
                "total_bytes": 32,
            },
            {
                "slave_id": 7,
                "device_type": "安全光栅传感器",
                "data_config": "遮挡状态(bool), 设备描述(string)",
                "total_bytes": 22,
            },
            {
                "slave_id": 8,
                "device_type": "工业路由器",
                "data_config": "信号强度(int16), 连接状态(bool), 设备描述(string)",
                "total_bytes": 25,
            },
        ]
    
    def set_config(self, **kwargs):
        """更新配置"""
        self.config.update(kwargs)
    
    def calculate_network_retransmission(self):
        """1. 网络重传与抖动"""
        loss_rate = self.config["packet_loss_rate"]
        
        if loss_rate <= 0.005:
            multiplier = 1.08
            desc = "理想工业网络"
        elif loss_rate <= 0.01:
            multiplier = 1.12
            desc = "普通车间网络"
        elif loss_rate <= 0.03:
            multiplier = 1.25
            desc = "复杂电磁环境"
        elif loss_rate <= 0.05:
            multiplier = 1.38
            desc = "老旧厂房/无线干扰"
        else:
            multiplier = 1.8
            desc = "极端场景"
        
        extra_traffic = self.theoretic_traffic_mb * (multiplier - 1)
        
        return {
            "name": "网络重传与抖动",
            "description": desc,
            "extra_traffic_mb": extra_traffic,
            "percentage": (extra_traffic / self.theoretic_traffic_mb) * 100
        }
    
    def calculate_connection_storm(self):
        """2. 设备连接风暴与批量上线"""
        per_dtu_connection = 25  # KB/DTU连接（含TLS）
        daily_connection_events = 2  # 日均2次连接事件
        
        traffic_kb = per_dtu_connection * daily_connection_events
        traffic_mb = traffic_kb / 1024
        
        # 日均分摊
        daily_avg_mb = traffic_mb / 10  # 假设每10天有1次大规模连接
        
        return {
            "name": "设备连接风暴",
            "description": "车间重启、网络恢复、配置更新",
            "extra_traffic_mb": daily_avg_mb,
            "percentage": (daily_avg_mb / self.theoretic_traffic_mb) * 100
        }
    
    def calculate_offline_cache(self):
        """3. 离线数据缓存上报"""
        offline_hours = self.config["avg_offline_duration_hours"]
        
        # 单个DTU每小时数据量（估算）
        per_dtu_hourly_mb = 0.33  # 8.15 MB/天 ÷ 24小时
        
        cache_traffic_mb = offline_hours * per_dtu_hourly_mb
        
        return {
            "name": "离线数据缓存上报",
            "description": f"日均离线{offline_hours}小时",
            "extra_traffic_mb": cache_traffic_mb,
            "percentage": (cache_traffic_mb / self.theoretic_traffic_mb) * 100
        }
    
    def calculate_mqtt_keepalive(self):
        """4. MQTT保活包（PINGREQ/PINGRESP）"""
        keepalive_sec = self.config["mqtt_keepalive_seconds"]
        
        # 单次保活：PINGREQ(2B) + PINGRESP(2B) + TCP/IP(80B) = 84B
        per_keepalive_bytes = 84
        keepalive_count_per_day = 86400 // keepalive_sec
        
        per_dtu_daily_bytes = per_keepalive_bytes * keepalive_count_per_day
        total_bytes = per_dtu_daily_bytes
        total_mb = total_bytes / (1024 * 1024)
        
        return {
            "name": "MQTT保活包",
            "description": f"保活间隔{keepalive_sec}秒",
            "extra_traffic_mb": total_mb,
            "percentage": (total_mb / self.theoretic_traffic_mb) * 100
        }
    
    def calculate_dns_queries(self):
        """5. DNS查询与重连"""
        per_dtu_daily_queries = 24  # 每小时1次
        per_query_bytes = 70  # 平均DNS查询+响应
        
        total_bytes = per_dtu_daily_queries * per_query_bytes
        total_mb = total_bytes / (1024 * 1024)
        
        # DNS重试
        retry_mb = total_mb * 0.2  # 20%重试
        
        return {
            "name": "DNS查询与重连",
            "description": "每小时1次DNS查询，含20%重试",
            "extra_traffic_mb": total_mb + retry_mb,
            "percentage": ((total_mb + retry_mb) / self.theoretic_traffic_mb) * 100
        }
    
    def calculate_tls_overhead(self):
        """6. TLS加密与证书开销"""
        if not self.config["tls_enabled"]:
            return {
                "name": "TLS加密",
                "description": "TLS未启用",
                "extra_traffic_mb": 0,
                "percentage": 0
            }
        
        # 基础加密开销
        encryption_overhead_mb = self.theoretic_traffic_mb * 0.08  # 8%
        
        # 握手开销（会话恢复）
        daily_handshakes = 12  # 每2小时1次重连
        per_handshake_bytes = 250  # 会话恢复
        handshake_mb = (daily_handshakes * per_handshake_bytes) / (1024 * 1024)
        
        total_mb = encryption_overhead_mb + handshake_mb
        
        return {
            "name": "TLS加密与证书",
            "description": "加密开销+会话恢复握手",
            "extra_traffic_mb": total_mb,
            "percentage": (total_mb / self.theoretic_traffic_mb) * 100
        }
    
    def calculate_remote_debug(self):
        """7. 远程调试与数据包抓取"""
        # 日志拉取：1次/周，500 KB/次
        log_traffic_mb = (0.5) / 7
        
        # 抓包：2次/月，10 MB/次（抓部分从站）
        capture_traffic_mb = (2 * 10) / 30
        
        # 诊断命令：10次/月，100 KB/次
        diag_traffic_mb = (10 * 0.1) / 30
        
        total_mb = log_traffic_mb + capture_traffic_mb + diag_traffic_mb
        
        return {
            "name": "远程调试与抓包",
            "description": "日志+抓包+诊断命令（日均）",
            "extra_traffic_mb": total_mb,
            "percentage": (total_mb / self.theoretic_traffic_mb) * 100
        }
    
    def calculate_alarm_storm(self):
        """8. 告警风暴与并发事件"""
        # 单从站告警：1 KB/次，5次/天
        single_alarm_mb = (8 * 5 * 0.001)
        
        # 区域告警：2次/周，3-5个从站，5-10 KB/次
        area_alarm_mb = (2 * 0.008) / 7
        
        # 车间级告警：1次/月，全部从站，30-50 KB/次
        full_alarm_mb = 0.04 / 30
        
        total_mb = single_alarm_mb + area_alarm_mb + full_alarm_mb
        
        return {
            "name": "告警风暴与并发事件",
            "description": "单从站+区域+车间级告警（日均）",
            "extra_traffic_mb": total_mb,
            "percentage": (total_mb / self.theoretic_traffic_mb) * 100
        }
    
    def calculate_ota_update(self):
        """9. OTA固件更新（真实场景）"""
        mode = self.config["ota_update_mode"]
        
        if mode == "full":
            per_dtu_fw_mb = 0.5  # 500 KB
            ota_traffic_mb = (per_dtu_fw_mb) / 90  # 季度更新
            desc = "整包推送"
        else:
            per_dtu_fw_mb = 0.1  # 100 KB
            ota_traffic_mb = (per_dtu_fw_mb) / 90
            desc = "差分更新"
        
        return {
            "name": "OTA固件更新",
            "description": f"{desc}，季度更新（日均）",
            "extra_traffic_mb": ota_traffic_mb,
            "percentage": (ota_traffic_mb / self.theoretic_traffic_mb) * 100
        }
    
    def calculate_operator_encapsulation(self):
        """10. 网络运营商额外封装（4G/5G）"""
        network_type = self.config["network_type"]
        
        if network_type == "wired":
            multiplier = 1.0
            desc = "有线网络，无额外封装"
        elif network_type == "4g":
            multiplier = 1.12
            desc = "4G LTE，GTP隧道"
        elif network_type == "5g":
            multiplier = 1.18
            desc = "5G NR，GTP-U + SDAP"
        elif network_type == "vpn":
            multiplier = 1.25
            desc = "VPN专线，IPSec/GRE"
        else:
            multiplier = 1.0
            desc = "未知网络"
        
        extra_traffic_mb = self.theoretic_traffic_mb * (multiplier - 1)
        
        return {
            "name": "网络运营商封装",
            "description": desc,
            "extra_traffic_mb": extra_traffic_mb,
            "percentage": (extra_traffic_mb / self.theoretic_traffic_mb) * 100
        }
    
    def run_full_analysis(self):
        """运行完整分析"""
        print("=" * 80)
        print("🏭 真实工业环境额外流量分析 - 1个DTU网关 + 8个Modbus从站")
        print("=" * 80)
        
        print(f"\n📋 Modbus从站详细配置：")
        for slave in self.slaves:
            print(f"  Slave {slave['slave_id']}：{slave['device_type']}")
            print(f"    数据：{slave['data_config']}")
            print(f"    单包数据量：{slave['total_bytes']}字节")
        
        print(f"\n📊 理论估算基准流量：{self.theoretic_traffic_mb:.2f} MB/天")
        print(f"⚙️  配置参数：")
        print(f"    - 丢包率：{self.config['packet_loss_rate']*100:.0f}%")
        print(f"    - 离线时长：{self.config['avg_offline_duration_hours']}小时/天")
        print(f"    - MQTT保活：{self.config['mqtt_keepalive_seconds']}秒")
        print(f"    - TLS：{'启用' if self.config['tls_enabled'] else '禁用'}")
        print(f"    - OTA模式：{self.config['ota_update_mode']}")
        print(f"    - 网络类型：{self.config['network_type']}")
        
        print(f"\n{'=' * 80}")
        print(f"📋 11项额外流量详细分析")
        print(f"{'=' * 80}")
        
        results = []
        calculations = [
            self.calculate_network_retransmission,
            self.calculate_connection_storm,
            self.calculate_offline_cache,
            self.calculate_mqtt_keepalive,
            self.calculate_dns_queries,
            self.calculate_tls_overhead,
            self.calculate_remote_debug,
            self.calculate_alarm_storm,
            self.calculate_ota_update,
            self.calculate_operator_encapsulation,
        ]
        
        for calc_func in calculations:
            result = calc_func()
            results.append(result)
            
            print(f"\n📌 {result['name']}")
            print(f"    说明：{result['description']}")
            print(f"    额外流量：{result['extra_traffic_mb']:.2f} MB/天 (+{result['percentage']:.1f}%)")
        
        # 汇总
        print(f"\n{'=' * 80}")
        print(f"📈 汇总分析")
        print(f"{'=' * 80}")
        
        total_extra_mb = sum(r['extra_traffic_mb'] for r in results)
        total_percentage = (total_extra_mb / self.theoretic_traffic_mb) * 100
        final_total_mb = self.theoretic_traffic_mb + total_extra_mb
        
        print(f"\n📊 理论估算流量：{self.theoretic_traffic_mb:.2f} MB/天")
        print(f"📌 额外流量合计：{total_extra_mb:.2f} MB/天 (+{total_percentage:.1f}%)")
        print(f"🚀 真实工业环境总流量：{final_total_mb:.2f} MB/天")
        print(f"📅 月流量：{final_total_mb * 30:.0f} MB ({final_total_mb * 30 / 1024:.2f} GB)")
        print(f"📅 年流量：{final_total_mb * 365:.0f} MB ({final_total_mb * 365 / 1024:.2f} GB)")
        
        print(f"\n📊 额外流量占比排序（从大到小）：")
        results_sorted = sorted(results, key=lambda x: -x['extra_traffic_mb'])
        for r in results_sorted:
            if r['extra_traffic_mb'] > 0.01:
                print(f"    {r['name']}：{r['extra_traffic_mb']:.2f} MB (+{r['percentage']:.1f}%)")
        
        print(f"\n{'=' * 80}")
        print(f"💡 真实流量倍数关系：")
        print(f"    理论估算值：1x")
        print(f"    真实工业环境：{final_total_mb / self.theoretic_traffic_mb:.2f}x")
        print(f"{'=' * 80}")
        
        return {
            "theoretic_mb": self.theoretic_traffic_mb,
            "extra_mb": total_extra_mb,
            "final_total_mb": final_total_mb,
            "multiplier": final_total_mb / self.theoretic_traffic_mb,
            "details": results
        }


def main():
    # 主要场景：小型机加工车间（1个DTU网关 + 8个Modbus从站）
    print("\n" + "=" * 80)
    print("综合工业场景：小型机加工车间（1个DTU网关 + 8个Modbus从站）")
    print("=" * 80)
    main_analyzer = RealIndustrialTrafficAnalyzer(theoretic_traffic_mb=8.15)
    main_result = main_analyzer.run_full_analysis()
    
    # 可选：显示极端场景对比
    print("\n" + "=" * 80)
    print("对比场景：极端工业环境（1个DTU网关 + 8个Modbus从站，5%丢包率，5G网络）")
    print("=" * 80)
    extreme_analyzer = RealIndustrialTrafficAnalyzer(theoretic_traffic_mb=8.15)
    extreme_analyzer.set_config(
        packet_loss_rate=0.05,
        avg_offline_duration_hours=2,
        network_type="5g"
    )
    extreme_result = extreme_analyzer.run_full_analysis()


if __name__ == "__main__":
    main()
