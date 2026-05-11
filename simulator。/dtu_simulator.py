#!/usr/bin/env python3
"""
4G DTU Simulator
Simulates a 4G DTU device that communicates with the platform via MQTT
and with Modbus TCP slave devices.
"""

import socket
import struct
import threading
import time
import random
import json
from typing import Optional, Dict, Any, List
import paho.mqtt.client as mqtt


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

FUNCTION_NAMES = {v: k for k, v in FUNCTION_CODES.items()}


class DTUSimulator:
    def __init__(
        self,
        mqtt_broker: str,
        mqtt_port: int,
        device_serial: str,
        modbus_host: str,
        modbus_port: int,
        up_topic: str,
        down_topic: str
    ):
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.device_serial = device_serial
        self.modbus_host = modbus_host
        self.modbus_port = modbus_port
        self.up_topic = up_topic
        self.down_topic = down_topic

        self.mqtt_client = None
        self.running = False
        self.connected = False

        self.module_config = {
            'send_mode': 0x00,
            'config_data': 0x001E,
            'baud': 0x05,
        }

        self.data_config: List[Dict[str, Any]] = []

        self._modbus_lock = threading.Lock()

    def start(self):
        self.running = True
        import time
        self.mqtt_client = mqtt.Client(client_id=f"dtu_sim_{self.device_serial}_{int(time.time())}")
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message
        self.mqtt_client.on_disconnect = self._on_disconnect
        self.mqtt_client.keepalive = 60

        try:
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()

            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self._heartbeat_thread.start()

            print(f"DTU Simulator started, connecting to {self.mqtt_broker}:{self.mqtt_port}")
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")

    def stop(self):
        self.running = False
        self._stop_data_polling()
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
            self.connected = True
            client.subscribe(self.down_topic, qos=0)
            print(f"Subscribed to {self.down_topic}")
        else:
            print(f"MQTT connection failed with code {rc}")
            self.connected = False

    def _on_disconnect(self, client, userdata, rc):
        print(f"Disconnected from MQTT broker with code {rc}")
        self.connected = False

    def _on_message(self, client, userdata, msg):
        print(f"\n[DOWNLINK] Topic: {msg.topic}")
        print(f"[DOWNLINK] QoS: {msg.qos}")
        print(f"[DOWNLINK] Payload: {msg.payload.hex()}")

        self._handle_downlink_message(msg.payload)

    def _handle_downlink_message(self, payload: bytes):
        if len(payload) < 1:
            return

        func_code = payload[0]

        try:
            if func_code == FUNCTION_CODES['MODULE_CONFIG_QUERY']:
                self._handle_module_config_query(payload[1:])
            elif func_code == FUNCTION_CODES['DOWNLOAD_MODULE_CONFIG']:
                self._handle_download_module_config(payload[1:])
            elif func_code == FUNCTION_CODES['DATA_CONFIG_QUERY']:
                self._handle_data_config_query(payload[1:])
            elif func_code == FUNCTION_CODES['DOWNLOAD_DATA_CONFIG']:
                self._handle_download_data_config(payload[1:])
            elif func_code == FUNCTION_CODES['REMOTE_WRITE']:
                self._handle_remote_write(payload[1:])
            else:
                print(f"[WARNING] Unknown function code: {func_code:02X}")
        except Exception as e:
            print(f"[ERROR] Error handling downlink message: {e}")

    def _handle_module_config_query(self, data: bytes):
        print("[HANDLER] Module Config Query")
        modbus_response = self._query_modbus_registers(slave_id=1, func_code=0x03, start_addr=0, quantity=10)
        if modbus_response:
            self._upload_module_config(modbus_response)

    def _upload_module_config(self, modbus_data: bytes):
        payload = bytes([FUNCTION_CODES['MODULE_CONFIG_UPLOAD']])
        payload += bytes([self.module_config['send_mode']])
        payload += struct.pack('>H', self.module_config['config_data'])
        payload += bytes([self.module_config['baud']])

        self._publish_uplink(payload)
        print(f"[UPLINK] Module Config Upload: {payload.hex()}")

    def _handle_download_module_config(self, data: bytes):
        print("[HANDLER] Download Module Config")
        if len(data) >= 4:
            self.module_config['send_mode'] = data[0]
            self.module_config['config_data'] = struct.unpack('>H', data[1:3])[0]
            self.module_config['baud'] = data[3]

        result = bytes([FUNCTION_CODES['MODULE_CONFIG_RESULT']])
        result += bytes([0x00])

        self._publish_uplink(result)
        print(f"[UPLINK] Module Config Result: {result.hex()}")

    def _handle_data_config_query(self, data: bytes):
        print("[HANDLER] Data Config Query")
        for cfg in self.data_config:
            modbus_response = self._read_modbus(
                slave_id=cfg['slave_id'],
                func_code=cfg['func_code'],
                start_addr=cfg['start_addr'],
                quantity=cfg['quantity']
            )
            if modbus_response:
                self._upload_data_config(cfg, modbus_response)

    def _upload_data_config(self, cfg: Dict[str, Any], modbus_data: bytes):
        # 协议文档规定：2字节数据数量（项数）
        payload = bytes([FUNCTION_CODES['DATA_CONFIG_UPLOAD']])
        data_count = 1  # 当前DTU配置了1组数据
        payload += struct.pack('>H', data_count)
        payload += bytes([cfg['slave_id']])
        payload += bytes([cfg['func_code']])
        payload += struct.pack('>H', cfg['start_addr'])
        payload += struct.pack('>H', cfg['quantity'])

        self._publish_uplink(payload)
        print(f"[UPLINK] Data Config Upload: {payload.hex()}")

    def _handle_download_data_config(self, data: bytes):
        """
        处理04数据配置下发

        【协议格式】04 00 01 01 04 00 00 00 02
        | 字节位置 | 字节值 | 含义 |
        |---------|--------|------|
        | 0 | 04 | 功能码（数据配置下发） |
        | 1-2 | 00 01 | 数据组数 = 1 |
        | 3 | 01 | 从站地址 = 1 |
        | 4 | 04 | 类型 = 4（保持寄存器区） |
        | 5-6 | 00 00 | 起始地址 = 0 |
        | 7-8 | 00 02 | 物理数量 = 2（读取2个寄存器） |
        """
        print("[HANDLER] Download Data Config")
        if len(data) < 2:
            return

        # data[0:2] is the data group count (big endian)
        data_count = int(data[0]) << 8 | int(data[1])
        self.data_config = []

        offset = 2
        # Each data group is 6 bytes: slave_id(1) + func_code(1) + start_addr(2) + quantity(2)
        for i in range(data_count):
            if offset + 6 > len(data):
                break
            slave_id = data[offset]
            func_code = data[offset + 1]  # 区域编号: 0/1/3/4
            start_addr = int(data[offset + 2]) << 8 | int(data[offset + 3])
            quantity = int(data[offset + 4]) << 8 | int(data[offset + 5])  # 物理数量（寄存器或位的数量）
            offset += 6

            self.data_config.append({
                'slave_id': slave_id,
                'func_code': func_code,
                'start_addr': start_addr,
                'quantity': quantity  # 物理数量：读取多少个寄存器/位
            })

            print(f"  Config item: slave_id={slave_id}, func_code={func_code}, addr={start_addr}, qty={quantity}")

        result = bytes([FUNCTION_CODES['CONFIG_RESULT']])
        result += bytes([0x00])

        self._publish_uplink(result)
        print(f"[UPLINK] Config Result: {result.hex()}")

        # 收到数据配置后，自动开始轮询并上传数据
        self._start_data_polling()

    def _start_data_polling(self):
        """启动数据轮询线程"""
        if hasattr(self, '_polling_thread') and self._polling_thread.is_alive():
            return
        self._polling_running = True
        self._polling_thread = threading.Thread(target=self._data_polling_loop, daemon=True)
        self._polling_thread.start()
        print("[POLLING] Data polling started")

    def _stop_data_polling(self):
        """停止数据轮询"""
        self._polling_running = False

    def _data_polling_loop(self):
        """数据轮询循环，每10秒上传一次数据"""
        while self._polling_running and self.running:
            time.sleep(10)
            if self.connected and self.data_config:
                self._poll_and_upload_data()

    def _handle_remote_write(self, data: bytes):
        print("[HANDLER] Remote Write")
        if len(data) < 6:
            return

        slave_id = data[0]
        func_code = data[1]
        addr = int(data[2]) << 8 | int(data[3])
        value = int(data[4]) << 8 | int(data[5])

        print(f"  Remote write: slave={slave_id}, func={func_code}, addr={addr}, value={value}")

        success = self._write_modbus(slave_id, func_code, addr, value)

        result = bytes([FUNCTION_CODES['CONFIG_RESULT']])
        result += bytes([0x00 if success else 0x01])

        self._publish_uplink(result)
        print(f"[UPLINK] Remote Write Result: {result.hex()}")

    def _heartbeat_loop(self):
        while self.running:
            time.sleep(30)
            if self.connected:
                self._send_heartbeat()

    def _send_heartbeat(self):
        payload = bytes([FUNCTION_CODES['HEARTBEAT']])
        self._publish_uplink(payload)
        print(f"[UPLINK] Heartbeat sent: {payload.hex()}")

    def _poll_and_upload_data(self):
        if not self.data_config:
            return

        for cfg in self.data_config:
            # NOTE: 前端下发的 func_code 实际是 Modbus 区域编号，不是功能码
            # 区域编号: 1=线圈(Coils), 2=离散输入(Discrete Inputs), 3=输入寄存器(Input Registers), 4=保持寄存器(Holding Registers)
            # 功能码: 0x01=读线圈, 0x02=读离散输入, 0x03=读保持寄存器, 0x04=读输入寄存器
            # 所以 4区(保持寄存器) 需要用功能码 0x03 来读取
            # 转换映射: 区域0→功能码0x01, 区域1→功能码0x02, 区域3→功能码0x04, 区域4→功能码0x03
            region_to_func_code = {0: 0x01, 1: 0x02, 3: 0x04, 4: 0x03}
            read_func_code = region_to_func_code.get(cfg['func_code'], cfg['func_code'])

            modbus_data = self._read_modbus(
                slave_id=cfg['slave_id'],
                func_code=read_func_code,
                start_addr=cfg['start_addr'],
                quantity=cfg['quantity']
            )
            if modbus_data:
                self._upload_data(cfg, modbus_data)

    def _upload_data(self, cfg: Dict[str, Any], modbus_data: bytes):
        """
        上传数据到服务器

        【协议说明】05上发格式:
        - 功能码(1字节) + 数据组数(2字节) + 每组数据(从站地址1 + 类型1 + 起始地址2 + 数据长度2 + 数据n字节)

        【关键】数据组数 = 下发04中的数据组数（合并后的组数）
               数据长度 = 该组内所有数据的实际字节数

        例如下发04: 04 00 01 01 04 00 00 00 02
        - 数据组数=1, 01=从站地址, 04=类型(4区), 00 00=起始地址, 00 02=物理数量(2个寄存器)
        - 模拟器读取2个寄存器的数据后，上发05:
        - 05 00 01 = 功能码 + 数据组数=1（来自04的一组配置，合并了温度和湿度）
          01 04 00 00 00 04 = 从站地址 + 类型 + 起始地址 + 数据长度=4字节
          00 FA 02 58 = 2个寄存器的实际数据

        解析方式：后端根据MySQL中变量配置(modbusType, modbusAddr)来拆分这n字节数据
        """
        payload = bytes([FUNCTION_CODES['DATA_UPLOAD']])

        # 【重要】data_count = 下发04中该组的数据组数（已合并相邻寄存器）
        # 例如：温度(addr=0)和湿度(addr=1)相邻 → 合并为一组下发 → data_count=1
        # 如果温度和湿度不相邻 → 分成多组下发 → 多次调用_upload_data，每次data_count=1
        data_count = 1
        payload += struct.pack('>H', data_count)

        payload += bytes([cfg['slave_id']])
        payload += bytes([cfg['func_code']])
        payload += struct.pack('>H', cfg['start_addr'])

        # 【重要】数据长度 = 所有数据的实际字节数
        # - 寄存器区域(3,4): 寄存器数 × 2字节
        # - 线圈区域(0,1): ceil(位数/8)字节
        if cfg['func_code'] in [3, 4]:
            data_len_bytes = cfg['quantity'] * 2
        else:  # 0, 1 线圈/离散输入
            data_len_bytes = (cfg['quantity'] + 7) // 8
        payload += struct.pack('>H', data_len_bytes)

        # 按区域类型发送数据
        if cfg['func_code'] in [3, 4]:  # 寄存器区域
            # 寄存器数据：每寄存器2字节，直接追加
            payload += modbus_data
        elif cfg['func_code'] in [0, 1]:  # 线圈/离散输入区域
            # 线圈数据：已经是字节数组（按位打包），直接追加
            payload += modbus_data

        self._publish_uplink(payload)
        print(f"[UPLINK] Data Upload: {payload.hex()}")

    def _query_modbus_registers(self, slave_id: int, func_code: int, start_addr: int, quantity: int) -> Optional[bytes]:
        return self._read_modbus(slave_id, func_code, start_addr, quantity)

    def _read_modbus(self, slave_id: int, func_code: int, start_addr: int, quantity: int) -> Optional[bytes]:
        with self._modbus_lock:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5.0)
                sock.connect((self.modbus_host, self.modbus_port))

                transaction_id = random.randint(1, 65535)
                protocol_id = 0
                length = 6

                request = struct.pack('>HHH', transaction_id, protocol_id, length)
                request += bytes([slave_id, func_code])
                request += struct.pack('>HH', start_addr, quantity)

                sock.send(request)

                response = sock.recv(1024)
                sock.close()

                if len(response) >= 9 and response[7] == func_code:
                    byte_count = response[8]
                    return response[9:9 + byte_count]

            except Exception as e:
                print(f"[ERROR] Modbus read error: {e}")

        return None

    def _write_modbus(self, slave_id: int, func_code: int, addr: int, value: int) -> bool:
        with self._modbus_lock:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5.0)
                sock.connect((self.modbus_host, self.modbus_port))

                transaction_id = random.randint(1, 65535)
                protocol_id = 0
                length = 6

                request = struct.pack('>HHH', transaction_id, protocol_id, length)
                request += bytes([slave_id, func_code])
                request += struct.pack('>HH', addr, value)

                sock.send(request)

                response = sock.recv(1024)
                sock.close()

                if len(response) >= 8 and response[7] == func_code:
                    return True

            except Exception as e:
                print(f"[ERROR] Modbus write error: {e}")

        return False

    def _publish_uplink(self, payload: bytes):
        if self.mqtt_client and self.connected:
            self.mqtt_client.publish(self.up_topic, payload, qos=2)
