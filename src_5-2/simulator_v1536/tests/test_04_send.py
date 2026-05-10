"""
手动测试脚本 - 验证全链路

使用方法:
1. 启动模拟器: python main.py
2. 在另一个终端运行: python -m pytest tests/test_04_send.py -v
   或从 src_5-2 目录运行: cd .. && python -m pytest simulator_v3/tests/test_04_send.py -v
"""

import unittest
import sys
import os
import time
import struct

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mqtt_client import MQTTClientManager
from core.config_manager import ConfigManager
from protocol.handler import HandlerRegistry
from protocol.heartbeat_handler import HeartbeatHandler
from protocol.data_config_handler import DataConfigHandler
from data.device_pool import DevicePool
from modbus.tcp_server import ModbusTCPServer
from modbus.request_handler import ModbusRequestHandler


class TestManual(unittest.TestCase):
    def test_modbus_server(self):
        print("\n=== 测试 Modbus TCP 服务器 ===")
        device_pool = DevicePool()
        server = ModbusTCPServer(host='127.0.0.1', port=5503)

        for slave_id in device_pool.get_all_slave_ids():
            device = device_pool.get_device(slave_id)
            if device:
                handler = ModbusRequestHandler(device)
                server.set_device_handler(slave_id, handler)

        try:
            server.start()
            print(f"✓ Modbus TCP 服务器启动成功 (127.0.0.1:5503)")

            time.sleep(1)

            device = device_pool.get_device(1)
            if device:
                device.holding_registers._data[0] = 250
                device.holding_registers._data[1] = 600

            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(('127.0.0.1', 5503))

            request = struct.pack('>HHH', 1, 0, 6)
            request += bytes([0x01])
            request += bytes([0x03])
            request += struct.pack('>HH', 0, 2)

            sock.send(request)
            response = sock.recv(1024)
            sock.close()

            self.assertGreater(len(response), 8)
            print(f"✓ Modbus 读取响应成功: {response.hex()}")

        finally:
            server.stop()

    def test_protocol_handlers(self):
        print("\n=== 测试协议处理器 ===")

        config_manager = ConfigManager()
        registry = HandlerRegistry()

        heartbeat_handler = HeartbeatHandler()
        data_config_handler = DataConfigHandler(config_manager)

        registry.register(heartbeat_handler)
        registry.register(data_config_handler)

        heartbeat_payload = bytes([0x00])
        heartbeat_response = registry.handle(heartbeat_payload)
        self.assertIsNotNone(heartbeat_response)
        self.assertEqual(heartbeat_response[0], 0x00)
        print("✓ 心跳处理器测试成功")

        data_config_payload = bytes([
            0x04,
            0x00, 0x01,
            0x01, 0x03, 0x00, 0x00, 0x00, 0x02
        ])
        data_config_response = registry.handle(data_config_payload)
        self.assertIsNotNone(data_config_response)
        self.assertEqual(data_config_response[0], 0x04)
        print("✓ 数据配置处理器测试成功")

        configs = config_manager.get_data_configs()
        self.assertEqual(len(configs), 1)
        print(f"✓ 配置已保存: slave={configs[0].slave_id}, func={configs[0].func_code}, addr={configs[0].start_addr}")

    def test_virtual_device(self):
        print("\n=== 测试虚拟设备 ===")
        device_pool = DevicePool()

        device = device_pool.get_device(1)
        self.assertIsNotNone(device, "默认设备不存在")

        device.holding_registers._data[0] = 250
        device.holding_registers._data[1] = 600
        device.coils._data[0] = 1

        data = device.read_holding_registers(0, 2)
        self.assertEqual(len(data), 4)
        print(f"✓ 读取保持寄存器成功: {data.hex()}")

        coil_data = device.read_coils(0, 1)
        self.assertEqual(len(coil_data), 1)
        print(f"✓ 读取线圈成功: {coil_data.hex()}")

        device.write_single_register(10, 1234)
        self.assertEqual(device.get_register(10), 1234)
        print("✓ 写入寄存器成功")


if __name__ == '__main__':
    unittest.main(verbosity=2)