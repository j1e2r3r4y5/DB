
import requests
import json
import time

BASE_URL = "http://localhost:8000"
token = None

print("=" * 50)
print("第一步：登录获取token")
print("=" * 50)

# 登录
login_data = {"username": "admin", "password": "1"}
login_response = requests.post(f"{BASE_URL}/login", json=login_data)
print(f"登录响应状态码: {login_response.status_code}")
login_result = login_response.json()
print(f"登录结果: {json.dumps(login_result, indent=2, ensure_ascii=False)}")

if login_result.get("code") == 0:
    token = login_result["data"]["token"]
    print(f"✅ 登录成功，获取到token")
    headers = {"Authorization": f"Bearer {token}"}
else:
    print("❌ 登录失败！")
    exit(1)

print("\n" + "=" * 50)
print("第二步：获取设备列表")
print("=" * 50)

# 获取设备列表
devlist_response = requests.post(f"{BASE_URL}/get-devicelist", json={}, headers=headers)
print(f"获取设备列表状态码: {devlist_response.status_code}")
devlist_result = devlist_response.json()
print(f"设备列表: {json.dumps(devlist_result, indent=2, ensure_ascii=False)}")

device_id = None
device_sn = None
if devlist_result.get("code") == 0:
    devices = devlist_result.get("data", {}).get("devicelist", [])
    if devices:
        device_id = devices[0]["id"]
        device_sn = devices[0]["serial"]
        print(f"✅ 找到设备 ID: {device_id}, SN: {device_sn}")
    else:
        print("❌ 没有找到设备")
        exit(1)

print("\n" + "=" * 50)
print("第三步：添加变量")
print("=" * 50)

# 添加一个温度变量
add_var_data = {
    "Devid": device_id,
    "Varname": "温度测试",
    "Datatype": 1,  # 整数
    "Modtype": 4,  # 保持寄存器
    "Moddevice": 1,  # 从站1
    "Modaddr": 0,  # 地址0
    "Regcount": 1,  # 寄存器数量
    "Scale": 0.1,  # 缩放因子
    "Offset": 0,  # 偏移
    "Byteorder": "ABCD",
    "Unit": "℃",
    "Datalen": 2
}
add_var_response = requests.post(f"{BASE_URL}/addvariable", json=add_var_data, headers=headers)
print(f"添加变量状态码: {add_var_response.status_code}")
add_var_result = add_var_response.json()
print(f"添加变量结果: {json.dumps(add_var_result, indent=2, ensure_ascii=False)}")

print("\n" + "=" * 50)
print("第四步：获取变量列表，确认添加成功")
print("=" * 50)

get_var_data = {"deviceId": device_id}
get_var_response = requests.post(f"{BASE_URL}/getvarbydeviceid", json=get_var_data, headers=headers)
print(f"获取变量状态码: {get_var_response.status_code}")
get_var_result = get_var_response.json()
print(f"变量列表: {json.dumps(get_var_result, indent=2, ensure_ascii=False)}")

print("\n" + "=" * 50)
print("第五步：下发数据配置（功能码0x04）")
print("=" * 50)

# 构建下发配置的 payload
# 我们手动构建一个 0x04 配置包
# 结构：04 (功能码) + 0001 (数据组数) + 01 (从站) + 04 (类型) + 0000 (起始地址) + 0002 (数量)
code_hex = "040001010400000002"

down_payload_data = {"serial": device_sn, "code": code_hex}
down_payload_response = requests.post(f"{BASE_URL}/payload", json=down_payload_data, headers=headers)
print(f"下发配置状态码: {down_payload_response.status_code}")
down_payload_result = down_payload_response.json()
print(f"下发配置结果: {json.dumps(down_payload_result, indent=2, ensure_ascii=False)}")

print("\n" + "=" * 50)
print("第六步：等待5秒，让模拟器处理配置并上传数据")
print("=" * 50)

time.sleep(5)

print("\n" + "=" * 50)
print("第七步：检查后端日志（通过模拟接口查询数据）")
print("=" * 50)

print("\n✅ 全流程测试完成！")
print("现在请查看后端终端的日志，看看有没有收到数据上传！")
