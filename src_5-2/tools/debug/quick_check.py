#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8000"

def login():
    url = f"{BASE_URL}/login"
    data = {"username": "admin", "password": "1"}
    response = requests.post(url, json=data)
    return response.json()['data']['token']

def get_variables_by_device(token, device_id):
    url = f"{BASE_URL}/getvarbydeviceid"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"deviceId": device_id}
    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    if result.get("code") == 0:
        return result.get("data", {}).get("variables", [])
    return []

def query_data(token, device_sn, slave_addr, modbus_type, data_addr):
    url = f"{BASE_URL}/dataquery"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "DevSerial": device_sn,
        "SlaveAddr": slave_addr,
        "ModbusType": modbus_type,
        "DataAddrs": [data_addr]
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()

def main():
    print("="*60)
    print("快速查询所有变量数据")
    print("="*60)
    
    token = login()
    print("✅ 登录成功")
    
    # 获取设备列表
    devlist_url = f"{BASE_URL}/get-devicelist"
    headers = {"Authorization": f"Bearer {token}"}
    devlist_response = requests.post(devlist_url, json={}, headers=headers)
    devices = devlist_response.json().get("data", {}).get("devicelist", [])
    if not devices:
        print("❌ 没有找到设备")
        return
    
    device = devices[0]
    device_id = device["id"]
    device_sn = device["serial"]
    print(f"✅ 设备: {device['name']} (SN: {device_sn})")
    
    # 获取变量
    variables = get_variables_by_device(token, device_id)
    print(f"✅ 找到 {len(variables)} 个变量\n")
    
    # 查询每个变量的数据
    for var in variables:
        print(f"--- 查询变量: {var['varName']} ---")
        print(f"  地址: {var['modbusAddr']}, 分区: {var['modbusType']}")
        
        result = query_data(
            token,
            device_sn,
            int(var['modbusDevice']),
            int(var['modbusType']),
            var['modbusAddr']
        )
        
        print(f"  完整结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        data_list = []
        if isinstance(result, list):
            data_list = result
        elif isinstance(result, dict):
            data_part = result.get("data")
            if isinstance(data_part, list):
                data_list = data_part
            elif isinstance(data_part, dict):
                data_list = data_part.get("data", [])
        
        print(f"  数据列表长度: {len(data_list)}")
        if data_list:
            latest = data_list[0] if isinstance(data_list[0], dict) else None
            if latest:
                print(f"    时间: {latest.get('time')}")
                print(f"    原始值: {latest.get('rawValue')}")
                print(f"    解析值: {latest.get('parsedValue')}")
                if latest.get('valueBool') is not None:
                    print(f"    布尔值: {latest.get('valueBool')}")
                if latest.get('valueInt') is not None:
                    print(f"    整数值: {latest.get('valueInt')}")
                if latest.get('valueFloat') is not None:
                    print(f"    浮点值: {latest.get('valueFloat')}")
                if latest.get('valueString') is not None:
                    print(f"    字符串: {latest.get('valueString')}")
            else:
                print(f"    ⚠️  数据格式异常")
        else:
            print(f"    ❌ 没有数据")
        print()

if __name__ == "__main__":
    main()
