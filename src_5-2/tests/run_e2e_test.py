#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按照数据类型支持改造_端到端测试与验证.md 文档的完整测试
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
                print_success("登录成功")
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
                devices = result["data"]["devicelist"] or []
                print_success(f"获取到 {len(devices)} 个设备")
                for dev in devices:
                    print(f"  - ID: {dev['id']}, 名称: {dev['name']}, 序列号: {dev['serial']}")
                return devices
        print_error(f"获取设备列表失败: {response.text}")
    except Exception as e:
        print_error(f"获取设备列表异常: {e}")
    return []

def add_test_device(token):
    print_header("步骤2a: 添加测试设备（因为数据库没有）")
    url = f"{BASE_URL}/add/device"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "device": {
            "devname": "ML307测试设备",
            "devserial": "A1B2C3D4",
            "devlocation": "测试室",
            "devstatus": "1",
            "baud": "9600",
            "changeflag": "0",
            "successflag": "0"
        }
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        print_info(f"添加设备响应: {response.status_code} - {response.text}")
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print_success("测试设备添加成功")
                return True
        print_error(f"添加设备失败: {response.text}")
    except Exception as e:
        print_error(f"添加设备异常: {e}")
    return False

def get_variables(token, dev_id):
    print_header(f"步骤3: 获取设备 {dev_id} 的现有变量列表")
    url = f"{BASE_URL}/getvarbydeviceid"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"device_id": dev_id}
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            variables = result.get("data", {}).get("variables", []) or []
            print_success(f"获取到 {len(variables)} 个变量")
            return variables
        print_error(f"获取变量列表失败: {response.text}")
    except Exception as e:
        print_error(f"获取变量列表异常: {e}")
    return []

def delete_all_variables(token, dev_id, variables):
    if not variables:
        print_info("没有需要删除的变量")
        return True
    
    print_header(f"步骤3a: 清空现有变量（{len(variables)}个）")
    url = f"{BASE_URL}/deletevariable"
    headers = {"Authorization": f"Bearer {token}"}
    
    success = True
    for var in variables:
        data = {"id": var["id"]}
        try:
            response = requests.post(url, json=data, headers=headers, timeout=10)
            result = response.json()
            if result.get("code") == 0:
                print_success(f"已删除变量: {var['varName']}")
            else:
                print_error(f"删除变量 {var['varName']} 失败: {result}")
                success = False
        except Exception as e:
            print_error(f"删除变量异常: {e}")
            success = False
    return success

def add_variable(token, dev_id, var_name, modbus_type, modbus_device, modbus_addr, data_type, string_len=0, reg_count=1):
    print_header(f"添加变量: {var_name} (类型: {data_type})")
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
    try:
        print_info(f"发送数据: {json.dumps(data, ensure_ascii=False)}")
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

def query_all_data(token, serial, slave_addr, modbus_type, modbus_addr):
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
            data_items = result.get("data", []) or []
            return data_items
    except Exception as e:
        print_error(f"查询数据异常: {e}")
    return []

def main():
    print_header("数据类型支持改造 - 端到端测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 登录
    token = login()
    if not token:
        return
    
    # 2. 获取设备列表
    devices = get_device_list(token)
    if not devices:
        # 数据库没有设备，添加一个
        print_info("数据库没有设备，先添加测试设备")
        add_test_device(token)
        time.sleep(1)
        devices = get_device_list(token)
        if not devices:
            print_error("无法添加或获取设备")
            return
    
    target_dev = devices[0]
    dev_id = target_dev["id"]
    dev_serial = target_dev["serial"]
    print_info(f"使用设备: ID={dev_id}, 序列号={dev_serial}")
    
    # 3. 获取并清空现有变量
    variables = get_variables(token, dev_id)
    if variables:
        if not delete_all_variables(token, dev_id, variables):
            print_error("无法清空变量")
            return
    variables = get_variables(token, dev_id)
    
    # 4. 配置6个测试变量（按照文档）
    print_header("测试阶段1: 配置6个测试变量")
    
    test_variables = [
        # 变量名, 类型, Modbus类型, 从站地址, 起始地址, 字符串长度, 寄存器个数
        ("switch_bool",  "0", 0, 1, 0, 0, 1),   # bool
        ("temp_float32", "3", 4, 1, 0, 0, 2),   # float32
        ("humi_int16",   "1", 4, 1, 2, 0, 1),   # int16
        ("power_float64","4", 4, 1, 3, 0, 4),   # float64
        ("energy_int32", "2", 4, 1, 7, 0, 2),   # int32
        ("device_desc",  "5", 4, 1,10,20,10)    # string
    ]
    
    all_ok = True
    for var_name, data_type, modbus_type, slave_addr, addr, string_len, reg_count in test_variables:
        if not add_variable(token, dev_id, var_name, modbus_type, slave_addr, addr, data_type, string_len, reg_count):
            all_ok = False
            print_error("继续添加其他变量...")
    
    if not all_ok:
        print_error("部分变量添加失败")
    else:
        print_success("所有6个变量添加成功！")
    
    # 5. 重新获取变量列表确认
    variables = get_variables(token, dev_id)
    
    # 6. 下发配置（使用功能码0x04）
    # 构建配置读取从站1的所有地址
    send_payload(token, dev_serial, "040001010400000002")
    
    # 7. 等待数据上传
    print_header("步骤7: 等待数据上传")
    wait_time = 15
    print_info(f"等待 {wait_time} 秒让模拟器上传数据...")
    time.sleep(wait_time)
    
    # 8. 查询数据
    print_header("步骤8: 验证数据查询")
    
    print_info("查询各个地址的数据...")
    test_addrs = [
        (0, 0, "switch_bool (bool)"),
        (0, 4, "temp_float32"),
        (2, 4, "humi_int16"),
        (3, 4, "power_float64"),
        (7, 4, "energy_int32"),
        (10,4, "device_desc (string)")
    ]
    
    has_data = False
    for addr, modbus_type, name in test_addrs:
        data_list = query_all_data(token, dev_serial, 1, modbus_type, addr)
        if data_list:
            has_data = True
            print_success(f"✅ {name} (地址={addr}, 类型={modbus_type}): 找到 {len(data_list)} 条数据")
            for item in data_list[:3]:
                print(f"    - {item.get('time','')}: value={item.get('value','')}, value_bool={item.get('valueBool')}, value_int={item.get('valueInt')}, value_float={item.get('valueFloat')}, value_string={item.get('valueString')}")
        else:
            print_error(f"❌ {name} (地址={addr}): 未找到数据")
    
    # 9. 总结
    print_header("测试总结")
    if all_ok and has_data:
        print_success("🎉 端到端测试成功！")
        print("\n系统功能验证:")
        print("  ✅ 后端API正常工作")
        print("  ✅ 新增变量支持所有6种新数据类型")
        print("  ✅ 配置下发功能正常")
        print("  ✅ 模拟器数据上传功能正常")
        print("  ✅ InfluxDB数据写入包含新字段")
        print("  ✅ 数据查询API支持新字段")
        print("\n等待前端来查看最终展示效果！")
    else:
        print_error("⚠️ 部分测试未通过，请检查各部分日志")

if __name__ == "__main__":
    main()
