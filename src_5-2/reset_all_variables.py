#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://127.0.0.1:8000"


def login():
    login_data = {
        "username": "admin",
        "password": "1"
    }
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        result = response.json()
        if result.get("code") == 0:
            token = result.get("data", {}).get("token")
            print(f"✅ 登录成功")
            return token
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
                device = devices[0]
                print(f"✅ 找到设备: {device['name']} ({device['serial']})")
                return device
            else:
                print("❌ 没有找到设备")
                return None
        else:
            print(f"❌ 获取设备列表失败: {result}")
            return None
    except Exception as e:
        print(f"❌ 获取设备列表请求失败: {e}")
        return None


def get_variables(token, dev_id):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(f"{BASE_URL}/getvariables", headers=headers, json={"devID": dev_id})
        result = response.json()
        if result.get("code") == 0:
            variables = result.get("data", {}).get("variables", [])
            print(f"✅ 获取到 {len(variables)} 个变量")
            return variables
        else:
            print(f"❌ 获取变量列表失败: {result}")
            return []
    except Exception as e:
        print(f"❌ 获取变量列表请求失败: {e}")
        return []


def send_remote_write(token, dev_serial, var_name, data_type, modbus_type, modbus_addr, value):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 构造远程置数的数据
    entries = []
    if data_type == 0:
        # 布尔/线圈
        entries.append({
            "slaveAddr": 1,
            "dataType": modbus_type,
            "startAddr": modbus_addr,
            "length": 1,
            "values": [1 if value else 0]
        })
    elif data_type == 5:
        # 字符串
        # 字符串转成字节数组，然后每2字节组成一个寄存器（大端序）
        bytes_value = value.encode('utf-8')
        reg_values = []
        for i in range(0, len(bytes_value), 2):
            byte1 = bytes_value[i] if i < len(bytes_value) else 0
            byte2 = bytes_value[i+1] if (i+1) < len(bytes_value) else 0
            reg_val = (byte1 << 8) | byte2
            reg_values.append(reg_val)
        
        entries.append({
            "slaveAddr": 1,
            "dataType": modbus_type,
            "startAddr": modbus_addr,
            "length": len(reg_values),
            "values": reg_values
        })
    
    data = {
        "devSerial": dev_serial,
        "entries": entries
    }
    
    print(f"\n📋 设置变量 '{var_name}' (类型 {data_type}, 区域 {modbus_type}, 地址 {modbus_addr})")
    print(f"   值: {value}")
    
    try:
        response = requests.post(f"{BASE_URL}/sendcod/remote-write", headers=headers, json=data)
        result = response.json()
        if result.get("code") == 0:
            print(f"✅ 远程置数成功！")
            return True
        else:
            print(f"❌ 远程置数失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 远程置数请求失败: {e}")
        return False


def main():
    print("=" * 60)
    print("使用远程置数强制重置所有变量")
    print("=" * 60)
    
    token = login()
    if not token:
        return
    
    device = get_device_list(token)
    if not device:
        return
    
    variables = get_variables(token, device['id'])
    if not variables:
        return
    
    # 定义正确的变量值
    correct_values = {
        '1': True,
        '2': True,
        '3': True,
        '4': True,
        '5': True,
        '6': True,
        '7': True,
        '8': True,
        '9': "ABCDEFGHIJKLM",
        '10': "ABCDEFGHIJKLM",
        '11': "ABCDEFGHIJKLM",
        '12': "ABCDEFGHIJKLM",
    }
    
    # 先设置所有字符串变量（因为它们更复杂）
    for var in variables:
        var_name = var.get('varName')
        if var_name in ['9', '10', '11', '12']:
            send_remote_write(
                token,
                device['serial'],
                var_name,
                var.get('dataType'),
                var.get('modbusType'),
                var.get('modbusAddr'),
                correct_values[var_name]
            )
    
    # 再设置布尔变量
    for var in variables:
        var_name = var.get('varName')
        if var_name in ['1', '2', '3', '4', '5', '6', '7', '8']:
            send_remote_write(
                token,
                device['serial'],
                var_name,
                var.get('dataType'),
                var.get('modbusType'),
                var.get('modbusAddr'),
                correct_values[var_name]
            )
    
    print("\n" + "=" * 60)
    print("✅ 所有变量强制设置完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
