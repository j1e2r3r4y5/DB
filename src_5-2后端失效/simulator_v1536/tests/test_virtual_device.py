"""
Unit tests for VirtualDevice
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator_v3.data.virtual_device import VirtualDevice
from simulator_v3.data.device_pool import DevicePool


class TestVirtualDevice(unittest.TestCase):
    def setUp(self):
        self.device = VirtualDevice(slave_id=1)

    def test_initialization(self):
        self.assertEqual(self.device.slave_id, 1)
        self.assertIn(0, self.device.coils._data)
        self.assertEqual(self.device.coils._data[0], 1)

    def test_read_coils(self):
        self.device.coils._data[0] = 1
        self.device.coils._data[1] = 0

        data = self.device.read_coils(0, 2)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], 0b01)

    def test_read_holding_registers(self):
        self.device.holding_registers._data[0] = 250
        self.device.holding_registers._data[1] = 600

        data = self.device.read_holding_registers(0, 2)
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0], 0x00)
        self.assertEqual(data[1], 0xFA)
        self.assertEqual(data[2], 0x02)
        self.assertEqual(data[3], 0x58)

    def test_write_single_coil(self):
        self.device.write_single_coil(5, True)
        self.assertTrue(self.device.get_coil(5))

        self.device.write_single_coil(6, False)
        self.assertFalse(self.device.get_coil(6))

    def test_write_single_register(self):
        self.device.write_single_register(10, 1234)

        value = self.device.get_register(10)
        self.assertEqual(value, 1234)

    def test_simulate_temperature_change(self):
        new_val = self.device.simulate_temperature_change(base_value=250, variance=10)

        self.assertGreaterEqual(new_val, 240)
        self.assertLessEqual(new_val, 260)

    def test_toggle_switch(self):
        initial = self.device.get_coil(0)
        toggled = self.device.toggle_switch()

        self.assertNotEqual(initial, toggled)
        self.assertEqual(toggled, self.device.get_coil(0))


class TestDevicePool(unittest.TestCase):
    def setUp(self):
        self.pool = DevicePool()

    def test_default_device(self):
        self.assertTrue(self.pool.device_exists(1))
        device = self.pool.get_device(1)
        self.assertIsNotNone(device)
        self.assertEqual(device.slave_id, 1)

    def test_add_device(self):
        new_device = VirtualDevice(slave_id=2)
        result = self.pool.add_device(new_device)

        self.assertTrue(result)
        self.assertTrue(self.pool.device_exists(2))
        self.assertEqual(len(self.pool), 2)

    def test_remove_device(self):
        result = self.pool.remove_device(1)

        self.assertTrue(result)
        self.assertFalse(self.pool.device_exists(1))
        self.assertEqual(len(self.pool), 0)

    def test_get_handler(self):
        handler = self.pool.get_handler(1)
        self.assertIsNotNone(handler)


if __name__ == '__main__':
    unittest.main()