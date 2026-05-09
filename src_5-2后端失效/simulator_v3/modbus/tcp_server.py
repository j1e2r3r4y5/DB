import socket
import threading
import logging
from typing import Optional, Dict
import random

from .request_handler import ModbusRequestHandler
from .response_builder import ModbusResponseBuilder

logger = logging.getLogger(__name__)


class ModbusTCPServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 502):
        self.host = host
        self.port = port
        self._server_socket: Optional[socket.socket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._clients: Dict[str, socket.socket] = {}
        self._client_lock = threading.Lock()
        self._device_handlers: Dict[int, ModbusRequestHandler] = {}
        self._default_handler: Optional[ModbusRequestHandler] = None

    def set_device_handler(self, slave_id: int, handler: ModbusRequestHandler):
        self._device_handlers[slave_id] = handler
        logger.info(f"Registered device handler for slave_id={slave_id}")

    def set_default_handler(self, handler: ModbusRequestHandler):
        self._default_handler = handler
        logger.info("Set default device handler")

    def start(self):
        if self._running:
            logger.warning("Server already running")
            return

        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.settimeout(1.0)

        try:
            self._server_socket.bind((self.host, self.port))
            self._server_socket.listen(5)
            self._running = True

            self._thread = threading.Thread(target=self._accept_loop, daemon=True)
            self._thread.start()

            logger.info(f"Modbus TCP server started on {self.host}:{self.port}")
        except OSError as e:
            logger.error(f"Failed to start server: {e}")
            self._server_socket = None
            raise

    def stop(self):
        self._running = False

        with self._client_lock:
            for client_id, client in self._clients.items():
                try:
                    client.close()
                except Exception:
                    pass
            self._clients.clear()

        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
            self._server_socket = None

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        logger.info("Modbus TCP server stopped")

    def _accept_loop(self):
        while self._running:
            try:
                client_socket, addr = self._server_socket.accept()
                client_id = f"{addr[0]}:{addr[1]}"
                logger.info(f"Client connected: {client_id}")

                with self._client_lock:
                    self._clients[client_id] = client_socket

                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr, client_id),
                    daemon=True
                )
                client_thread.start()

            except socket.timeout:
                continue
            except OSError as e:
                if self._running:
                    logger.error(f"Accept loop error: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error in accept loop: {e}")
                break

    def _handle_client(self, client_socket: socket.socket, addr: tuple, client_id: str):
        client_socket.settimeout(30.0)
        buffer = bytearray()

        try:
            while self._running:
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break

                    buffer.extend(data)
                    self._process_buffer(client_socket, buffer, client_id)

                except socket.timeout:
                    break
                except ConnectionResetError:
                    break
                except OSError as e:
                    logger.error(f"Socket error: {e}")
                    break

        except Exception as e:
            logger.error(f"Client handler error: {e}")
        finally:
            with self._client_lock:
                if client_id in self._clients:
                    del self._clients[client_id]
            try:
                client_socket.close()
            except Exception:
                pass
            logger.info(f"Client disconnected: {client_id}")

    def _process_buffer(self, client_socket: socket.socket, buffer: bytearray, client_id: str):
        offset = 0
        while len(buffer) - offset >= 9:
            transaction_id = int.from_bytes(buffer[offset:offset+2], 'big')
            protocol_id = int.from_bytes(buffer[offset+2:offset+4], 'big')
            length = int.from_bytes(buffer[offset+4:offset+6], 'big')

            total_length = 6 + length
            if len(buffer) - offset < total_length:
                break

            if length < 2:
                offset += 1
                continue

            unit_id = buffer[offset + 6]
            func_code = buffer[offset + 7]

            device = self._find_device(unit_id)
            if not device:
                offset += total_length
                continue

            request_data = bytes(buffer[offset:offset + total_length])
            response = device.handle(request_data)

            if response:
                try:
                    client_socket.sendall(response)
                except Exception as e:
                    logger.error(f"Failed to send response: {e}")
                    return

            offset += total_length

        if offset > 0:
            del buffer[:offset]

    def _find_device(self, slave_id: int) -> Optional[ModbusRequestHandler]:
        return self._device_handlers.get(slave_id, self._default_handler)

    def is_running(self) -> bool:
        return self._running

    @property
    def server_socket(self) -> Optional[socket.socket]:
        return self._server_socket