#!/usr/bin/env python3
import requests
import json
import time

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
            print(f"✅ 登录成功，token: {token[:20]}...")
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
                print(f"✅ 找到设备: ID={device['id']}, 名称={device['name']}, 序列号={device['serial']}")
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
            print(f"✅ 找到 {len(variables)} 个变量:")
            for v in variables:
                var_id = v.get('iD') or v.get('id')
                print(f"  - ID: {var_id}, 名称: {v.get('varName')}, 类型: {v.get('dataType')}, 分区: {v.get('modbusType')}, 地址: {v.get('modbusAddr')}")
            return variables
        else:
            print(f"❌ 获取变量列表失败: {result}")
            return []
    except Exception as e:
        print(f"❌ 获取变量列表请求失败: {e}")
        return []


def send_data_config(token, dev_serial, variables):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 按照分区和地址合并变量
    entries = []
    
    # 0区线圈
    coil_vars = [v for v in variables if str(v.get('modbusType')) == '0']
    if coil_vars:
        addrs = sorted([int(v.get('modbusAddr')) for v in coil_vars])
        entries.append({
            "slaveAddr": int(coil_vars[0].get('modbusDevice')),
            "dataType": 0,
            "startAddr": addrs[0],
            "length": (addrs[-1] - addrs[0]) + 1
        })
    
    # 1区离散输入
    discrete_vars = [v for v in variables if str(v.get('modbusType')) == '1']
    if discrete_vars:
        addrs = sorted([int(v.get('modbusAddr')) for v in discrete_vars])
        entries.append({
            "slaveAddr": int(discrete_vars[0].get('modbusDevice')),
            "dataType": 1,
            "startAddr": addrs[0],
            "length": (addrs[-1] - addrs[0]) + 1
        })
    
    # 3区输入寄存器
    input_reg_vars = [v for v in variables if str(v.get('modbusType')) == '3']
    if input_reg_vars:
        addrs = sorted([int(v.get('modbusAddr')) for v in input_reg_vars])
        entries.append({
            "slaveAddr": int(input_reg_vars[0].get('modbusDevice')),
            "dataType": 3,
            "startAddr": addrs[0],
            "length": (addrs[-1] - addrs[0] + 1) + 1
        })
    
    # 4区保持寄存器
    holding_reg_vars = [v for v in variables if str(v.get('modbusType')) == '4']
    if holding_reg_vars:
        addrs = sorted([int(v.get('modbusAddr')) for v in holding_reg_vars])
        entries.append({
            "slaveAddr": int(holding_reg_vars[0].get('modbusDevice')),
            "dataType": 4,
            "startAddr": addrs[0],
            "length": (addrs[-1] - addrs[0] + 1) + 1
        })
    
    data = {
        "devSerial": dev_serial,
        "entries": entries
    }
    
    print(f"\n📋 准备下发配置: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(f"{BASE_URL}/sendcod/data-config", headers=headers, json=data)
        result = response.json()
        if result.get("code") == 0:
            print(f"✅ 下发数据配置成功！")
            return True
        else:
            print(f"❌ 下发数据配置失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 下发数据配置请求失败: {e}")
        return False


def main():
    print("="*60)
    print("完成部署配置")
    print("="*60)
    
    # 登录
    token = login()
    if not token:
        return
    
    # 获取设备
    device = get_device_list(token)
    if not device:
        return
    
    # 获取变量列表
    variables = get_variables(token, device['id'])
    if not variables:
        return
    
    # 下发数据配置
    send_data_config(token, device['serial'], variables)
    
    print("\n" + "="*60)
    print("✅ 配置完成！")
    print("="*60)
    print("\n现在请在前端：")
    print("1. 访问 http://localhost:4325/")
    print("2. 在'变量管理'页面，选中所有12个变量")
    print("3. 点击'下发'按钮")
    print("4. 然后在'数据'页面查看实时数据")
    print("\n等待几秒让模拟器上报数据...")
    time.sleep(5)
    print("\n✅ 全部完成！")


if __name__ == "__main__":
    main()
