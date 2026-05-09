"""
Integration tests for DTU+Modbus Simulator
"""

import unittest
import sys
import os
import time
import struct

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator_v3.core.config_manager import ConfigManager
from simulator_v3.data.device_pool import DevicePool
from simulator_v3.data.virtual_device import VirtualDevice
from simulator_v3.data.data_scheduler import DataScheduler, DataCollectionJob
from simulator_v3.protocol.handler import HandlerRegistry
from simulator_v3.protocol.heartbeat_handler import HeartbeatHandler
from simulator_v3.protocol.data_config_handler import DataConfigHandler
from simulator_v3.modbus.tcp_server import ModbusTCPServer
from simulator_v3.modbus.request_handler import ModbusRequestHandler


class TestIntegrationDataFlow(unittest.TestCase):
    def setUp(self):
        self.config_manager = ConfigManager()
        self.device_pool = DevicePool()
        self.device = self.device_pool.get_device(1)

    def test_data_config_update_flow(self):
        data_config_handler = DataConfigHandler(self.config_manager)

        payload = bytes([
            0x04,
            0x00, 0x01,
            0x01, 0x03, 0x00, 0x00, 0x00, 0x02
        ])

        result = data_config_handler._handle_download_data_config(payload)

        self.assertIsNotNone(result)
        self.assertEqual(result[0], 0x04)

        configs = self.config_manager.get_data_configs()
        self.assertEqual(len(configs), 1)

        config = configs[0]
        self.assertEqual(config.slave_id, 1)
        self.assertEqual(config.func_code, 3)
        self.assertEqual(config.start_addr, 0)
        self.assertEqual(config.quantity, 2)

    def test_handler_to_device_flow(self):
        device = VirtualDevice(slave_id=10)
        self.device_pool.add_device(device)

        device.holding_registers._data[0] = 250
        device.holding_registers._data[1] = 600

        handler = ModbusRequestHandler(device)

        request = struct.pack('>HHH', 1, 0, 7)
        request += bytes([10])
        request += bytes([0x03])
        request += struct.pack('>HH', 0, 2)

        response = handler.handle(request)

        self.assertIsNotNone(response)
        self.assertEqual(response[7], 0x03)
        self.assertEqual(response[8], 4)


class TestIntegrationProtocolFlow(unittest.TestCase):
    def setUp(self):
        self.config_manager = ConfigManager()
        self.handler_registry = HandlerRegistry()

        self.heartbeat_handler = HeartbeatHandler()
        self.data_config_handler = DataConfigHandler(self.config_manager)

        self.handler_registry.register(self.heartbeat_handler)
        self.handler_registry.register(self.data_config_handler)

    def test_downlink_to_uplink_flow(self):
        payload = bytes([0x04, 0x00, 0x01, 0x01, 0x03, 0x00, 0x00, 0x00, 0x02])

        response = self.handler_registry.handle(payload)

        self.assertIsNotNone(response)
        self.assertEqual(response[0], 0x04)

        configs = self.config_manager.get_data_configs()
        self.assertEqual(len(configs), 1)

    def test_heartbeat_flow(self):
        payload = bytes([0x00])

        response = self.handler_registry.handle(payload)

        self.assertIsNotNone(response)
        self.assertEqual(response[0], 0x00)


class TestIntegrationModbusServer(unittest.TestCase):
    def setUp(self):
        self.device_pool = DevicePool()
        self.tcp_server = ModbusTCPServer(host='127.0.0.1', port=5502)

        for slave_id in self.device_pool.get_all_slave_ids():
            device = self.device_pool.get_device(slave_id)
            if device:
                handler = ModbusRequestHandler(device)
                self.tcp_server.set_device_handler(slave_id, handler)

    def test_server_lifecycle(self):
        self.tcp_server.start()
        self.assertTrue(self.tcp_server.is_running())

        time.sleep(0.5)

        self.tcp_server.stop()
        self.assertFalse(self.tcp_server.is_running())


class TestIntegrationDataScheduler(unittest.TestCase):
    def setUp(self):
        self.config_manager = ConfigManager()
        self.scheduler = DataScheduler()

    def test_add_and_remove_job(self):
        job = DataCollectionJob(
            job_id='test_job',
            slave_id=1,
            func_code=3,
            start_addr=0,
            quantity=2,
            interval=10
        )

        result = self.scheduler.add_job(job)
        self.assertTrue(result)

        retrieved = self.scheduler.get_job('test_job')
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.slave_id, 1)

        result = self.scheduler.remove_job('test_job')
        self.assertTrue(result)

        retrieved = self.scheduler.get_job('test_job')
        self.assertIsNone(retrieved)

    def test_scheduler_start_stop(self):
        self.scheduler.start()
        self.assertTrue(self.scheduler.is_running)

        self.scheduler.stop()
        self.assertFalse(self.scheduler.is_running)


if __name__ == '__main__':
    unittest.main()