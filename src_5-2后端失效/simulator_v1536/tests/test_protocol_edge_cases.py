"""
Edge case and boundary tests for Protocol Handlers
"""

import unittest
import sys
import os
import struct

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator_v3.protocol.handler import ProtocolHandler, HandlerRegistry
from simulator_v3.protocol.heartbeat_handler import HeartbeatHandler
from simulator_v3.protocol.module_config_handler import ModuleConfigHandler
from simulator_v3.protocol.data_config_handler import DataConfigHandler, DataConfig
from simulator_v3.protocol.remote_write_handler import RemoteWriteHandler
from simulator_v3.core.config_manager import ConfigManager


class TestHeartbeatHandlerEdgeCases(unittest.TestCase):
    def setUp(self):
        self.handler = HeartbeatHandler()

    def test_empty_payload(self):
        result = self.handler.handle(bytes([]))
        self.assertIsNone(result)

    def test_single_byte_payload(self):
        result = self.handler.handle(bytes([0x00]))
        self.assertIsNotNone(result)

    def test_heartbeat_with_extra_data(self):
        result = self.handler.handle(bytes([0x00, 0x01, 0x02]))
        self.assertIsNotNone(result)

    def test_unknown_function_code(self):
        result = self.handler.handle(bytes([0xFF]))
        self.assertIsNone(result)

    def test_heartbeat_count_overflow(self):
        for _ in range(10000):
            self.handler.handle(bytes([0x00]))
        count = self.handler.get_heartbeat_count()
        self.assertEqual(count, 10000)


class TestModuleConfigHandlerEdgeCases(unittest.TestCase):
    def setUp(self):
        self.config_manager = ConfigManager()
        self.handler = ModuleConfigHandler(self.config_manager)

    def test_payload_too_short(self):
        result = self.handler._handle_download_config(bytes([0x02, 0x00]))
        self.assertIsNone(result)

    def test_config_payload_with_minimum_length(self):
        payload = bytes([0x02, 0x00, 0x00, 0x00])
        result = self.handler._handle_download_config(payload)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 0x02)

    def test_config_result_too_short(self):
        result = self.handler._handle_config_result(bytes([0x02]))
        self.assertIsNone(result)

    def test_create_module_config_upload_all_params(self):
        payload = self.handler.create_upload_config(0x01, 0x1234, 0x96)
        self.assertEqual(len(payload), 5)
        self.assertEqual(payload[0], 0x01)
        self.assertEqual(payload[1], 0x01)
        self.assertEqual(payload[2:4], struct.pack('>H', 0x1234))
        self.assertEqual(payload[4], 0x96)

    def test_module_config_result_format(self):
        payload = bytes([0x02, 0x00])
        self.assertEqual(len(payload), 2)
        self.assertEqual(payload[0], 0x02)
        self.assertEqual(payload[1], 0x00)


class TestDataConfigHandlerEdgeCases(unittest.TestCase):
    def setUp(self):
        self.config_manager = ConfigManager()
        self.handler = DataConfigHandler(self.config_manager)

    def test_payload_too_short(self):
        result = self.handler._handle_download_data_config(bytes([0x04, 0x00]))
        self.assertIsNone(result)

    def test_zero_group_count(self):
        payload = bytes([0x04, 0x00, 0x00])
        result = self.handler._handle_download_data_config(payload)
        self.assertIsNotNone(result)
        configs = self.config_manager.get_data_configs()
        self.assertEqual(len(configs), 0)

    def test_incomplete_group(self):
        payload = bytes([0x04, 0x00, 0x01, 0x01, 0x01, 0x00, 0x00])
        result = self.handler._handle_download_data_config(payload)
        self.assertIsNotNone(result)

    def test_multiple_groups_exactly(self):
        payload = bytes([
            0x04, 0x00, 0x03,
            0x01, 0x03, 0x00, 0x00, 0x00, 0x02,
            0x01, 0x04, 0x00, 0x10, 0x00, 0x04,
            0x01, 0x01, 0x00, 0x20, 0x00, 0x08
        ])
        result = self.handler._handle_download_data_config(payload)
        self.assertIsNotNone(result)
        configs = self.config_manager.get_data_configs()
        self.assertEqual(len(configs), 3)

    def test_config_result_format(self):
        result = self.handler._build_config_result(0x00)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], 0x04)
        self.assertEqual(result[1], 0x00)

    def test_config_result_error_format(self):
        result = self.handler._build_config_result(0x02)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], 0x04)
        self.assertEqual(result[1], 0x02)

    def test_create_data_config_upload(self):
        configs = [
            DataConfig(1, 3, 0, 10),
            DataConfig(1, 4, 16, 20)
        ]
        payload = self.handler.create_data_config_upload(configs)
        self.assertEqual(payload[0], 0x03)
        self.assertEqual(payload[1:3], struct.pack('>H', 2))


class TestRemoteWriteHandlerEdgeCases(unittest.TestCase):
    def setUp(self):
        self.handler = RemoteWriteHandler()

    def test_create_remote_write_all_types(self):
        for slave_id in [1, 247, 0]:
            for func_code in [1, 5, 15]:
                for addr in [0, 65535]:
                    payload = self.handler.create_remote_write(slave_id, func_code, addr, 1)
                    self.assertIsNotNone(payload)

    def test_remote_write_payload_too_short(self):
        result = self.handler._handle_remote_write(bytes([0x06, 0x00]))
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 7)
        self.assertEqual(result[6], 0x01)

    def test_remote_write_success(self):
        class MockModbusMaster:
            def write_single_register(self, slave_id, address, value):
                return True
            def write_single_coil(self, slave_id, address, value):
                return True

        handler = RemoteWriteHandler(modbus_master=MockModbusMaster())
        payload = bytes([0x06, 0x04, 0x00, 0x00, 0x00, 0x01, 0x00, 0x64])
        result = handler._handle_remote_write(payload)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 7)
        self.assertEqual(result[0], 0x06)
        self.assertEqual(result[1], 0x04)
        self.assertEqual(result[6], 0x00)

    def test_remote_write_failure_no_modbus_master(self):
        payload = bytes([0x06, 0x04, 0x00, 0x00, 0x00, 0x01, 0x00, 0x64])
        result = self.handler._handle_remote_write(payload)
        self.assertIsNotNone(result)
        self.assertEqual(result[6], 0x02)


class TestHandlerRegistryEdgeCases(unittest.TestCase):
    def setUp(self):
        self.registry = HandlerRegistry()

    def test_handle_empty_registry(self):
        result = self.registry.handle(bytes([0x00]))
        self.assertIsNone(result)

    def test_unregister_nonexistent(self):
        result = self.registry.unregister(0xFF)
        self.assertFalse(result)

    def test_multiple_handlers_same_code(self):
        handler1 = HeartbeatHandler()
        handler2 = HeartbeatHandler()
        self.registry.register(handler1)
        self.registry.register(handler2)
        result = self.registry.get(0x00)
        self.assertIs(result, handler2)

    def test_handler_chain_unknown_code(self):
        handler = HeartbeatHandler()
        self.registry.register(handler)
        result = self.registry.handle(bytes([0x05]))
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
