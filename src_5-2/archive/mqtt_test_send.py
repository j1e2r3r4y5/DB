import paho.mqtt.client as mqtt
import time

broker = "112.6.224.25"
port = 20042
dev_serial = "078AA6C46691"

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"连接成功 (rc={rc})")
    client.subscribe(f"/dtu/{dev_serial}/up", qos=1)
    print(f"已订阅 /dtu/{dev_serial}/up\n")

    payload_hex = "040009010400000001"
    print(f"发送: {payload_hex}")
    print(f" => 04 00 09 01 04 00 00 00 01\n")
    client.publish(f"/dtu/{dev_serial}/down", payload=bytes.fromhex(payload_hex), qos=1)
    print("已发送，等待响应...")

def on_message(client, userdata, msg):
    payload = msg.payload.hex().upper()
    print(f"收到: {payload}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

print(f"连接 {broker}:{port}...")
client.connect(broker, port, 60)
client.loop_forever()