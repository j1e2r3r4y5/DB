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
            print(f"✅ 登录成功")
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
                print(f"✅ 找到设备: {device['name']} ({device['serial']})")
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
    
    # 正确的合并配置！
    entries = [
        # 0区线圈：地址0-24（25个线圈，覆盖变量1-4）
        {
            "slaveAddr": 1,
            "dataType": 0,
            "startAddr": 0,
            "length": 25
        },
        # 1区离散输入：地址0-32（33个，覆盖变量5-8）
        {
            "slaveAddr": 1,
            "dataType": 1,
            "startAddr": 0,
            "length": 33
        },
        # 3区输入寄存器：地址0-25（26个寄存器 = 52字节，覆盖变量9-10）
        {
            "slaveAddr": 1,
            "dataType": 3,
            "startAddr": 0,
            "length": 26
        },
        # 4区保持寄存器：地址0-25（26个寄存器 = 52字节，覆盖变量11-12）
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
    
    print(f"\n📋 配置: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(f"{BASE_URL}/sendcod/data-config", headers=headers, json=data)
        result = response.json()
        if result.get("code") == 0:
            print(f"✅ 发送数据配置成功！")
            return True
        else:
            print(f"❌ 发送数据配置失败: {result}")
            return False
    except Exception as e:
        print(f"❌ 发送请求失败: {e}")
        return False


def main():
    print("=" * 60)
    print("重新发送合并后的数据配置")
    print("=" * 60)
    
    token = login()
    if not token:
        return
    
    device = get_device_list(token)
    if not device:
        return
    
    send_correct_data_config(token, device['serial'])
    
    print("\n" + "=" * 60)
    print("✅ 完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
