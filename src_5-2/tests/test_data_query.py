
import requests
import json
import time

BASE_URL = "http://localhost:8000"
token = None

print("=" * 50)
print("第一步：登录获取token")
print("=" * 50)

login_data = {"username": "admin", "password": "1"}
login_response = requests.post(f"{BASE_URL}/login", json=login_data)
print(f"登录响应状态码: {login_response.status_code}")
login_result = login_response.json()
print(f"登录结果: {json.dumps(login_result, indent=2, ensure_ascii=False)}")

if login_result.get("code") == 0:
    token = login_result["data"]["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ 登录成功")
else:
    print("❌ 登录失败！")
    exit(1)

print("\n" + "=" * 50)
print("第二步：获取设备列表")
print("=" * 50)

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
print("第三步：获取变量列表")
print("=" * 50)

get_var_data = {"device_id": device_id}
get_var_response = requests.post(f"{BASE_URL}/getvarbydeviceid", json=get_var_data, headers=headers)
print(f"获取变量状态码: {get_var_response.status_code}")
get_var_result = get_var_response.json()
print(f"变量列表: {json.dumps(get_var_result, indent=2, ensure_ascii=False)}")

variables = []
if get_var_result.get("code") == 0:
    variables = get_var_result.get("data", {}).get("variables", [])
    print(f"✅ 找到 {len(variables)} 个变量")

print("\n" + "=" * 50)
print("第四步：查询最新数据")
print("=" * 50)

for var in variables:
    print(f"\n查询变量 {var['varName']} (addr: {var['modbusAddr']})")
    query_data = {
        "DevSerial": device_sn,
        "SlaveAddr": var["modbusDevice"],
        "ModbusType": int(var["modbusType"]),
        "DataAddrs": [var["modbusAddr"]]
    }
    query_response = requests.post(f"{BASE_URL}/dataquery", json=query_data, headers=headers)
    print(f"查询状态码: {query_response.status_code}")
    print(f"查询结果: {json.dumps(query_response.json(), indent=2, ensure_ascii=False)}")

print("\n" + "=" * 50)
print("第五步：查询历史数据")
print("=" * 50)

if variables:
    var = variables[0]
    print(f"\n查询变量 {var['varName']} 的历史数据")
    history_data = {
        "DevSerial": device_sn,
        "SlaveAddr": var["modbusDevice"],
        "dataType": int(var["modbusType"]),  # 注意这里是 dataType
        "DataAddr": var["modbusAddr"],
        "modbusAddr": var["modbusAddr"]
    }
    history_response = requests.post(f"{BASE_URL}/alldata", json=history_data, headers=headers)
    print(f"历史数据查询状态码: {history_response.status_code}")
    print(f"历史数据结果: {json.dumps(history_response.json(), indent=2, ensure_ascii=False)}")
