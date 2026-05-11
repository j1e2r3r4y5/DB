#!/usr/bin/env python3
"""
测试工具：手动发送04配置到模拟器，验证模拟器能否正确响应并发送05数据
"""

import paho.mqtt.client as mqtt
import time
import struct

DEVICE_SERIAL = "A1B2C3D4"
DOWN_TOPIC = f"/dtu/{DEVICE_SERIAL}/down"
MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883

def build_04_config():
    """构建04下发配置：温度+湿度（两个相邻寄存器）"""
    payload = bytes([0x04])  # 功能码
    payload += struct.pack('>H', 1)  # 数据组数 = 1
    payload += bytes([0x01])  # 从站地址 = 1
    payload += bytes([0x04])  # 类型 = 4（保持寄存器）
    payload += struct.pack('>H', 0)  # 起始地址 = 0
    payload += struct.pack('>H', 2)  # 数量 = 2（温度+湿度）
    return payload

def main():
    print("=" * 60)
    print("测试：手动发送04配置到模拟器")
    print("=" * 60)

    client = mqtt.Client(client_id="test_sender")
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()

    time.sleep(1)

    config_payload = build_04_config()
    print(f"发送04配置到 {DOWN_TOPIC}")
    print(f"Payload: {config_payload.hex()}")

    result = client.publish(DOWN_TOPIC, config_payload, qos=2)
    print(f"Publish result: {result.rc}")

    if result.rc == 0:
        print("✅ 消息发送成功！")
        print("请观察模拟器窗口是否出现 [DOWNLINK] 和 [UPLINK]")
    else:
        print(f"❌ 消息发送失败: {result.rc}")

    time.sleep(5)

    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    main()
