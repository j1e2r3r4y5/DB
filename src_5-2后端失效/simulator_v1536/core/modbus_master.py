"""
Modbus Master - Manages Modbus connections and read/write operations
"""

import logging
import random
import socket
import struct
import threading
import time
from typing import Optional, List, Tuple

from config import config


logger = logging.getLogger(__name__)


class ModbusConnection:
    """Modbus connection wrapper"""

    def __init__(self, sock: socket.socket, last_used: float):
        self.sock = sock
        self.last_used = last_used


class ModbusMaster:
    """
    Modbus Master - Manages Modbus TCP connections

    Features:
    - Connection pool for reuse
    - Automatic connection recovery
    - Thread-safe operations
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        pool_size: int = None,
        timeout: float = None,
        lazy_init: bool = True,
    ):
        self.host = host or config.MODBUS_HOST
        self.port = port or config.MODBUS_PORT
        self.pool_size = pool_size or config.MODBUS_POOL_SIZE
        self.timeout = timeout or config.MODBUS_TIMEOUT
        self.lazy_init = lazy_init

        self._pool: List[ModbusConnection] = []
        self._lock = threading.Lock()
        self._initialized = False

        if not self.lazy_init:
            self._initialize_pool()

        logger.info(f"ModbusMaster initialized: {self.host}:{self.port}, pool_size={self.pool_size}")

    def _initialize_pool(self):
        """Initialize connection pool"""
        with self._lock:
            for _ in range(self.pool_size):
                conn = self._create_connection()
                if conn:
                    self._pool.append(conn)

    def _create_connection(self) -> Optional[ModbusConnection]:
        """Create new Modbus connection"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.connect((self.host, self.port))
            conn = ModbusConnection(sock, time.time())
            logger.info(f"Created new Modbus connection to {self.host}:{self.port}")
            return conn
        except Exception as e:
            logger.error(f"Failed to create Modbus connection: {e}")
            return None

    def _get_connection(self) -> Optional[ModbusConnection]:
        """Get a connection from pool"""
        with self._lock:
            if self.lazy_init and not self._initialized:
                self._initialized = True
                for i in range(self.pool_size):
                    conn = self._create_connection()
                    if conn:
                        self._pool.append(conn)

            current_time = time.time()

            for conn in self._pool:
                try:
                    conn.sock.settimeout(0.5)
                    header = conn.sock.recv(7, socket.MSG_PEEK)
                    conn.last_used = current_time
                    return conn
                except:
                    continue

            if len(self._pool) < self.pool_size:
                conn = self._create_connection()
                if conn:
                    self._pool.append(conn)
                    return conn

            oldest_conn = min(self._pool, key=lambda c: c.last_used)
            oldest_conn.last_used = current_time
            return oldest_conn

    def _return_connection(self, conn: ModbusConnection):
        """Return connection to pool"""
        with self._lock:
            conn.last_used = time.time()

    def read(
        self,
        slave_id: int,
        func_code: int,
        start_addr: int,
        quantity: int,
    ) -> Optional[bytes]:
        """
        Read Modbus data

        Args:
            slave_id: Modbus slave ID (1-247)
            func_code: Function code (0x01/0x02/0x03/0x04)
            start_addr: Starting address (0-based)
            quantity: Number of items to read

        Returns:
            bytes: Data read, or None on failure
        """
        conn = self._get_connection()
        if not conn:
            logger.error("No available Modbus connection")
            return None

        try:
            transaction_id = random.randint(1, 65535)
            protocol_id = 0
            unit_id = slave_id

            request = struct.pack('>HHH', transaction_id, protocol_id, 6)
            request += bytes([func_code])
            request += struct.pack('>HH', start_addr, quantity)

            conn.sock.send(request)

            response = conn.sock.recv(1024)

            if len(response) < 9:
                logger.warning(f"Invalid Modbus response: too short ({len(response)} bytes)")
                return None

            resp_func_code = response[7]
            if resp_func_code != func_code:
                logger.warning(f"Function code mismatch: expected {func_code}, got {resp_func_code}")
                return None

            byte_count = response[8]
            data = response[9:9 + byte_count]

            logger.debug(f"Modbus read success: slave={slave_id}, func={func_code}, addr={start_addr}, qty={quantity}, data={data.hex()}")
            return data

        except socket.timeout:
            logger.warning(f"Modbus read timeout: slave={slave_id}, func={func_code}, addr={start_addr}")
            self._mark_connection_dead(conn)
            return None
        except Exception as e:
            logger.error(f"Modbus read error: {e}")
            self._mark_connection_dead(conn)
            return None
        finally:
            self._return_connection(conn)

    def write_single(
        self,
        slave_id: int,
        func_code: int,
        addr: int,
        value: int,
    ) -> bool:
        """
        Write single register/coil

        Args:
            slave_id: Modbus slave ID
            func_code: Function code (0x05 for coil, 0x06 for register)
            addr: Address to write
            value: Value to write

        Returns:
            bool: True on success
        """
        conn = self._get_connection()
        if not conn:
            logger.error("No available Modbus connection")
            return False

        try:
            transaction_id = random.randint(1, 65535)
            protocol_id = 0

            request = struct.pack('>HHH', transaction_id, protocol_id, 6)
            request += bytes([func_code])
            request += struct.pack('>HH', addr, value)

            conn.sock.send(request)

            response = conn.sock.recv(1024)

            if len(response) < 9:
                logger.warning(f"Invalid Modbus response")
                return False

            resp_func_code = response[7]
            if resp_func_code != func_code:
                logger.warning(f"Function code mismatch")
                return False

            logger.debug(f"Modbus write success: slave={slave_id}, func={func_code}, addr={addr}, value={value}")
            return True

        except Exception as e:
            logger.error(f"Modbus write error: {e}")
            self._mark_connection_dead(conn)
            return False
        finally:
            self._return_connection(conn)

    def _mark_connection_dead(self, conn: ModbusConnection):
        """Mark connection as dead and remove from pool"""
        with self._lock:
            if conn in self._pool:
                self._pool.remove(conn)
                try:
                    conn.sock.close()
                except:
                    pass
                logger.debug("Removed dead connection from pool")

    def write_single_coil(self, slave_id: int, addr: int, value: bool) -> bool:
        """Write single coil"""
        coil_value = 0xFF00 if value else 0x0000
        return self.write_single(slave_id, 0x05, addr, coil_value)

    def write_single_register(self, slave_id: int, addr: int, value: int) -> bool:
        """Write single holding register"""
        return self.write_single(slave_id, 0x06, addr, value)

    def close_all(self):
        """Close all connections"""
        with self._lock:
            for conn in self._pool:
                try:
                    conn.sock.close()
                except:
                    pass
            self._pool.clear()
        logger.info("All Modbus connections closed")
