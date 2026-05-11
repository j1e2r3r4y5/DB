#!/usr/bin/env python3
"""
Configuration for DTU+Modbus Simulator
"""

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883
DEVICE_SERIAL = "A1B2C3D4"
MODBUS_HOST = "127.0.0.1"
MODBUS_PORT = 502
HEARTBEAT_INTERVAL = 30
UP_TOPIC = f"/dtu/{DEVICE_SERIAL}/up"
DOWN_TOPIC = f"/dtu/{DEVICE_SERIAL}/down"


class SimulatorConfig:
    def __init__(self):
        self.mqtt_broker = MQTT_BROKER
        self.mqtt_port = MQTT_PORT
        self.device_serial = DEVICE_SERIAL
        self.modbus_host = MODBUS_HOST
        self.modbus_port = MODBUS_PORT
        self.heartbeat_interval = HEARTBEAT_INTERVAL
        self.up_topic = f"/dtu/{self.device_serial}/up"
        self.down_topic = f"/dtu/{self.device_serial}/down"

    def print_info(self):
        print(f"MQTT Broker: {self.mqtt_broker}:{self.mqtt_port}")
        print(f"Device Serial: {self.device_serial}")
        print(f"Up Topic: {self.up_topic}")
        print(f"Down Topic: {self.down_topic}")
        print(f"Modbus TCP: {self.modbus_host}:{self.modbus_port}")
