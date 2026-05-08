#!/usr/bin/env python3
"""
传输量实际测试脚本
测量设备与平台之间的实际 MQTT 流量
"""

import paho.mqtt.client as mqtt
import time
import threading
from collections import defaultdict


class TrafficAnalyzer:
    def __init__(self, broker="127.0.0.1", port=1883):
        self.broker = broker
        self.port = port
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "traffic_analyzer")
        
        # 统计数据
        self.uplink_bytes = 0
        self.downlink_bytes = 0
        self.uplink_count = 0
        self.downlink_count = 0
        self.message_details = defaultdict(list)
        self.running = False
        
        # 回调设置
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        
        self.start_time = None
        self.lock = threading.Lock()
    
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        print(f"✅ 连接成功 (rc={rc})")
        # 订阅上行主题（设备→平台）
        client.subscribe("/dtu/+/up")
        # 订阅下行主题（平台→设备）
        client.subscribe("/dtu/+/down")
    
    def _on_message(self, client, userdata, msg):
        topic_parts = msg.topic.split("/")
        direction = "上行" if topic_parts[-1] == "up" else "下行"
        msg_len = len(msg.payload)
        
        with self.lock:
            if direction == "上行":
                self.uplink_bytes += msg_len
                self.uplink_count += 1
                self.message_details["uplink"].append({
                    "time": time.time(),
                    "len": msg_len,
                    "payload": msg.payload.hex()[:50] + "..." if len(msg.payload) > 50 else msg.payload.hex()
                })
            else:
                self.downlink_bytes += msg_len
                self.downlink_count += 1
                self.message_details["downlink"].append({
                    "time": time.time(),
                    "len": msg_len,
                    "payload": msg.payload.hex()[:50] + "..." if len(msg.payload) > 50 else msg.payload.hex()
                })
        
        print(f"📨 {direction}: {msg_len} 字节 | 总数: {self.uplink_count + self.downlink_count}")
    
    def _on_publish(self, client, userdata, mid, reason_code=None, properties=None):
        pass
    
    def start(self):
        """开始流量监控"""
        self.running = True
        self.start_time = time.time()
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_start()
        print("🔍 开始监控 MQTT 流量...")
        print(f"   订阅主题: /dtu/+/up, /dtu/+/down")
        print("-" * 60)
    
    def stop(self):
        """停止监控"""
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
    
    def print_stats(self):
        """打印统计信息"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        
        print("\n" + "=" * 60)
        print("📊 实际流量统计报告")
        print("=" * 60)
        print(f"📅 监控时长: {elapsed:.1f} 秒")
        print()
        
        print("📤 上行流量 (设备 → 平台):")
        print(f"   消息数: {self.uplink_count}")
        print(f"   总字节: {self.uplink_bytes:,} B ({self.uplink_bytes / 1024:.2f} KB)")
        if self.uplink_count > 0:
            print(f"   平均大小: {self.uplink_bytes / self.uplink_count:.1f} B/条")
        if elapsed > 0:
            print(f"   平均速率: {self.uplink_bytes / elapsed:.2f} B/s")
        
        print("\n📥 下行流量 (平台 → 设备):")
        print(f"   消息数: {self.downlink_count}")
        print(f"   总字节: {self.downlink_bytes:,} B ({self.downlink_bytes / 1024:.2f} KB)")
        if self.downlink_count > 0:
            print(f"   平均大小: {self.downlink_bytes / self.downlink_count:.1f} B/条")
        if elapsed > 0:
            print(f"   平均速率: {self.downlink_bytes / elapsed:.2f} B/s")
        
        print("\n📈 总计:")
        print(f"   总消息: {self.uplink_count + self.downlink_count}")
        print(f"   总字节: {self.uplink_bytes + self.downlink_bytes:,} B ({(self.uplink_bytes + self.downlink_bytes) / 1024:.2f} KB)")
        
        if elapsed > 0:
            hours = elapsed / 3600
            day = hours * 24
            print(f"\n📅 日流量估算 (按当前速率):")
            print(f"   日上行: {(self.uplink_bytes / elapsed * 86400):,.0f} B ({(self.uplink_bytes / elapsed * 86400) / 1024 / 1024:.2f} MB)")
            print(f"   日下行: {(self.downlink_bytes / elapsed * 86400):,.0f} B ({(self.downlink_bytes / elapsed * 86400) / 1024 / 1024:.2f} MB)")
            print(f"   日总计: {((self.uplink_bytes + self.downlink_bytes) / elapsed * 86400):,.0f} B ({((self.uplink_bytes + self.downlink_bytes) / elapsed * 86400) / 1024 / 1024:.2f} MB)")
        
        print("\n🔍 消息详情样本 (前5条):")
        for direction, msgs in self.message_details.items():
            print(f"\n   {direction.upper()}:")
            for i, msg in enumerate(msgs[:5]):
                print(f"     [{i+1}] {msg['len']} 字节 - {msg['payload']}")
        
        print("\n" + "=" * 60)


def main():
    print("=" * 60)
    print("🚀 MQTT 实际传输量测试工具")
    print("=" * 60)
    
    analyzer = TrafficAnalyzer()
    
    try:
        analyzer.start()
        
        # 监控 60 秒
        print(f"\n⏱️  监控进行中 (1分钟)...")
        for i in range(60):
            time.sleep(1)
            if (i + 1) % 10 == 0:
                print(f"   已监控 {i+1} 秒...")
        
        analyzer.print_stats()
        
    except KeyboardInterrupt:
        print("\n⚠️  用户中断")
        analyzer.print_stats()
    finally:
        analyzer.stop()


if __name__ == "__main__":
    main()
