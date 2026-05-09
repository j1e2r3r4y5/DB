#!/usr/bin/env python3
"""
测试发送空配置
"""

import paho.mqtt.client as mqtt
import time

# MQTT 配置
MQTT_BROKER = '127.0.0.1'
MQTT_PORT = 1883
DEV_SERIAL = 'A1B2C3D4'
DOWN_TOPIC = f'/dtu/{DEV_SERIAL}/down'

def on_connect(client, userdata, flags, rc):
    print(f'[MQTT] Connected with result code {rc}')
    
    # 发送空配置
    # 协议: 04 00 00 (功能码04, 0组)
    empty_payload = bytes([0x04, 0x00, 0x00])
    print(f'[MQTT] Sending empty config: {empty_payload.hex()}')
    
    client.publish(DOWN_TOPIC, empty_payload, qos=0)
    print(f'[MQTT] Empty config sent!')
    
    time.sleep(1)
    print('[Test] Done!')
    client.disconnect()

def main():
    print('[Test] Starting empty config test...')
    
    client = mqtt.Client()
    client.on_connect = on_connect
    
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

if __name__ == '__main__':
    main()
