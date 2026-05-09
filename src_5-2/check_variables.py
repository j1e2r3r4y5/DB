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
            return token
        else:
            print(f"❌ 登录失败: {result}")
            return None
    except Exception as e:
        print(f"❌ 登录请求失败: {e}")
        return None


def get_variables(token, dev_id):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(f"{BASE_URL}/getvariables", headers=headers, json={"devID": dev_id})
        result = response.json()
        if result.get("code") == 0:
            variables = result.get("data", {}).get("variables", [])
            return variables
        else:
            print(f"❌ 获取变量列表失败: {result}")
            return []
    except Exception as e:
        print(f"❌ 获取变量列表请求失败: {e}")
        return []


def update_variable(token, var_id, new_name, new_modbus_type, new_data_type, new_modbus_addr, new_modbus_device, new_string_len, new_data_len):
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "iD": var_id,
        "varName": new_name,
        "modbusType": new_modbus_type,
        "dataType": new_data_type,
        "modbusAddr": new_modbus_addr,
        "modbusDevice": new_modbus_device,
        "stringLen": str(new_string_len),
        "dataLen": str(new_data_len)
    }
    try:
        response = requests.post(f"{BASE_URL}/updatevariable", headers=headers, json=data)
        result = response.json()
        if result.get("code") == 0:
            print(f"✅ 更新变量 {new_name} 成功")
            return True
        else:
            print(f"❌ 更新变量失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 更新变量请求失败: {e}")
        return False


def get_device_list(token):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(f"{BASE_URL}/get-devicelist", headers=headers, json={})
        result = response.json()
        if result.get("code") == 0:
            devices = result.get("data", {}).get("devicelist", [])
            if devices:
                return devices[0]
        return None
    except Exception:
        return None


def main():
    print("="*60)
    print("检查并修复变量配置")
    print("="*60)
    
    token = login()
    if not token:
        return
    
    device = get_device_list(token)
    if not device:
        return
    
    variables = get_variables(token, device['id'])
    
    print("\n当前变量：")
    for v in variables:
        var_id = v.get('iD') or v.get('id')
        name = v.get('varName')
        modbus_type = v.get('modbusType')
        data_type = v.get('dataType')
        addr = v.get('modbusAddr')
        string_len = v.get('stringLen')
        data_len = v.get('dataLen') or v.get('data_len')
        print(f"  ID={var_id}, 名称={name}, 分区={modbus_type}, 类型={data_type}, 地址={addr}, 字符串长度={string_len}, 数据长度={data_len}")
    
    print("\n\n需要更新变量（如果需要）...")
    # 找到需要更新的变量：
    # 变量9-12 的字符串长度应该是13
    # 让我自动修复
    for v in variables:
        var_id = v.get('iD') or v.get('id')
        name = v.get('varName')
        if name in ['9', '10', '11', '12']:
            print(f"\n更新变量 {name}...")
            update_variable(
                token,
                var_id,
                name,
                v.get('modbusType'),
                v.get('dataType'),
                v.get('modbusAddr'),
                v.get('modbusDevice'),
                13,  # 字符串长度13字节
                7    # 数据长度7个寄存器
            )
    
    print("\n✅ 完成！")


if __name__ == "__main__":
    main()
