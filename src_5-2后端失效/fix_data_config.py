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


def send_correct_data_config(token, dev_serial):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 根据 address_segments_final.txt 的正确配置：
    # 0区线圈: 0-24 (变量1-4，共25位)
    # 1区离散输入: 0-32 (变量5-8，共33位)
    # 3区输入寄存器: 0-25 (变量9-10，共26个寄存器 = 52字节)
    # 4区保持寄存器: 0-25 (变量11-12，共26个寄存器 = 52字节)
    entries = [
        {
            "slaveAddr": 1,
            "dataType": 0,
            "startAddr": 0,
            "length": 25
        },
        {
            "slaveAddr": 1,
            "dataType": 1,
            "startAddr": 0,
            "length": 33
        },
        {
            "slaveAddr": 1,
            "dataType": 3,
            "startAddr": 0,
            "length": 26
        },
        {
            "slaveAddr": 1,
            "dataType": 4,
            "startAddr": 0,
            "length": 26
        }
    ]
    
    data = {
        "devSerial": dev_serial,
        "entries": entries
    }
    
    print(f"\n📋 准备下发修正后的配置: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
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
    print("修正数据配置")
    print("="*60)
    
    # 登录
    token = login()
    if not token:
        return
    
    # 获取设备
    device = get_device_list(token)
    if not device:
        return
    
    # 下发正确的数据配置
    send_correct_data_config(token, device['serial'])
    
    print("\n" + "="*60)
    print("✅ 配置已修正！")
    print("="*60)
    print("\n等待模拟器下次上报数据（约30秒）...")


if __name__ == "__main__":
    main()
