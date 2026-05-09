#!/usr/bin/env python3
"""
直接连接到模拟器的 Modbus TCP 并写入正确的数据
"""

import sys
import struct
import socket

# Modbus 协议常量
FUNC_WRITE_COIL = 5
FUNC_WRITE_REGISTER = 6
FUNC_WRITE_MULTIPLE_REGISTERS = 23


def create_modbus_tcp_request(slave_id, func_code, payload):
    """创建 Modbus TCP 请求"""
    # 事务ID
    transaction_id = 1
    # 协议ID（Modbus=0）
    protocol_id = 0
    # 单元ID
    unit_id = slave_id
    
    # 长度 = 单元ID长度(1) + 功能码(1) + 有效载荷长度
    length = 1 + 1 + len(payload)
    
    # 构建头部
    header = struct.pack('>HHHB', transaction_id, protocol_id, length, unit_id)
    
    # 构建完整报文
    return header + bytes([func_code]) + payload


def send_modbus_tcp_command(host, port, slave_id, func_code, payload, timeout=2):
    """发送 Modbus TCP 命令并返回响应"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        
        request = create_modbus_tcp_request(slave_id, func_code, payload)
        sock.sendall(request)
        
        # 读取响应头
        response_header = sock.recv(8)
        if not response_header:
            return None
        
        # 解析响应长度
        (txn_id, proto_id, length, unit_id) = struct.unpack('>HHHB', response_header)
        expected_data_len = length - 2  # 减去功能码和单元ID
        
        # 读取响应数据
        response_data = b''
        while len(response_data) < expected_data_len:
            chunk = sock.recv(expected_data_len - len(response_data))
            if not chunk:
                break
            response_data += chunk
        
        sock.close()
        return response_header + response_data
        
    except Exception as e:
        print(f"  ❌ Modbus TCP 错误: {e}")
        return None


def write_single_coil(host, port, slave_id, addr, value):
    """写入单个线圈"""
    payload = struct.pack('>HH', addr, 0xFF00 if value else 0x0000)
    return send_modbus_tcp_command(host, port, slave_id, FUNC_WRITE_COIL, payload) is not None


def write_single_register(host, port, slave_id, addr, value):
    """写入单个寄存器"""
    payload = struct.pack('>HH', addr, value)
    return send_modbus_tcp_command(host, port, slave_id, FUNC_WRITE_REGISTER, payload) is not None


def write_multiple_registers(host, port, slave_id, start_addr, values):
    """写入多个寄存器"""
    # 构建 Payload: 起始地址(2B) + 数量(2B) + 字节数(1B) + 数据
    num_registers = len(values)
    byte_count = num_registers * 2
    
    payload = bytearray()
    payload.extend(struct.pack('>HH', start_addr, num_registers))
    payload.append(byte_count)
    for val in values:
        payload.extend(struct.pack('>H', val))
    
    return send_modbus_tcp_command(host, port, slave_id, FUNC_WRITE_MULTIPLE_REGISTERS, bytes(payload)) is not None


def string_to_registers(s):
    """字符串转寄存器列表，大端序"""
    data = s.encode('utf-8')
    registers = []
    for i in range(0, len(data), 2):
        byte1 = data[i] if i < len(data) else 0
        byte2 = data[i+1] if (i+1) < len(data) else 0
        reg_val = (byte1 << 8) | byte2
        registers.append(reg_val)
    return registers


def main():
    print("="*60)
    print("直接连接 Modbus TCP 并重置所有变量")
    print("="*60)
    
    host = "127.0.0.1"
    port = 502
    slave_id = 1
    
    # 1. 写入 0区线圈（变量1-4）
    print("\n1️⃣  写入0区线圈...")
    coil_addresses = [0, 8, 16, 24]
    for addr in coil_addresses:
        ok = write_single_coil(host, port, slave_id, addr, True)
        print(f"  地址 {addr} → {'✅ 成功' if ok else '❌ 失败'}")
    
    # 2. 写入 1区离散输入 - 注意：离散输入通常不能写入！
    # 但我们通过线圈的方式测试，或者直接忽略（因为模拟器有初始化逻辑）
    
    # 3. 写入 3区输入寄存器（变量9-10）
    print("\n2️⃣  写入3区输入寄存器字符串...")
    input_reg_0_str = "ABCDEFGHIJKLM"
    input_reg_0_vals = string_to_registers(input_reg_0_str)
    # 补零到 7个寄存器
    while len(input_reg_0_vals) < 7:
        input_reg_0_vals.append(0)
    ok = write_multiple_registers(host, port, slave_id, 0, input_reg_0_vals)
    print(f"  地址 0-6 → \"{input_reg_0_str}\": {'✅ 成功' if ok else '❌ 失败'}")
    
    input_reg_13_str = "ABCDEFGHIJKLM"
    input_reg_13_vals = string_to_registers(input_reg_13_str)
    while len(input_reg_13_vals) < 7:
        input_reg_13_vals.append(0)
    ok = write_multiple_registers(host, port, slave_id, 13, input_reg_13_vals)
    print(f"  地址 13-19 → \"{input_reg_13_str}\": {'✅ 成功' if ok else '❌ 失败'}")
    
    # 4. 写入 4区保持寄存器（变量11-12） - 关键！
    print("\n3️⃣  写入4区保持寄存器字符串...")
    holding_reg_0_str = "ABCDEFGHIJKLM"
    holding_reg_0_vals = string_to_registers(holding_reg_0_str)
    while len(holding_reg_0_vals) < 7:
        holding_reg_0_vals.append(0)
    ok = write_multiple_registers(host, port, slave_id, 0, holding_reg_0_vals)
    print(f"  地址 0-6 → \"{holding_reg_0_str}\": {'✅ 成功' if ok else '❌ 失败'}")
    
    holding_reg_13_str = "ABCDEFGHIJKLM"
    holding_reg_13_vals = string_to_registers(holding_reg_13_str)
    while len(holding_reg_13_vals) < 7:
        holding_reg_13_vals.append(0)
    ok = write_multiple_registers(host, port, slave_id, 13, holding_reg_13_vals)
    print(f"  地址 13-19 → \"{holding_reg_13_str}\": {'✅ 成功' if ok else '❌ 失败'}")
    
    print("\n" + "="*60)
    print("✅ 所有变量重置完成！")
    print("="*60)
    print("\n等待下一次数据上报（约30秒）...")


if __name__ == "__main__":
    main()
