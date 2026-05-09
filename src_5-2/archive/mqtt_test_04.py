import paho.mqtt.client as mqtt
import time

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Connected with result code {rc}")
    client.subscribe("/dtu/078AA6C46691/up", qos=1)
    print("已订阅 /dtu/078AA6C46691/up\n")

    # 测试1: 先清除配置 04 00 00 00
    print("=" * 50)
    print("测试1: 清除配置 04 00 00 00")
    client.publish("/dtu/078AA6C46691/down", payload=bytes([0x04, 0x00, 0x00, 0x00]), qos=1)
    time.sleep(2)

    # 测试2: 尝试设置配置 04 00 01 01 04 00 00 00 02
    print("=" * 50)
    print("测试2: 设置配置 04 00 01 01 04 00 00 00 02")
    client.publish("/dtu/078AA6C46691/down", payload=bytes([0x04, 0x00, 0x01, 0x01, 0x04, 0x00, 0x00, 0x00, 0x02]), qos=1)
    print("命令已发送")

def on_message(client, userdata, msg):
    payload = msg.payload.hex().upper()
    print(f"\n收到响应: {payload}")
    if payload.startswith("04"):
        status = payload[2:4]
        status_map = {"00": "成功", "01": "打开文件错误", "02": "写入文件错误", "03": "数据类型错误", "04": "查询数据越界", "05": "数据接收长度错误"}
        print(f"功能码: 04, 状态码: {status} ({status_map.get(status, '未知')})")
    elif payload.startswith("05"):
        print(f"功能码: 05 (数据上发)")
    print("-" * 50)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

broker = "112.6.224.25"
port = 20042

print(f"连接 MQTT Broker {broker}:{port}...")
client.connect(broker, port, 60)
client.loop_forever()