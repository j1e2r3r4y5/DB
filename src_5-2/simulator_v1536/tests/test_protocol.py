"""
Unit tests for Protocol Handlers
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from protocol.handler import ProtocolHandler, HandlerRegistry
from protocol.heartbeat_handler import HeartbeatHandler
from protocol.module_config_handler import ModuleConfigHandler
from protocol.data_config_handler import DataConfigHandler
from protocol.remote_write_handler import RemoteWriteHandler
from core.config_manager import ConfigManager


class TestHandlerRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = HandlerRegistry()

    def test_register_and_get(self):
        handler = HeartbeatHandler()
        self.registry.register(handler)

        retrieved = self.registry.get(0x00)
        self.assertIs(retrieved, handler)

    def test_unregister(self):
        handler = HeartbeatHandler()
        self.registry.register(handler)

        result = self.registry.unregister(0x00)
        self.assertTrue(result)

        retrieved = self.registry.get(0x00)
        self.assertIsNone(retrieved)

    def test_handle_with_registered_handler(self):
        handler = HeartbeatHandler()
        self.registry.register(handler)

        result = self.registry.handle(bytes([0x00]))
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 0x00)

    def test_handle_unknown_function_code(self):
        handler = HeartbeatHandler()
        self.registry.register(handler)

        result = self.registry.handle(bytes([0xFF]))
        self.assertIsNone(result)


class TestHeartbeatHandler(unittest.TestCase):
    def setUp(self):
        self.handler = HeartbeatHandler()

    def test_handle_heartbeat(self):
        payload = bytes([0x00])
        result = self.handler._handle_heartbeat(payload)

        self.assertIsNotNone(result)
        self.assertEqual(result[0], 0x00)

    def test_heartbeat_count(self):
        initial_count = self.handler.get_heartbeat_count()

        self.handler._handle_heartbeat(bytes([0x00]))
        self.assertEqual(self.handler.get_heartbeat_count(), initial_count + 1)

    def test_function_code(self):
        self.assertEqual(self.handler.get_function_code(), 0x00)


class TestModuleConfigHandler(unittest.TestCase):
    def setUp(self):
        self.config_manager = ConfigManager()
        self.handler = ModuleConfigHandler(self.config_manager)

    def test_handle_download_config(self):
        payload = bytes([0x02, 0x00, 0x00, 0x1E, 0x05])
        result = self.handler._handle_download_config(payload)

        self.assertIsNotNone(result)
        self.assertEqual(result[0], 0x02)

        config = self.config_manager.get_module_config()
        self.assertEqual(config.send_interval, 0x001E)

    def test_create_module_config_upload(self):
        payload = self.handler.create_upload_config(0x00, 0x001E, 0x05)

        self.assertEqual(payload[0], 0x01)
        self.assertEqual(payload[1], 0x00)
        self.assertEqual(payload[2], 0x00)
        self.assertEqual(payload[3], 0x1E)
        self.assertEqual(payload[4], 0x05)


class TestDataConfigHandler(unittest.TestCase):
    def setUp(self):
        self.config_manager = ConfigManager()
        self.handler = DataConfigHandler(self.config_manager)

    def test_handle_download_data_config(self):
        payload = bytes([0x04, 0x00, 0x01, 0x01, 0x04, 0x00, 0x00, 0x00, 0x02])
        result = self.handler._handle_download_data_config(payload)

        self.assertIsNotNone(result)
        self.assertEqual(result[0], 0x04)

        configs = self.config_manager.get_data_configs()
        self.assertEqual(len(configs), 1)
        self.assertEqual(configs[0].slave_id, 1)
        self.assertEqual(configs[0].func_code, 3)
        self.assertEqual(configs[0].start_addr, 0)
        self.assertEqual(configs[0].quantity, 2)

    def test_multiple_data_config_groups(self):
        payload = bytes([
            0x04,
            0x00, 0x02,
            0x01, 0x01, 0x00, 0x00, 0x00, 0x01,
            0x01, 0x03, 0x00, 0x00, 0x00, 0x02
        ])

        result = self.handler._handle_download_data_config(payload)
        self.assertIsNotNone(result)

        configs = self.config_manager.get_data_configs()
        self.assertEqual(len(configs), 2)


class TestRemoteWriteHandler(unittest.TestCase):
    def setUp(self):
        self.handler = RemoteWriteHandler()

    def test_create_remote_write(self):
        payload = self.handler.create_remote_write(1, 4, 0, 250)
        self.assertEqual(payload[0], 0x06)
        self.assertEqual(payload[1], 0x04)

    def test_function_code(self):
        self.assertEqual(self.handler.get_function_code(), 0x06)


if __name__ == '__main__':
    unittest.main()