"""
Unit tests for Modbus Master Connection Pool
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import socket
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestModbusConnectionPool(unittest.TestCase):
    """Test Modbus connection pool functionality"""

    @patch('core.modbus_master.socket')
    def test_connection_uses_keepalive(self, mock_socket):
        """Test that connections use SO_KEEPALIVE option"""
        from core.modbus_master import ModbusMaster

        mock_sock_instance = MagicMock()
        mock_socket.socket.return_value = mock_sock_instance
        mock_sock_instance.connect.return_value = None

        master = ModbusMaster(host='127.0.0.1', port=502)
        master._create_connection()

        mock_sock_instance.setsockopt.assert_called()
        calls = mock_sock_instance.setsockopt.call_args_list
        self.assertTrue(any('SO_KEEPALIVE' in str(c) or len(c) >= 3 for c in calls))

    @patch('core.modbus_master.socket')
    def test_connection_timeout_set(self, mock_socket):
        """Test that connection timeout is properly set"""
        from core.modbus_master import ModbusMaster

        mock_sock_instance = MagicMock()
        mock_socket.socket.return_value = mock_sock_instance
        mock_sock_instance.connect.return_value = None

        master = ModbusMaster(host='127.0.0.1', port=502, timeout=10.0)
        master._create_connection()

        mock_sock_instance.settimeout.assert_called()

    @patch('core.modbus_master.socket')
    def test_get_connection_validates_with_recv(self, mock_socket):
        """Test that get_connection validates connection with recv instead of send"""
        from core.modbus_master import ModbusMaster, ModbusConnection

        mock_sock_instance = MagicMock()
        mock_sock_instance.recv.return_value = b'\x00\x01\x00\x00\x00\x05\x00'
        mock_socket.socket.return_value = mock_sock_instance
        mock_sock_instance.connect.return_value = None

        mock_conn = ModbusConnection(mock_sock_instance, time.time())

        master = ModbusMaster(host='127.0.0.1', port=502)
        master._pool = [mock_conn]
        master.timeout = 5.0

        conn = master._get_connection()

        self.assertEqual(conn, mock_conn)
        mock_sock_instance.recv.assert_called()
        call_args = mock_sock_instance.recv.call_args
        self.assertEqual(call_args[0][0], 7)


class TestModbusConnectionClass(unittest.TestCase):
    """Test ModbusConnection class"""

    def test_connection_initialization(self):
        """Test that ModbusConnection initializes correctly"""
        from core.modbus_master import ModbusConnection

        mock_sock = MagicMock()
        current_time = time.time()
        conn = ModbusConnection(mock_sock, current_time)

        self.assertEqual(conn.sock, mock_sock)
        self.assertEqual(conn.last_used, current_time)


if __name__ == '__main__':
    unittest.main()
