#!/usr/bin/env python3
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def login():
    login_data = {"username": "admin", "password": "1"}
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        result = response.json()
        if result.get("code") == 0:
            print(f"✅ 登录成功")
            return result.get("data", {}).get("token")
        else:
            print(f"❌ 登录失败: {result}")
            return None
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return None

def get_device_list(token):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(f"{BASE_URL}/get-devicelist", headers=headers, json={})
        result = response.json()
        if result.get("code") == 0:
            devices = result.get("data", {}).get("devicelist", [])
            if devices:
                print(f"✅ 找到设备: {devices[0]['name']} ({devices[0]['serial']})")
                return devices[0]
        print("❌ 获取设备失败")
        return None
    except Exception as e:
        print(f"❌ 获取设备失败: {e}")
        return None

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

def force_reset_single_coil(token, dev_serial, slave_addr, start_addr, value):
    """强制重置单个线圈"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "devSerial": dev_serial,
        "entries": [{
            "slaveAddr": slave_addr,
            "dataType": 0,
            "startAddr": start_addr,
            "length": 1,
            "values": [1 if value else 0]
        }]
    }
    try:
        response = requests.post(f"{BASE_URL}/sendcod/remote-write", headers=headers, json=payload)
        result = response.json()
        return result.get("code") == 0
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        return False

def force_reset_single_di(token, dev_serial, slave_addr, start_addr, value):
    """强制重置单个离散输入"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "devSerial": dev_serial,
        "entries": [{
            "slaveAddr": slave_addr,
            "dataType": 1,
            "startAddr": start_addr,
            "length": 1,
            "values": [1 if value else 0]
        }]
    }
    try:
        response = requests.post(f"{BASE_URL}/sendcod/remote-write", headers=headers, json=payload)
        result = response.json()
        return result.get("code") == 0
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        return False

def force_reset_string(token, dev_serial, slave_addr, modbus_type, start_addr, value, num_registers):
    """强制重置字符串"""
    headers = {"Authorization": f"Bearer {token}"}
    registers = string_to_registers(value)
    # 补零到指定数量的寄存器
    while len(registers) < num_registers:
        registers.append(0)
    payload = {
        "devSerial": dev_serial,
        "entries": [{
            "slaveAddr": slave_addr,
            "dataType": modbus_type,
            "startAddr": start_addr,
            "length": num_registers,
            "values": registers
        }]
    }
    try:
        response = requests.post(f"{BASE_URL}/sendcod/remote-write", headers=headers, json=payload)
        result = response.json()
        return result.get("code") == 0
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        return False

def main():
    print("="*60)
    print("强制重置所有变量（通过远程置数API）")
    print("="*60)

    token = login()
    if not token:
        return

    device = get_device_list(token)
    if not device:
        return

    dev_serial = device["serial"]

    print("\n📋 开始重置...")

    # 1-4: 0区线圈
    print("\n1️⃣  重置0区线圈变量...")
    for i in range(4):
        var_num = i + 1
        addr = 0 if i == 0 else (8 * i)
        print(f"  变量{var_num}: 0区线圈 地址{addr} → 1")
        ok = force_reset_single_coil(token, dev_serial, 1, addr, True)
        print(f"  {'✅ 成功' if ok else '❌ 失败'}")

    # 5-8: 1区离散输入
    print("\n2️⃣  重置1区离散输入变量...")
    for i in range(4):
        var_num = i + 5
        addr = 0 if i == 0 else (8 * i if i < 3 else 32)
        print(f"  变量{var_num}: 1区离散 地址{addr} → 1")
        ok = force_reset_single_di(token, dev_serial, 1, addr, True)
        print(f"  {'✅ 成功' if ok else '❌ 失败'}")

    # 9-12: 3区和4区字符串
    print("\n3️⃣  重置字符串变量...")
    for i in range(4):
        var_num = i + 9
        modbus_type = 3 if i < 2 else 4
        addr = 0 if i % 2 == 0 else 13
        value = "ABCDEFGHIJKLM"
        print(f"  变量{var_num}: {modbus_type}区字符串 地址{addr} → \"{value}\"")
        ok = force_reset_string(token, dev_serial, 1, modbus_type, addr, value, 7)
        print(f"  {'✅ 成功' if ok else '❌ 失败'}")

    print("\n" + "="*60)
    print("✅ 所有变量重置完成！")
    print("="*60)
    print("\n请等待下一次数据上报（约30秒）后刷新前端查看")

if __name__ == "__main__":
    main()
