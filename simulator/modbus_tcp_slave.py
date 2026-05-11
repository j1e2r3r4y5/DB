#!/usr/bin/env python3
"""
Modbus TCP Slave Simulator
Simulates a Modbus TCP slave device with multiple register types.
Supports dynamic adding/removing of slave devices.
"""

import socket
import struct
import threading
import random
import time
from typing import Dict, Optional, List
from dataclasses import dataclass


FUNCTION_CODES = {
    'READ_COILS': 0x01,
    'READ_DISCRETE_INPUTS': 0x02,
    'READ_HOLDING_REGISTERS': 0x03,
    'READ_INPUT_REGISTERS': 0x04,
    'WRITE_SINGLE_COIL': 0x05,
    'WRITE_SINGLE_REGISTER': 0x06,
}


@dataclass
class RegisterArea:
    coils: Dict[int, bool]
    discrete_inputs: Dict[int, bool]
    holding_registers: Dict[int, int]
    input_registers: Dict[int, int]


class ModbusDevice:
    def __init__(self, slave_id: int):
        self.slave_id = slave_id
        self.area = RegisterArea(
            coils={},
            discrete_inputs={},
            holding_registers={},
            input_registers={}
        )
        self.online = True
        self._init_default_data()

    def _init_default_data(self):
        if self.slave_id == 1:
            self.area.holding_registers[0] = 250
            self.area.holding_registers[1] = 600
            self.area.holding_registers[9] = 15000
            self.area.coils[0] = True
            self._running = True
            self._update_thread = threading.Thread(target=self._update_values, daemon=True)
            self._update_thread.start()

    def _update_values(self):
        while self._running:
            if self.slave_id == 1:
                self.area.holding_registers[0] = max(0, min(1000, 250 + random.randint(-50, 50)))
                self.area.holding_registers[1] = max(0, min(1000, 600 + random.randint(-30, 30)))
                self.area.holding_registers[9] = max(0, min(20000, 15000 + random.randint(-100, 100)))
            time.sleep(2)

    def stop(self):
        self._running = False


class ModbusTCPSlave:
    def __init__(self, host: str = "127.0.0.1", port: int = 502):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.devices: Dict[int, ModbusDevice] = {}
        self.lock = threading.Lock()
        self._add_default_device()

    def _add_default_device(self):
        device = ModbusDevice(slave_id=1)
        self.devices[1] = device

    def add_device(self, slave_id: int) -> bool:
        with self.lock:
            if slave_id in self.devices:
                return False
            self.devices[slave_id] = ModbusDevice(slave_id=slave_id)
            return True

    def remove_device(self, slave_id: int) -> bool:
        with self.lock:
            if slave_id not in self.devices:
                return False
            if slave_id in self.devices:
                self.devices[slave_id].stop()
                del self.devices[slave_id]
            return True

    def is_device_online(self, slave_id: int) -> bool:
        with self.lock:
            return slave_id in self.devices

    def get_device(self, slave_id: int) -> Optional[ModbusDevice]:
        with self.lock:
            return self.devices.get(slave_id)

    def start(self):
        self.running = True
        self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
        self.server_thread.start()
        print(f"Modbus TCP Slave started on {self.host}:{self.port}")

    def stop(self):
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        with self.lock:
            for device in self.devices.values():
                device.stop()

    def _server_loop(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        self.socket.settimeout(1.0)

        while self.running:
            try:
                client_socket, addr = self.socket.accept()
                thread = threading.Thread(target=self._handle_client, args=(client_socket,), daemon=True)
                thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"Accept error: {e}")

    def _handle_client(self, client_socket: socket.socket):
        try:
            client_socket.settimeout(5.0)
            while self.running:
                try:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    response = self._process_request(data)
                    if response:
                        client_socket.send(response)
                except socket.timeout:
                    break
                except Exception as e:
                    print(f"Client error: {e}")
                    break
        finally:
            client_socket.close()

    def _process_request(self, data: bytes) -> Optional[bytes]:
        if len(data) < 9:
            return None

        transaction_id = struct.unpack('>H', data[0:2])[0]
        protocol_id = struct.unpack('>H', data[2:4])[0]
        length = struct.unpack('>H', data[4:6])[0]
        slave_id = data[6]
        function_code = data[7]

        with self.lock:
            if slave_id not in self.devices:
                return self._build_error_response(transaction_id, protocol_id, slave_id, function_code, 0x0B)

        device = self.devices[slave_id]

        if function_code == FUNCTION_CODES['READ_COILS']:
            return self._read_coils(device, transaction_id, protocol_id, data)
        elif function_code == FUNCTION_CODES['READ_DISCRETE_INPUTS']:
            return self._read_discrete_inputs(device, transaction_id, protocol_id, data)
        elif function_code == FUNCTION_CODES['READ_HOLDING_REGISTERS']:
            return self._read_holding_registers(device, transaction_id, protocol_id, data)
        elif function_code == FUNCTION_CODES['READ_INPUT_REGISTERS']:
            return self._read_input_registers(device, transaction_id, protocol_id, data)
        elif function_code == FUNCTION_CODES['WRITE_SINGLE_COIL']:
            return self._write_single_coil(device, transaction_id, protocol_id, data)
        elif function_code == FUNCTION_CODES['WRITE_SINGLE_REGISTER']:
            return self._write_single_register(device, transaction_id, protocol_id, data)
        else:
            return self._build_error_response(transaction_id, protocol_id, slave_id, function_code, 0x01)

    def _read_coils(self, device: ModbusDevice, transaction_id: int, protocol_id: int, data: bytes) -> bytes:
        start_addr = struct.unpack('>H', data[8:10])[0]
        quantity = struct.unpack('>H', data[10:12])[0]

        byte_count = (quantity + 7) // 8
        coil_values = []
        for i in range(quantity):
            addr = start_addr + i
            value = device.area.coils.get(addr, False)
            coil_values.append(value)

        response_data = [byte_count]
        for i in range(byte_count):
            byte_val = 0
            for bit in range(8):
                idx = i * 8 + bit
                if idx < len(coil_values) and coil_values[idx]:
                    byte_val |= (1 << bit)
            response_data.append(byte_val)

        return self._build_response(transaction_id, protocol_id, device.slave_id, FUNCTION_CODES['READ_COILS'], response_data)

    def _read_discrete_inputs(self, device: ModbusDevice, transaction_id: int, protocol_id: int, data: bytes) -> bytes:
        start_addr = struct.unpack('>H', data[8:10])[0]
        quantity = struct.unpack('>H', data[10:12])[0]

        byte_count = (quantity + 7) // 8
        input_values = []
        for i in range(quantity):
            addr = start_addr + i
            value = device.area.discrete_inputs.get(addr, False)
            input_values.append(value)

        response_data = [byte_count]
        for i in range(byte_count):
            byte_val = 0
            for bit in range(8):
                idx = i * 8 + bit
                if idx < len(input_values) and input_values[idx]:
                    byte_val |= (1 << bit)
            response_data.append(byte_val)

        return self._build_response(transaction_id, protocol_id, device.slave_id, FUNCTION_CODES['READ_DISCRETE_INPUTS'], response_data)

    def _read_holding_registers(self, device: ModbusDevice, transaction_id: int, protocol_id: int, data: bytes) -> bytes:
        start_addr = struct.unpack('>H', data[8:10])[0]
        quantity = struct.unpack('>H', data[10:12])[0]

        byte_count = quantity * 2
        response_data = [byte_count]
        for i in range(quantity):
            addr = start_addr + i
            value = device.area.holding_registers.get(addr, 0)
            response_data.extend(struct.pack('>H', value))

        return self._build_response(transaction_id, protocol_id, device.slave_id, FUNCTION_CODES['READ_HOLDING_REGISTERS'], response_data)

    def _read_input_registers(self, device: ModbusDevice, transaction_id: int, protocol_id: int, data: bytes) -> bytes:
        start_addr = struct.unpack('>H', data[8:10])[0]
        quantity = struct.unpack('>H', data[10:12])[0]

        byte_count = quantity * 2
        response_data = [byte_count]
        for i in range(quantity):
            addr = start_addr + i
            value = device.area.input_registers.get(addr, 0)
            response_data.extend(struct.pack('>H', value))

        return self._build_response(transaction_id, protocol_id, device.slave_id, FUNCTION_CODES['READ_INPUT_REGISTERS'], response_data)

    def _write_single_coil(self, device: ModbusDevice, transaction_id: int, protocol_id: int, data: bytes) -> bytes:
        addr = struct.unpack('>H', data[8:10])[0]
        value = struct.unpack('>H', data[10:12])[0]

        device.area.coils[addr] = (value == 0xFF00)

        return self._build_response(transaction_id, protocol_id, device.slave_id, FUNCTION_CODES['WRITE_SINGLE_COIL'],
                                     list(data[8:12]))

    def _write_single_register(self, device: ModbusDevice, transaction_id: int, protocol_id: int, data: bytes) -> bytes:
        addr = struct.unpack('>H', data[8:10])[0]
        value = struct.unpack('>H', data[10:12])[0]

        device.area.holding_registers[addr] = value

        return self._build_response(transaction_id, protocol_id, device.slave_id, FUNCTION_CODES['WRITE_SINGLE_REGISTER'],
                                     list(data[8:12]))

    def _build_response(self, transaction_id: int, protocol_id: int, slave_id: int, function_code: int, data: List[int]) -> bytes:
        body = bytes([slave_id, function_code] + data)
        length = len(body)
        header = struct.pack('>HHH', transaction_id, protocol_id, length)
        return header + body

    def _build_error_response(self, transaction_id: int, protocol_id: int, slave_id: int, function_code: int, error_code: int) -> bytes:
        return self._build_response(transaction_id, protocol_id, slave_id, function_code | 0x80, [error_code])
