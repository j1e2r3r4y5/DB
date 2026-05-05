#!/usr/bin/env python3
import requests
import json
import time

# 配置
BASE_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "1"

# 全局变量
token = ""


def login():
    """登录获取token"""
    global token
    url = f"{BASE_URL}/login"
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        if result.get("code") == 0 or (result.get("data") and result.get("data").get("token")):
            token = result.get("data", {}).get("token", "")
            print(f"✅ 登录成功！")
            return True
        else:
            print(f"❌ 登录失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return False


def get_device_list():
    """获取设备列表"""
    url = f"{BASE_URL}/get-devicelist"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        response = requests.post(url, headers=headers, json={}, timeout=10)
        result = response.json()
        if result.get("code") == 0 or result.get("code") == "0" or result.get("data"):
            devices = result.get("data", {}).get("devicelist", [])
            if not devices:
                devices = result.get("devicelist", [])
            return devices
        else:
            print(f"❌ 获取设备列表失败: {result}")
            return []
    except Exception as e:
        print(f"❌ 获取设备列表异常: {e}")
        return []


def get_variables():
    """获取所有变量列表"""
    url = f"{BASE_URL}/getvariables"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    data = {}
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        result = response.json()
        if result.get("code") == 0 or result.get("code") == "0" or result.get("data"):
            variables = result.get("data", {}).get("variables", [])
            if not variables:
                variables = result.get("variables", [])
            return variables
        else:
            return []
    except Exception as e:
        print(f"❌ 获取变量异常: {e}")
        return []


def delete_variable(var):
    """删除变量"""
    url = f"{BASE_URL}/deletevariable"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    data = {
        "In": {
            "id": var.get("iD") or var.get("id"),
            "devID": var.get("devID"),
            "varName": var.get("varName"),
            "dataType": var.get("dataType"),
            "modbusType": var.get("modbusType"),
            "modbusDevice": var.get("modbusDevice"),
            "modbusAddr": var.get("modbusAddr"),
            "data_len": var.get("data_len") or var.get("dataLen"),
            "stringLen": var.get("stringLen"),
        }
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        result = response.json()
        if result.get("code") == 0 or result.get("code") == "0" or "成功" in str(result):
            return True
        else:
            return False
    except Exception as e:
        print(f"❌ 删除变量异常: {e}")
        return False


def add_variable(dev_id, var_name, data_type, modbus_type, modbus_device, modbus_addr, data_len, string_len=0):
    """添加变量"""
    url = f"{BASE_URL}/addvariable"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    data = {
        "variable": {
            "devID": dev_id,
            "varName": var_name,
            "dataType": data_type,
            "modbusType": modbus_type,
            "modbusDevice": modbus_device,
            "modbusAddr": modbus_addr,
            "data_len": data_len,
            "stringLen": string_len,
            "decimalDigits": 0
        }
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        result = response.json()
        if result.get("code") == 0 or result.get("code") == "0" or "成功" in str(result):
            print(f"✅ 添加变量 {var_name} 成功")
            return True
        else:
            print(f"❌ 添加变量 {var_name} 失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 添加变量异常: {e}")
        return False


def main():
    print("=" * 60)
    print("        🚀 清空数据 & 添加中文变量")
    print("=" * 60)
    
    # 1. 登录
    if not login():
        return
    
    # 获取设备列表
    devices = get_device_list()
    if not devices:
        print("❌ 没有找到设备！")
        return
    
    dev_id = devices[0]["id"]
    print(f"\n📌 使用设备ID: {dev_id}")
    
    # 获取所有变量
    variables = get_variables()
    
    # 删除所有属于该设备的变量
    device_vars = [v for v in variables if str(v.get("devID")) == str(dev_id)]
    if device_vars:
        print(f"\n🗑️ 开始删除 {len(device_vars)} 个旧变量...")
        for v in device_vars:
            delete_variable(v)
            time.sleep(0.1)
        print("✅ 所有旧变量已删除！")
    else:
        print("\n✅ 没有旧变量需要删除！")
    
    print("\n" + "-" * 60)
    print("📝  添加中文变量（修正 Modbus 类型）")
    print("-" * 60)
    
    # 定义要添加的中文变量 - 修正 Modbus 类型
    new_variables = [
        # 变量名, 数据类型, Modbus类型, 从站地址, 起始地址, 寄存器数量, 字符串长度
        ("开关状态", 0, 0, 1, 0, 1, 0),          # 线圈
        ("温度数值", 3, 4, 1, 0, 2, 0),          # 保持寄存器
        ("湿度数值", 1, 4, 1, 2, 1, 0),          # 保持寄存器
        ("功率数值", 4, 4, 1, 3, 4, 0),          # 保持寄存器
        ("电能数值", 2, 4, 1, 7, 2, 0),          # 保持寄存器
        ("设备描述", 5, 4, 1, 10, 10, 20),       # 保持寄存器
    ]
    
    for var_name, data_type, modbus_type, slave, addr, reg_len, str_len in new_variables:
        add_variable(dev_id, var_name, data_type, modbus_type, slave, addr, reg_len, str_len)
        time.sleep(0.2)
    
    print("\n" + "=" * 60)
    print("        ✅ 变量添加完成！")
    print("=" * 60)
    print("\n📋 现在请执行：")
    print("1. 在前端设备管理页面，点击「配置下发」")
    print("2. 进入设备列表，点击「查看数据」")
    print("3. 验证所有变量数据正常显示！")


if __name__ == "__main__":
    main()

