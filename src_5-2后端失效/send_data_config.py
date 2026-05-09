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
                return device['serial']
            else:
                print("❌ 没有找到设备")
                return None
        else:
            print(f"❌ 获取设备列表失败: {result}")
            return None
    except Exception as e:
        print(f"❌ 获取设备列表请求失败: {e}")
        return None

# 下发数据配置
def send_data_config(token, dev_serial):
    headers = {"Authorization": f"Bearer {token}"}
    
    # 根据 address_segments_final.txt 的配置
    # 合并相同站号和分区的变量
    entries = [
        # 0区线圈：地址0-24，共25个线圈（变量1-4）
        {
            "slaveAddr": 1,
            "dataType": 0,
            "startAddr": 0,
            "length": 25
        },
        # 1区离散输入：地址0-32，共33个（变量5-8）
        {
            "slaveAddr": 1,
            "dataType": 1,
            "startAddr": 0,
            "length": 33
        },
        # 3区输入寄存器：地址0-25，共26个寄存器（变量9-10，每个13个）
        {
            "slaveAddr": 1,
            "dataType": 3,
            "startAddr": 0,
            "length": 26
        },
        # 4区保持寄存器：地址0-25，共26个寄存器（变量11-12，每个13个）
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
    print("下发数据配置到模拟器")
    print("="*60)
    
    # 登录
    token = login()
    if not token:
        return
    
    # 获取设备序列号
    dev_serial = get_device_list(token)
    if not dev_serial:
        return
    
    # 下发数据配置
    send_data_config(token, dev_serial)
    
    print("\n" + "="*60)
    print("完成！")
    print("="*60)

if __name__ == "__main__":
    main()
