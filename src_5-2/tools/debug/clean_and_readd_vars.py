#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def login():
    url = f"{BASE_URL}/login"
    data = {"username": "admin", "password": "1"}
    response = requests.post(url, json=data)
    result = response.json()
    return result['data']['token']

def get_device_list(token):
    url = f"{BASE_URL}/get-devicelist"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers)
    result = response.json()
    devices = result['data']['devicelist'] or []
    return devices

def get_variables(token, dev_id):
    url = f"{BASE_URL}/getvarbydeviceid"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"device_id": dev_id}
    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    variables = result.get("data", {}).get("variables", []) or []
    return variables

def delete_variable(token, var_id):
    url = f"{BASE_URL}/deletevariable"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"id": var_id}
    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    return result.get("code") == 0

def add_variable(token, dev_id, var_name, modbus_type, modbus_device, modbus_addr, data_type, string_len=0, reg_count=1):
    url = f"{BASE_URL}/addvariable"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "variable": {
            "devID": dev_id,
            "varName": var_name,
            "dataType": str(data_type),
            "modbusType": str(modbus_type),
            "modbusDevice": modbus_device,
            "modbusAddr": modbus_addr,
            "stringLen": string_len,
            "regCount": reg_count,
            "scale": 1.0,
            "offset": 0,
            "byteOrder": "ABCD",
            "unit": ""
        }
    }
    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    return result.get("code") == 0

def main():
    print("登录系统...")
    token = login()
    print(f"获取token: {token[:30]}...")
    
    print("\n获取设备列表...")
    devices = get_device_list(token)
    if not devices:
        print("没有设备！")
        return
    
    target_dev = devices[0]
    dev_id = target_dev["id"]
    print(f"使用设备: ID={dev_id}")
    
    print("\n获取当前变量...")
    variables = get_variables(token, dev_id)
    
    if variables:
        print(f"找到 {len(variables)} 个变量，删除中...")
        for v in variables:
            var_id = v["iD"]  # 注意这里是小写i
            success = delete_variable(token, var_id)
            if success:
                print(f"  已删除: {v['varName']}")
            else:
                print(f"  删除失败: {v['varName']}")
        time.sleep(0.5)
    
    print("\n重新添加变量...")
    
    test_variables = [
        ("switch_bool",  "0", 0, 1, 0, 0, 1),    # bool
        ("temp_float32", "3", 4, 1, 0, 0, 2),    # float32
        ("humi_int16",   "1", 4, 1, 2, 0, 1),    # int16
        ("power_float64","4", 4, 1, 3, 0, 4),    # float64
        ("energy_int32", "2", 4, 1, 7, 0, 2),    # int32
        ("device_desc",  "5", 4, 1,10,20,10)     # string
    ]
    
    all_success = True
    for var_name, data_type, modbus_type, slave, addr, str_len, reg in test_variables:
        success = add_variable(token, dev_id, var_name, modbus_type, slave, addr, data_type, str_len, reg)
        if success:
            print(f"✅ 添加成功: {var_name} (类型: {data_type})")
        else:
            print(f"❌ 添加失败: {var_name}")
            all_success = False
        time.sleep(0.2)
    
    print("\n验证变量是否同步到caching表...")
    variables_after = get_variables(token, dev_id)
    print(f"变量数量: {len(variables_after)}")
    
    if all_success and len(variables_after) == 6:
        print("\n🎉 所有变量添加成功！")
    else:
        print("\n⚠️  部分工作未完成")

if __name__ == "__main__":
    main()
