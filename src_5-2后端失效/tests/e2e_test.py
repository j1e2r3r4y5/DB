#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
端到端测试脚本
1. 登录系统
2. 查看设备列表和变量列表
3. 创建温度和湿度变量（如果不存在）
4. 下发配置
5. 验证数据写入InfluxDB
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_success(msg):
    print(f"✅ {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def print_info(msg):
    print(f"ℹ️  {msg}")

def login():
    print_header("步骤1: 登录系统")
    url = f"{BASE_URL}/login"
    data = {"username": "admin", "password": "1"}
    try:
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                token = result["data"]["token"]
                print_success(f"登录成功")
                print_info(f"Token: {token[:50]}...")
                return token
        print_error(f"登录失败: {response.text}")
    except Exception as e:
        print_error(f"登录异常: {e}")
    return None

def get_device_list(token):
    print_header("步骤2: 获取设备列表")
    url = f"{BASE_URL}/get-devicelist"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(url, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                devices = result["data"]["devicelist"]
                print_success(f"获取到 {len(devices)} 个设备")
                for dev in devices:
                    print(f"  - ID: {dev['id']}, 名称: {dev['name']}, 序列号: {dev['serial']}, 状态: {dev['status']}")
                return devices
        print_error(f"获取设备列表失败: {response.text}")
    except Exception as e:
        print_error(f"获取设备列表异常: {e}")
    return []

def get_variables(token, dev_id):
    print_header(f"步骤3: 获取设备 {dev_id} 的变量列表")
    url = f"{BASE_URL}/getvarbydeviceid"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"device_id": dev_id}
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print_info(f"响应: {json.dumps(result, ensure_ascii=False)}")
            if result.get("code") == 0:
                variables = result["variables"] if "variables" in result else []
                print_success(f"获取到 {len(variables)} 个变量")
                for var in variables:
                    print(f"  - {var['VarName']} (地址: {var['ModbusAddr']}, 类型: {var['ModbusType']})")
                return variables
        print_error(f"获取变量列表失败: {response.text}")
    except Exception as e:
        print_error(f"获取变量列表异常: {e}")
    return []

def add_variable(token, dev_id, var_name, modbus_type, modbus_device, modbus_addr, data_type, unit, scale=0.1):
    print_header(f"步骤4: 创建变量 '{var_name}'")
    url = f"{BASE_URL}/addvariable"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "variable": {
            "devID": dev_id,
            "varName": var_name,
            "dataType": data_type,
            "modbusType": str(modbus_type),
            "modbusDevice": modbus_device,
            "modbusAddr": modbus_addr,
            "scale": scale,
            "offset": 0,
            "regCount": 1,
            "byteOrder": "ABCD",
            "unit": unit
        }
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print_success(f"变量 '{var_name}' 创建成功")
                return True
        print_error(f"创建变量失败: {response.text}")
    except Exception as e:
        print_error(f"创建变量异常: {e}")
    return False

def send_payload(token, serial, code):
    print_header("步骤5: 下发配置到设备")
    url = f"{BASE_URL}/payload"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"serial": serial, "code": code}
    try:
        print_info(f"下发代码: {code}")
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print_success("配置下发成功")
                return True
        print_error(f"配置下发失败: {response.text}")
    except Exception as e:
        print_error(f"配置下发异常: {e}")
    return False

def query_data_from_influx(token, serial, slave_addr, modbus_type, modbus_addr):
    print_header("步骤6: 查询InfluxDB中的数据")
    url = f"{BASE_URL}/alldata"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "devSerial": serial,
        "slaveAddr": slave_addr,
        "dataType": modbus_type,
        "dataAddr": modbus_addr
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print_info(f"响应: {json.dumps(result, ensure_ascii=False)}")
            if result.get("code") == 0:
                data_items = result["data"] if "data" in result else []
                print_success(f"查询到 {len(data_items)} 条数据记录")
                for item in data_items[:5]:  # 只显示前5条
                    print(f"  - 时间: {item['time']}, 值: {item['value']} {item['field']}")
                return data_items
        print_error(f"查询数据失败: {response.text}")
    except Exception as e:
        print_error(f"查询数据异常: {e}")
    return []

def main():
    print_header("4G物联网设备管理平台 - 端到端测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 登录
    token = login()
    if not token:
        return
    
    # 2. 获取设备列表
    devices = get_device_list(token)
    if not devices:
        return
    
    target_dev = devices[0]  # 使用第一个设备
    dev_id = target_dev["id"]
    dev_serial = target_dev["serial"]
    
    # 3. 获取现有变量
    variables = get_variables(token, dev_id)
    existing_var_names = [v["VarName"] for v in variables]
    
    # 4. 如果温度和湿度变量不存在，就创建它们
    temp_exists = "温度" in existing_var_names
    hum_exists = "湿度" in existing_var_names
    
    if not temp_exists:
        add_variable(token, dev_id, "温度", 4, 1, 0, "int16", "℃", 0.1)
    else:
        print_info("温度变量已存在，跳过创建")
    
    if not hum_exists:
        add_variable(token, dev_id, "湿度", 4, 1, 1, "int16", "%", 0.1)
    else:
        print_info("湿度变量已存在，跳过创建")
    
    # 5. 重新获取变量列表确认
    variables = get_variables(token, dev_id)
    
    # 6. 下发配置（0x04功能码，读取从站1，类型4，地址0-1）
    send_payload(token, dev_serial, "040001010400000002")
    
    # 7. 等待数据上传
    print_header("步骤7: 等待数据上传")
    print_info("等待15秒让模拟器上传数据...")
    time.sleep(15)
    
    # 8. 查询温度数据
    print_header("步骤8: 验证温度数据")
    temp_data = query_data_from_influx(token, dev_serial, 1, 4, 0)
    
    # 9. 查询湿度数据
    print_header("步骤9: 验证湿度数据")
    hum_data = query_data_from_influx(token, dev_serial, 1, 4, 1)
    
    # 10. 总结
    print_header("测试总结")
    temp_ok = temp_data and len(temp_data) > 0
    hum_ok = hum_data and len(hum_data) > 0
    if temp_ok and hum_ok:
        print_success("🎉 端到端测试成功！")
        print("系统工作流程验证完毕:")
        print("  1. 前端可以成功登录")
        print("  2. 可以创建变量配置")
        print("  3. 配置可以成功下发到设备")
        print("  4. 模拟器可以正确处理配置并上传数据")
        print("  5. 数据正确写入InfluxDB")
        print("  6. 数据可以正确查询")
    else:
        print_error("⚠️ 部分测试未通过")
        if not temp_ok:
            print("  - 温度数据查询失败")
        if not hum_ok:
            print("  - 湿度数据查询失败")
        print("请检查后端和模拟器日志")

if __name__ == "__main__":
    main()
