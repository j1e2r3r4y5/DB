"""
Unit tests for Modbus areas
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modbus.areas import CoilArea, DiscreteInputArea, HoldingRegisterArea, InputRegisterArea


class TestCoilArea(unittest.TestCase):
    def setUp(self):
        self.coils = CoilArea()

    def test_read_empty(self):
        data = self.coils.read(0, 8)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0], 0)

    def test_read_with_data(self):
        self.coils._data[0] = 1
        self.coils._data[3] = 1

        data = self.coils.read(0, 8)
        self.assertEqual(data[0], 0b00001001)

    def test_write(self):
        self.coils.write(0, 8, bytes([0b10101010]))

        self.assertEqual(self.coils._data.get(0), 0)
        self.assertEqual(self.coils._data.get(1), 1)
        self.assertEqual(self.coils._data.get(2), 0)
        self.assertEqual(self.coils._data.get(3), 1)


class TestHoldingRegisterArea(unittest.TestCase):
    def setUp(self):
        self.registers = HoldingRegisterArea()

    def test_read_empty(self):
        data = self.registers.read(0, 2)
        self.assertEqual(len(data), 4)
        self.assertEqual(data, bytes([0, 0, 0, 0]))

    def test_read_with_data(self):
        self.registers._data[0] = 250
        self.registers._data[1] = 600

        data = self.registers.read(0, 2)
        self.assertEqual(len(data), 4)
        self.assertEqual(data[0], 0)
        self.assertEqual(data[1], 250)
        self.assertEqual(data[2], 2)
        self.assertEqual(data[3], 88)

    def test_write(self):
        self.registers.write(0, 2, bytes([0x00, 0xFA, 0x02, 0x58]))

        self.assertEqual(self.registers._data.get(0), 250)
        self.assertEqual(self.registers._data.get(1), 600)

    def test_value_overflow(self):
        self.registers._data[0] = 70000

        data = self.registers.read(0, 1)
        self.assertEqual(data[0], 0x11)
        self.assertEqual(data[1], 0x70)


class TestInputRegisterArea(unittest.TestCase):
    def setUp(self):
        self.registers = InputRegisterArea()

    def test_read_empty(self):
        data = self.registers.read(0, 1)
        self.assertEqual(len(data), 2)
        self.assertEqual(data, bytes([0, 0]))


if __name__ == '__main__':
    unittest.main()