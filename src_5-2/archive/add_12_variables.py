#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# 先登录获取token
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
            print(f"✅ 登录成功，token: {token[:20]}...")
            return token
        else:
            print(f"❌ 登录失败: {result}")
            return None
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return None

# 获取设备列表
def get_device_list(token):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(f"{BASE_URL}/get-devicelist", headers=headers, json={})
        result = response.json()
        if result.get("code") == 0:
            devices = result.get("data", {}).get("devicelist", [])
            if devices:
                device = devices[0]
                print(f"✅ 找到设备: ID={device['id']}, 名称={device['name']}, 序列号={device['serial']}")
                return device['id']
            else:
                print("❌ 没有找到设备")
                return None
        else:
            print(f"❌ 获取设备列表失败: {result}")
            return None
    except Exception as e:
        print(f"❌ 获取设备列表请求失败: {e}")
        return None

# 添加变量
def add_variable(token, dev_id, var_name, data_type, modbus_type, modbus_device, modbus_addr, data_len, string_len=""):
    headers = {"Authorization": f"Bearer {token}"}
    variable_data = {
        "variable": {
            "devID": dev_id,
            "varName": var_name,
            "dataType": data_type,
            "modbusType": modbus_type,
            "modbusDevice": modbus_device,
            "modbusAddr": modbus_addr,
            "dataLen": str(data_len),
            "stringLen": str(string_len) if string_len else ""
        }
    }
    try:
        response = requests.post(f"{BASE_URL}/addvariable", headers=headers, json=variable_data)
        result = response.json()
        if result.get("code") == 0:
            print(f"✅ 添加变量 '{var_name}' 成功")
            return True
        else:
            print(f"❌ 添加变量 '{var_name}' 失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 添加变量 '{var_name}' 请求失败: {e}")
        return False

def main():
    print("="*60)
    print("添加12个变量配置")
    print("="*60)
    
    # 登录
    token = login()
    if not token:
        return
    
    # 获取设备ID
    dev_id = get_device_list(token)
    if not dev_id:
        return
    
    print("\n" + "="*60)
    print("开始添加变量...")
    print("="*60)
    
    # 12个变量配置
    variables = [
        # 0区（线圈）- 布尔值
        {"name": "1", "data_type": "0", "modbus_type": "0", "addr": 0, "len": 1},
        {"name": "2", "data_type": "0", "modbus_type": "0", "addr": 8, "len": 1},
        {"name": "3", "data_type": "0", "modbus_type": "0", "addr": 16, "len": 1},
        {"name": "4", "data_type": "0", "modbus_type": "0", "addr": 24, "len": 1},
        
        # 1区（离散输入）- 布尔值
        {"name": "5", "data_type": "0", "modbus_type": "1", "addr": 0, "len": 1},
        {"name": "6", "data_type": "0", "modbus_type": "1", "addr": 8, "len": 1},
        {"name": "7", "data_type": "0", "modbus_type": "1", "addr": 16, "len": 1},
        {"name": "8", "data_type": "0", "modbus_type": "1", "addr": 32, "len": 1},
        
        # 3区（输入寄存器）- 字符串
        {"name": "9", "data_type": "5", "modbus_type": "3", "addr": 0, "len": 7, "string_len": 13},
        {"name": "10", "data_type": "5", "modbus_type": "3", "addr": 13, "len": 7, "string_len": 13},
        
        # 4区（保持寄存器）- 字符串
        {"name": "11", "data_type": "5", "modbus_type": "4", "addr": 0, "len": 7, "string_len": 13},
        {"name": "12", "data_type": "5", "modbus_type": "4", "addr": 13, "len": 7, "string_len": 13},
    ]
    
    success_count = 0
    for var in variables:
        if add_variable(
            token=token,
            dev_id=dev_id,
            var_name=var["name"],
            data_type=var["data_type"],
            modbus_type=var["modbus_type"],
            modbus_device=1,
            modbus_addr=var["addr"],
            data_len=var["len"],
            string_len=var.get("string_len", "")
        ):
            success_count += 1
    
    print("\n" + "="*60)
    print(f"✅ 完成！成功添加 {success_count}/{len(variables)} 个变量")
    print("="*60)

if __name__ == "__main__":
    main()
