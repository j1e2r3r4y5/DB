
import paho.mqtt.client as mqtt
import time

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Connected with result code {rc}")
    client.subscribe("/dtu/A1B2C3D4/down")

def on_message(client, userdata, msg):
    print(f"Received message on {msg.topic}: {msg.payload.hex()}")

# 创建订阅者
sub_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "test_subscriber")
sub_client.on_connect = on_connect
sub_client.on_message = on_message

sub_client.connect("127.0.0.1", 1883, 60)
sub_client.loop_start()

time.sleep(1)

# 创建发布者
pub_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "test_publisher")
pub_client.connect("127.0.0.1", 1883, 60)

# 发布测试消息
test_payload = bytes.fromhex("040001010400000002")
print(f"Publishing test message: {test_payload.hex()}")
pub_client.publish("/dtu/A1B2C3D4/down", test_payload, qos=0)

time.sleep(3)

sub_client.loop_stop()
sub_client.disconnect()
pub_client.disconnect()
print("Test completed")
