#!/usr/bin/env python3
"""
DTU+Modbus Simulator - Main Entry Point
Supports running V1 (legacy) or V2 (improved) simulator with integrated Modbus TCP slave
"""

import sys
import time
import threading


def run_v1():
    """Run legacy V1 simulator"""
    print("Starting DTU Simulator V1 (Legacy)...")
    from dtu_simulator import DTUSimulator
    from modbus_tcp_slave import ModbusTCPSlave
    from config import MQTT_BROKER, MQTT_PORT, DEVICE_SERIAL, MODBUS_HOST, MODBUS_PORT, UP_TOPIC, DOWN_TOPIC

    modbus_slave = ModbusTCPSlave(MODBUS_HOST, MODBUS_PORT)
    modbus_slave.start()
    print(f"Modbus TCP Slave started on {MODBUS_HOST}:{MODBUS_PORT}")

    simulator = DTUSimulator(
        mqtt_broker=MQTT_BROKER,
        mqtt_port=MQTT_PORT,
        device_serial=DEVICE_SERIAL,
        modbus_host=MODBUS_HOST,
        modbus_port=MODBUS_PORT,
        up_topic=UP_TOPIC,
        down_topic=DOWN_TOPIC
    )

    simulator.start()
    print("DTU Simulator V1 started. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        simulator.stop()
        modbus_slave.stop()


def run_v2():
    """Run improved V2 simulator"""
    print("Starting DTU Simulator V2 (Improved)...")
    from dtu_simulator_v2 import DTUSimulatorV2
    from modbus_tcp_slave import ModbusTCPSlave
    from config import MQTT_BROKER, MQTT_PORT, DEVICE_SERIAL, MODBUS_HOST, MODBUS_PORT, UP_TOPIC, DOWN_TOPIC

    modbus_slave = ModbusTCPSlave(MODBUS_HOST, MODBUS_PORT)
    modbus_slave.start()
    print(f"Modbus TCP Slave started on {MODBUS_HOST}:{MODBUS_PORT}")

    simulator = DTUSimulatorV2(
        mqtt_broker=MQTT_BROKER,
        mqtt_port=MQTT_PORT,
        device_serial=DEVICE_SERIAL,
        modbus_host=MODBUS_HOST,
        modbus_port=MODBUS_PORT,
        up_topic=UP_TOPIC,
        down_topic=DOWN_TOPIC,
        heartbeat_interval=30,
        poll_interval=10
    )

    simulator.start()
    print("DTU Simulator V2 started. Press Ctrl+C to stop.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        simulator.stop()
        modbus_slave.stop()


def main():
    if len(sys.argv) > 1:
        version = sys.argv[1].lower()
        if version == "v1":
            run_v1()
            return
        elif version == "v2":
            run_v2()
            return
        else:
            print(f"Unknown version: {version}")
            print("Usage: python dtu_modbus_simulator.py [v1|v2]")
            print("Defaulting to V2 (recommended)...")

    run_v2()


if __name__ == "__main__":
    main()
