#!/usr/bin/env python3
"""
4G DTU Simulator - 重构版本
稳定、高效、支持自动重连的DTU模拟器
"""

import socket
import struct
import threading
import time
import random
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from queue import Queue, Empty
from enum import Enum
import paho.mqtt.client as mqtt


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


FUNCTION_CODES = {
    'HEARTBEAT': 0x00,
    'MODULE_CONFIG_QUERY': 0x01,
    'MODULE_CONFIG_UPLOAD': 0x01,
    'DOWNLOAD_MODULE_CONFIG': 0x02,
    'MODULE_CONFIG_RESULT': 0x02,
    'DATA_CONFIG_QUERY': 0x03,
    'DATA_CONFIG_UPLOAD': 0x03,
    'DOWNLOAD_DATA_CONFIG': 0x04,
    'CONFIG_RESULT': 0x04,
    'DATA_UPLOAD': 0x05,
    'REMOTE_WRITE': 0x06,
}

REGION_TO_FUNC_CODE = {0: 0x01, 1: 0x02, 3: 0x04, 4: 0x03}


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class DataConfig:
    slave_id: int
    func_code: int
    start_addr: int
    quantity: int


@dataclass
class ModbusPooledConnection:
    sock: socket.socket
    last_used: float
    slave_id: int


class ModbusConnectionPool:
    def __init__(self, host: str, port: int, pool_size: int = 3, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.pool_size = pool_size
        self.timeout = timeout
        self._pool: List[ModbusPooledConnection] = []
        self._lock = threading.Lock()
        self._create_pool()

    def _create_pool(self):
        for _ in range(self.pool_size):
            conn = self._create_connection()
            if conn:
                self._pool.append(conn)

    def _create_connection(self) -> Optional[ModbusPooledConnection]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            return ModbusPooledConnection(sock=sock, last_used=time.time(), slave_id=0)
        except Exception as e:
            logger.error(f"Failed to create Modbus connection: {e}")
            return None

    def get_connection(self, slave_id: int) -> Optional[ModbusPooledConnection]:
        with self._lock:
            current_time = time.time()
            for conn in self._pool:
                if current_time - conn.last_used > 30:
                    try:
                        conn.sock.close()
                    except:
                        pass
                    new_conn = self._create_connection()
                    if new_conn:
                        conn.sock = new_conn.sock
                        conn.last_used = current_time
                        conn.slave_id = slave_id
                        return conn
            if self._pool:
                conn = self._pool[0]
                conn.last_used = current_time
                return conn
            return None

    def return_connection(self, conn: ModbusPooledConnection):
        with self._lock:
            conn.last_used = time.time()

    def read_modbus(self, slave_id: int, func_code: int, start_addr: int, quantity: int) -> Optional[bytes]:
        conn = self.get_connection(slave_id)
        if not conn:
            logger.warning(f"No available Modbus connection for slave {slave_id}")
            return None

        try:
            transaction_id = random.randint(1, 65535)
            request = struct.pack('>HHH', transaction_id, 0, 6)
            request += bytes([slave_id, func_code])
            request += struct.pack('>HH', start_addr, quantity)

            conn.sock.send(request)
            response = conn.sock.recv(1024)

            if len(response) >= 9 and response[7] == func_code:
                byte_count = response[8]
                return response[9:9 + byte_count]

        except socket.timeout:
            logger.warning(f"Modbus read timeout for slave {slave_id}")
            self._mark_connection_dead(conn)
        except Exception as e:
            logger.error(f"Modbus read error: {e}")
            self._mark_connection_dead(conn)
        finally:
            self.return_connection(conn)

        return None

    def _mark_connection_dead(self, conn: ModbusPooledConnection):
        with self._lock:
            if conn in self._pool:
                self._pool.remove(conn)
                try:
                    conn.sock.close()
                except:
                    pass
                new_conn = self._create_connection()
                if new_conn:
                    self._pool.append(new_conn)

    def close_all(self):
        with self._lock:
            for conn in self._pool:
                try:
                    conn.sock.close()
                except:
                    pass
            self._pool.clear()


class DTUSimulatorV2:
    def __init__(
        self,
        mqtt_broker: str,
        mqtt_port: int,
        device_serial: str,
        modbus_host: str,
        modbus_port: int,
        up_topic: str,
        down_topic: str,
        heartbeat_interval: int = 30,
        poll_interval: int = 10
    ):
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.device_serial = device_serial
        self.modbus_host = modbus_host
        self.modbus_port = modbus_port
        self.up_topic = up_topic
        self.down_topic = down_topic
        self.heartbeat_interval = heartbeat_interval
        self.poll_interval = poll_interval

        self.mqtt_client: Optional[mqtt.Client] = None
        self.modbus_pool: Optional[ModbusConnectionPool] = None

        self.running = False
        self.mqtt_state = ConnectionState.DISCONNECTED
        self.reconnect_delay = 5
        self.max_reconnect_delay = 60

        self.module_config = {
            'send_mode': 0x00,
            'config_data': 0x001E,  # 30秒默认间隔
            'baud': 0x05,
            'send_interval': 30,  # 发送间隔（秒）
        }

        self.data_configs: List[DataConfig] = []
        self._data_configs_lock = threading.Lock()

        self._mqtt_lock = threading.Lock()
        self._reconnect_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self):
        self.running = True
        self._stop_event.clear()

        self.modbus_pool = ModbusConnectionPool(self.modbus_host, self.modbus_port)

        self._init_mqtt()
        self._start_threads()

        logger.info(f"DTU Simulator V2 started for device {self.device_serial}")

    def stop(self):
        logger.info("Stopping DTU Simulator V2...")
        self.running = False
        self._stop_event.set()

        if self.modbus_pool:
            self.modbus_pool.close_all()

        if self.mqtt_client:
            try:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            except:
                pass

        logger.info("DTU Simulator V2 stopped")

    def _init_mqtt(self):
        client_id = f"dtu_sim_{self.device_serial}_{int(time.time())}"
        self.mqtt_client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)

        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_disconnect = self._on_disconnect
        self.mqtt_client.on_message = self._on_message
        self.mqtt_client.on_subscribe = self._on_subscribe

        self.mqtt_client.keepalive = 60
        self.mqtt_client.reconnect_delay_set(min_delay=5, max_delay=60)

        self._do_mqtt_connect()

    def _do_mqtt_connect(self):
        self.mqtt_state = ConnectionState.CONNECTING
        try:
            logger.info(f"Connecting to MQTT broker {self.mqtt_broker}:{self.mqtt_port}")
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, keepalive=60)
            self.mqtt_client.loop_start()
        except Exception as e:
            logger.error(f"MQTT connection failed: {e}")
            self.mqtt_state = ConnectionState.ERROR

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("MQTT connected successfully")
            self.mqtt_state = ConnectionState.CONNECTED
            self.reconnect_delay = 5

            client.subscribe(self.down_topic, qos=2)
            logger.info(f"Subscribed to {self.down_topic}")
        else:
            reason_codes = {
                1: "Protocol version mismatch",
                2: "Invalid client identifier",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized"
            }
            logger.error(f"MQTT connection failed with code {rc}: {reason_codes.get(rc, 'Unknown')}")
            self.mqtt_state = ConnectionState.ERROR

    def _on_disconnect(self, client, userdata, rc):
        logger.warning(f"MQTT disconnected with code {rc}")
        self.mqtt_state = ConnectionState.DISCONNECTED

        if self.running:
            self._schedule_reconnect()

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        logger.info(f"Subscribed successfully, QoS: {granted_qos}")

    def _on_message(self, client, userdata, msg):
        try:
            logger.info(f"[DOWNLINK] Topic: {msg.topic}, QoS: {msg.qos}, Payload: {msg.payload.hex()}")
            self._handle_downlink_message(msg.payload)
        except Exception as e:
            logger.error(f"Error handling downlink message: {e}", exc_info=True)

    def _schedule_reconnect(self):
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            return

        self._reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
        self._reconnect_thread.start()

    def _reconnect_loop(self):
        while self.running and self.mqtt_state != ConnectionState.CONNECTED:
            logger.info(f"Scheduling MQTT reconnect in {self.reconnect_delay} seconds...")
            time.sleep(self.reconnect_delay)

            if not self.running:
                break

            if self.mqtt_state != ConnectionState.CONNECTED:
                self._do_mqtt_connect()
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)

    def _start_threads(self):
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True, name="Heartbeat")
        heartbeat_thread.start()

        polling_thread = threading.Thread(target=self._polling_loop, daemon=True, name="Polling")
        polling_thread.start()

        send_interval = self.module_config.get('send_interval', 30)
        logger.info(f"Threads started: heartbeat_interval={self.heartbeat_interval}s, data_send_interval={send_interval}s")

    def _heartbeat_loop(self):
        while self.running:
            time.sleep(self.heartbeat_interval)
            if self.mqtt_state == ConnectionState.CONNECTED:
                self._send_heartbeat()

    def _send_heartbeat(self):
        payload = bytes([FUNCTION_CODES['HEARTBEAT']])
        self._publish_uplink(payload)
        logger.info(f"[UPLINK] Heartbeat sent: {payload.hex()}")

    def _polling_loop(self):
        while self.running:
            send_interval = self.module_config.get('send_interval', 30)
            time.sleep(send_interval)

            if self.mqtt_state != ConnectionState.CONNECTED:
                continue

            with self._data_configs_lock:
                if not self.data_configs:
                    continue

            self._poll_and_upload_data()

    def _poll_and_upload_data(self):
        with self._data_configs_lock:
            configs = list(self.data_configs)

        for cfg in configs:
            func_code = REGION_TO_FUNC_CODE.get(cfg.func_code, cfg.func_code)

            modbus_data = self.modbus_pool.read_modbus(
                slave_id=cfg.slave_id,
                func_code=func_code,
                start_addr=cfg.start_addr,
                quantity=cfg.quantity
            )

            if modbus_data:
                self._upload_data(cfg, modbus_data)
            else:
                logger.warning(f"Failed to read Modbus data for config: {cfg}")

    def _upload_data(self, cfg: DataConfig, modbus_data: bytes):
        payload = bytes([FUNCTION_CODES['DATA_UPLOAD']])

        data_count = 1
        payload += struct.pack('>H', data_count)

        payload += bytes([cfg.slave_id])
        payload += bytes([cfg.func_code])
        payload += struct.pack('>H', cfg.start_addr)

        if cfg.func_code in [3, 4]:
            data_len = cfg.quantity * 2
        else:
            data_len = (cfg.quantity + 7) // 8
        payload += struct.pack('>H', data_len)

        payload += modbus_data

        self._publish_uplink(payload)
        logger.info(f"[UPLINK] Data Upload: {payload.hex()}")

    def _handle_downlink_message(self, payload: bytes):
        if len(payload) < 1:
            logger.warning("Empty payload received")
            return

        func_code = payload[0]

        handlers = {
            FUNCTION_CODES['DOWNLOAD_DATA_CONFIG']: self._handle_download_data_config,
            FUNCTION_CODES['DOWNLOAD_MODULE_CONFIG']: self._handle_download_module_config,
            FUNCTION_CODES['REMOTE_WRITE']: self._handle_remote_write,
        }

        handler = handlers.get(func_code)
        if handler:
            handler(payload[1:])
        else:
            logger.warning(f"Unknown function code: {func_code:02X}")

    def _handle_download_data_config(self, data: bytes):
        logger.info("[HANDLER] Download Data Config")

        if len(data) < 2:
            logger.error("Invalid data config payload: too short")
            return

        data_count = int(data[0]) << 8 | int(data[1])
        logger.info(f"Data config count: {data_count}")

        new_configs = []

        offset = 2
        for i in range(data_count):
            if offset + 6 > len(data):
                logger.error(f"Incomplete data config at index {i}")
                break

            slave_id = data[offset]
            func_code = data[offset + 1]
            start_addr = int(data[offset + 2]) << 8 | int(data[offset + 3])
            quantity = int(data[offset + 4]) << 8 | int(data[offset + 5])
            offset += 6

            cfg = DataConfig(
                slave_id=slave_id,
                func_code=func_code,
                start_addr=start_addr,
                quantity=quantity
            )
            new_configs.append(cfg)

            logger.info(f"  Config[{i}]: slave_id={slave_id}, func_code={func_code}, addr={start_addr}, qty={quantity}")

        with self._data_configs_lock:
            self.data_configs = new_configs

        self._send_config_result(success=True)
        logger.info(f"Data config updated with {len(new_configs)} configurations")

    def _handle_download_module_config(self, data: bytes):
        logger.info("[HANDLER] Download Module Config")

        if len(data) >= 4:
            self.module_config['send_mode'] = data[0]
            self.module_config['config_data'] = struct.unpack('>H', data[1:3])[0]
            self.module_config['baud'] = data[3]

            send_interval = self.module_config['config_data']
            if send_interval > 0:
                self.module_config['send_interval'] = send_interval
                logger.info(f"Send interval updated to: {send_interval} seconds")

            logger.info(f"Module config: {self.module_config}")

        self._send_config_result(success=True)

    def _handle_remote_write(self, data: bytes):
        logger.info("[HANDLER] Remote Write")

        if len(data) < 6:
            logger.error("Invalid remote write payload: too short")
            self._send_config_result(success=False)
            return

        slave_id = data[0]
        func_code = data[1]
        addr = int(data[2]) << 8 | int(data[3])
        value = int(data[4]) << 8 | int(data[5])

        logger.info(f"  Remote write: slave={slave_id}, func={func_code}, addr={addr}, value={value}")

        self._send_config_result(success=True)

    def _send_config_result(self, success: bool = True):
        payload = bytes([FUNCTION_CODES['CONFIG_RESULT']])
        payload += bytes([0x00 if success else 0x01])
        self._publish_uplink(payload)
        logger.debug(f"[UPLINK] Config Result: {payload.hex()}")

    def _publish_uplink(self, payload: bytes):
        with self._mqtt_lock:
            if self.mqtt_client and self.mqtt_state == ConnectionState.CONNECTED:
                try:
                    result = self.mqtt_client.publish(self.up_topic, payload, qos=2)
                    if result.rc != mqtt.MQTT_ERR_SUCCESS:
                        logger.warning(f"Failed to publish uplink: {mqtt.error_string(result.rc)}")
                except Exception as e:
                    logger.error(f"Error publishing uplink: {e}")


def main():
    from config import MQTT_BROKER, MQTT_PORT, DEVICE_SERIAL, UP_TOPIC, DOWN_TOPIC, MODBUS_HOST, MODBUS_PORT

    simulator = DTUSimulatorV2(
        mqtt_broker=MQTT_BROKER,
        mqtt_port=MQTT_PORT,
        device_serial=DEVICE_SERIAL,
        modbus_host=MODBUS_HOST,
        modbus_port=MODBUS_PORT,
        up_topic=UP_TOPIC,
        down_topic=DOWN_TOPIC,
        heartbeat_interval=30,
        poll_interval=30
    )

    try:
        simulator.start()
        print("=" * 60)
        print("DTU Simulator V2 Running")
        print(f"Device Serial: {DEVICE_SERIAL}")
        print(f"MQTT: {MQTT_BROKER}:{MQTT_PORT}")
        print(f"Modbus: {MODBUS_HOST}:{MODBUS_PORT}")
        print("=" * 60)
        print("Press Ctrl+C to stop")
        print("=" * 60)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nShutdown requested...")
    finally:
        simulator.stop()


if __name__ == "__main__":
    main()
