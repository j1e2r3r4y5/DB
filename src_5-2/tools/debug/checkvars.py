#!/usr/bin/env python3
import requests

BASE_URL = "http://localhost:8000"

def main():
    print("登录中...")
    login_res = requests.post(f"{BASE_URL}/login", json={"username": "admin", "password": "1"}).json()
    token = login_res.get("data", {}).get("token", "")
    print("Token:", token[:20], "...")
    print()

    print("获取设备列表...")
    devices_res = requests.post(f"{BASE_URL}/get-devicelist", headers={"Authorization": f"Bearer {token}"}).json()
    print("设备列表响应:", devices_res)
    devices = devices_res.get("data", {}).get("devicelist", [])
    if not devices:
        devices = devices_res.get("devicelist", [])
    print("设备数量:", len(devices))
    if devices:
        dev = devices[0]
        print("使用设备:", dev)
        dev_id = dev["id"]
        print("设备ID:", dev_id)

        print()
        print("获取变量列表...")
        vars_res = requests.post(
            f"{BASE_URL}/getvarbydeviceid",
            json={"device_id": dev_id},
            headers={"Authorization": f"Bearer {token}"}
        ).json()
        print("变量响应:", vars_res)
        vars_list = vars_res.get("data", {}).get("variables", [])
        if not vars_list:
            vars_list = vars_res.get("variables", [])
        print("变量数量:", len(vars_list))

        print()
        print("变量详情:")
        for v in vars_list:
            print(f"  名称: {v.get('VarName')}")
            print(f"  从站地址: {v.get('ModbusDevice')}")
            print(f"  Modbus类型: {v.get('ModbusType')}")
            print(f"  地址: {v.get('ModbusAddr')}")
            print(f"  数据类型: {v.get('DataType')}")
            print(f"  数据长度: {v.get('DataLen')}")
            print(f"  字符串长度: {v.get('StringLen')}")
            print("---")

if __name__ == "__main__":
    main()

