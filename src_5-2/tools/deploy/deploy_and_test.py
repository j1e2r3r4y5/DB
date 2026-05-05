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
        print(f"登录响应状态: {response.status_code}")
        print(f"登录响应内容: {response.text[:200]}")
        result = response.json()
        if result.get("code") == 0 or result.get("code") == "0" or (result.get("data") and result.get("data").get("token")):
            token = result.get("data", {}).get("token", "")
            if not token:
                token = result.get("token", "")
            print(f"✅ 登录成功！Token: {token[:20]}...")
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
        print(f"获取设备响应: {response.text[:300]}")
        result = response.json()
        if result.get("code") == 0 or result.get("code") == "0" or result.get("data"):
            devices = result.get("data", {}).get("devicelist", [])
            if not devices:
                devices = result.get("devicelist", [])
            print(f"✅ 找到 {len(devices)} 个设备")
            for d in devices:
                print(f"  - 设备ID: {d.get('id')}, 名称: {d.get('name') or d.get('Devname')}")
            return devices
        else:
            print(f"❌ 获取设备列表失败: {result}")
            return []
    except Exception as e:
        print(f"❌ 获取设备列表异常: {e}")
        return []


def get_variables(dev_id):
    """获取变量列表"""
    url = f"{BASE_URL}/getvarbydeviceid"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    data = {"device_id": dev_id}
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        print(f"获取变量响应: {response.text[:300]}")
        result = response.json()
        if result.get("code") == 0 or result.get("code") == "0" or result.get("data"):
            variables = result.get("data", {}).get("variables", [])
            if not variables:
                variables = result.get("variables", [])
            print(f"✅ 设备 {dev_id} 有 {len(variables)} 个变量")
            for v in variables:
                print(f"  - 变量ID: {v.get('iD') or v.get('id')}, 名称: {v.get('varName')}")
            return variables
        else:
            print(f"❌ 获取变量列表失败: {result}")
            return []
    except Exception as e:
        print(f"❌ 获取变量列表异常: {e}")
        return []


def delete_variable(var_id):
    """删除变量"""
    url = f"{BASE_URL}/deletevariable"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    data = {"id": {"iD": var_id}}
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        result = response.json()
        if result.get("code") == 0 or result.get("code") == "0" or "成功" in str(result):
            print(f"✅ 删除变量 {var_id} 成功")
            return True
        else:
            print(f"❌ 删除变量 {var_id} 失败: {result}")
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


def send_config(dev_id):
    """下发配置"""
    url = f"{BASE_URL}/payload"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    data = {"idlist": [dev_id]}
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        result = response.json()
        if result.get("code") == 0 or result.get("code") == "0" or "成功" in str(result):
            print(f"✅ 下发配置成功！")
            return True
        else:
            print(f"❌ 下发配置失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 下发配置异常: {e}")
        return False


def main():
    print("=" * 60)
    print("       🚀 数据类型支持改造 - 完整部署测试")
    print("=" * 60)
    
    # 1. 登录
    if not login():
        return
    
    print("\n" + "-" * 60)
    print("📋 第二步：清理旧变量")
    print("-" * 60)
    
    # 获取设备列表
    devices = get_device_list()
    if not devices:
        print("❌ 没有找到设备！")
        return
    
    # 取第一个设备
    dev_id = devices[0]["id"]
    print(f"\n📌 使用设备ID: {dev_id}")
    
    # 获取该设备的所有变量
    variables = get_variables(dev_id)
    
    # 删除所有变量
    if variables:
        print(f"\n🗑️ 开始删除 {len(variables)} 个变量...")
        for v in variables:
            var_id = v.get("iD") or v.get("id")
            delete_variable(var_id)
            time.sleep(0.1)
        print("\n✅ 所有旧变量已删除！")
    else:
        print("\n✅ 没有旧变量需要删除！")
    
    print("\n" + "-" * 60)
    print("📝 第三步：添加6个新测试变量")
    print("-" * 60)
    
    # 定义要添加的变量
    new_variables = [
        # 变量名, 数据类型(0=bool,1=int16,2=int32,3=float32,4=float64,5=string), 
        # Modbus类型(0=线圈,1=离散输入,2=输入寄存器,3=保持寄存器), 
        # 从站地址, 起始地址, 寄存器数量, 字符串长度
        ("switch_bool", 0, 0, 1, 0, 1, 0),
        ("temp_float32", 3, 3, 1, 0, 2, 0),
        ("humi_int16", 1, 3, 1, 2, 1, 0),
        ("power_float64", 4, 3, 1, 3, 4, 0),
        ("energy_int32", 2, 3, 1, 7, 2, 0),
        ("device_desc", 5, 3, 1, 10, 10, 20)
    ]
    
    for var_name, data_type, modbus_type, slave, addr, reg_len, str_len in new_variables:
        add_variable(dev_id, var_name, data_type, modbus_type, slave, addr, reg_len, str_len)
        time.sleep(0.2)
    
    print("\n" + "-" * 60)
    print("📤 第四步：下发配置")
    print("-" * 60)
    
    send_config(dev_id)
    
    print("\n" + "=" * 60)
    print("       ✅ 部署测试完成！")
    print("=" * 60)
    print("\n📊 现在可以查看：")
    print("   1. 数据展示页面 - 查看实时数据")
    print("   2. 后端日志 - 查看数据解析和InfluxDB写入")
    print("   3. InfluxDB - 查看存储的数据")
    print("\n🌐 前端地址: http://localhost:4326")


if __name__ == "__main__":
    main()
