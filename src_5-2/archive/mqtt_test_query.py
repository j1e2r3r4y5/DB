import paho.mqtt.client as mqtt
import time

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Connected with result code {rc}")
    client.subscribe("/dtu/078AA6C46691/up", qos=1)
    print("已订阅 /dtu/078AA6C46691/up\n")

    # 先发送03查询，看看设备当前配置
    print("=" * 50)
    print("发送查询命令: 03")
    client.publish("/dtu/078AA6C46691/down", payload=bytes([0x03]), qos=1)
    print("等待响应...")

def on_message(client, userdata, msg):
    payload = msg.payload.hex().upper()
    print(f"\n收到响应: {payload}")
    print(f"原始字节: {msg.payload}")
    print(f"字节长度: {len(msg.payload)}")

    if payload.startswith("03"):
        # 解析03响应
        print("\n--- 03 响应解析 ---")
        data_count = int(payload[6:10], 16)
        print(f"声明的数据项数量: {data_count}")
        print(f"实际数据项:")
        # 每个数据项 6 字节 = 12 hex chars
        hex_data = payload[10:]  # 去掉 03 + 00 + data count (0F)
        item_count = len(hex_data) // 12
        for i in range(min(item_count, 10)):  # 最多显示10个
            offset = i * 12
            item = hex_data[offset:offset+12]
            slave = item[0:2]
            dtype = item[2:4]
            addr = item[4:8]
            length = item[8:12]
            print(f"  数据项{i+1}: 从站={slave}, 类型={dtype}, 地址={addr}, 长度={length}")
    elif payload.startswith("04"):
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