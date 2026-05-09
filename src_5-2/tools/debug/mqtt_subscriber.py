import paho.mqtt.client as mqtt
import time

def on_connect(client, userdata, flags, rc, properties=None):
    print(f"Connected with result code {rc}")
    client.subscribe("/dtu/078AA6C46691/up", qos=1)
    print("Subscribed to /dtu/078AA6C46691/up")

def on_message(client, userdata, msg):
    payload = msg.payload.hex().upper()
    print(f"Time: {time.strftime('%H:%M:%S')}")
    print(f"Topic: {msg.topic}")
    print(f"Payload (hex): {payload}")
    print(f"Payload (bytes): {msg.payload}")
    print("-" * 50)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

broker = "112.6.224.25"
port = 20042

print(f"Connecting to MQTT broker {broker}:{port}...")
client.connect(broker, port, 60)
client.loop_forever()