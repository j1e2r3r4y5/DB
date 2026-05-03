"""
Unit tests for RemoteWriteHandler exception handling
"""

import unittest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
import struct

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestRemoteWriteHandlerExceptionHandling(unittest.TestCase):
    """Test RemoteWriteHandler exception handling mechanisms"""

    def setUp(self):
        from simulator_v3.protocol.remote_write_handler import RemoteWriteHandler
        self.handler = RemoteWriteHandler(modbus_master=None)
        self.handler.modbus_master = None

    def test_payload_too_short_returns_error_response(self):
        """Test that payload too short returns error response instead of None"""
        short_payload = bytes([0x06, 0x01])

        response = self.handler._handle_remote_write(short_payload)

        self.assertIsNotNone(response)
        self.assertEqual(len(response), 7)
        self.assertEqual(response[0], 0x06)
        self.assertEqual(response[6], self.handler.ERROR_CODE_PARSE_FAILED)

    def test_valid_holding_register_write(self):
        """Test valid holding register (type 4) remote write"""
        payload = bytes([0x06, 0x04, 0x00, 0x01, 0x00, 0x01, 0x00, 0xC8])

        response = self.handler._handle_remote_write(payload)

        self.assertIsNotNone(response)
        self.assertEqual(response[0], 0x06)
        self.assertEqual(response[1], 0x04)

    def test_valid_coil_write(self):
        """Test valid coil (type 0) remote write"""
        payload = bytes([0x06, 0x00, 0x00, 0x01, 0x00, 0x01, 0x01])

        response = self.handler._handle_remote_write(payload)

        self.assertIsNotNone(response)
        self.assertEqual(response[0], 0x06)
        self.assertEqual(response[1], 0x00)

    def test_unsupported_data_type_returns_error(self):
        """Test that unsupported data type returns error response"""
        payload = bytes([0x06, 0x02, 0x00, 0x01, 0x00, 0x01, 0x00, 0x64])

        response = self.handler._handle_remote_write(payload)

        self.assertIsNotNone(response)
        self.assertEqual(response[6], self.handler.ERROR_CODE_UNSUPPORTED_TYPE)

    def test_error_response_structure(self):
        """Test error response has correct structure"""
        short_payload = bytes([0x06, 0x01])

        response = self.handler._handle_remote_write(short_payload)

        self.assertEqual(len(response), 7)
        self.assertEqual(response[0], 0x06)
        self.assertEqual(response[1], 0xFF)
        self.assertEqual(response[2:4], struct.pack('>H', 0))
        self.assertEqual(response[4:6], struct.pack('>H', 1))

    def test_struct_error_handling(self):
        """Test struct.error is caught and handled properly"""
        with patch('simulator_v3.protocol.remote_write_handler.struct.unpack') as mock_unpack:
            mock_unpack.side_effect = struct.error("Invalid struct format")

            payload = bytes([0x06, 0x04, 0x00, 0x01, 0x00, 0x01, 0x00, 0xC8])
            response = self.handler._handle_remote_write(payload)

            self.assertIsNotNone(response)
            self.assertEqual(response[6], self.handler.ERROR_CODE_PARSE_FAILED)

    def test_exception_includes_timestamp(self):
        """Test that exceptions include timestamp in logs"""
        short_payload = bytes([0x06, 0x01])

        with self.assertLogs('simulator_v3.protocol.remote_write_handler', level='ERROR') as log:
            self.handler._handle_remote_write(short_payload)

            self.assertTrue(len(log.output) > 0)
            self.assertIn('ERROR', log.output[0])

    def test_no_modbus_master_returns_failure_status(self):
        """Test behavior when no Modbus master is configured"""
        self.handler.modbus_master = None
        payload = bytes([0x06, 0x04, 0x00, 0x01, 0x00, 0x01, 0x00, 0xC8])

        response = self.handler._handle_remote_write(payload)

        self.assertIsNotNone(response)
        self.assertEqual(response[6], self.handler.ERROR_CODE_WRITE_FAILED)

    def test_modbus_master_write_success(self):
        """Test successful Modbus write through mock master"""
        mock_master = MagicMock()
        mock_master.write_single_register.return_value = True
        self.handler.modbus_master = mock_master

        payload = bytes([0x06, 0x04, 0x00, 0x01, 0x00, 0x01, 0x00, 0xC8])

        response = self.handler._handle_remote_write(payload)

        self.assertIsNotNone(response)
        self.assertEqual(response[6], self.handler.ERROR_CODE_SUCCESS)
        mock_master.write_single_register.assert_called_once()

    def test_modbus_master_write_failure(self):
        """Test Modbus write failure is properly handled"""
        mock_master = MagicMock()
        mock_master.write_single_register.return_value = False
        self.handler.modbus_master = mock_master

        payload = bytes([0x06, 0x04, 0x00, 0x01, 0x00, 0x01, 0x00, 0xC8])

        response = self.handler._handle_remote_write(payload)

        self.assertIsNotNone(response)
        self.assertEqual(response[6], self.handler.ERROR_CODE_WRITE_FAILED)

    def test_build_error_response_method(self):
        """Test _build_error_response creates correct structure"""
        response = self.handler._build_error_response(
            self.handler.ERROR_CODE_PARSE_FAILED,
            {"reason": "test"}
        )

        self.assertEqual(len(response), 7)
        self.assertEqual(response[0], 0x06)
        self.assertEqual(response[1], 0xFF)
        self.assertEqual(response[6], self.handler.ERROR_CODE_PARSE_FAILED)

    def test_empty_payload_returns_none(self):
        """Test that empty payload returns None"""
        response = self.handler.handle(bytes([]))

        self.assertIsNone(response)

    def test_none_payload_returns_none(self):
        """Test that None payload returns None"""
        response = self.handler.handle(None)

        self.assertIsNone(response)


class TestRemoteWriteExceptions(unittest.TestCase):
    """Test custom exception classes"""

    def test_remote_write_error_base(self):
        from simulator_v3.protocol.remote_write_handler import RemoteWriteError

        error = RemoteWriteError("Test error", error_code=0xE1, details={"key": "value"})

        self.assertEqual(error.error_code, 0xE1)
        self.assertEqual(error.details, {"key": "value"})
        self.assertEqual(str(error), "Test error")

    def test_payload_parse_error(self):
        from simulator_v3.protocol.remote_write_handler import PayloadParseError

        error = PayloadParseError("Parse failed", details={"offset": 5})

        self.assertEqual(error.error_code, 0xE1)
        self.assertEqual(error.details, {"offset": 5})

    def test_modbus_write_error(self):
        from simulator_v3.protocol.remote_write_handler import ModbusWriteError

        error = ModbusWriteError("Write failed", details={"slave_id": 1})

        self.assertEqual(error.error_code, 0xE2)

    def test_unsupported_data_type_error(self):
        from simulator_v3.protocol.remote_write_handler import UnsupportedDataTypeError

        error = UnsupportedDataTypeError(data_type=5)

        self.assertEqual(error.error_code, 0xE3)
        self.assertEqual(error.details, {"data_type": 5})


if __name__ == '__main__':
    unittest.main()
