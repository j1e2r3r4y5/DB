
import requests
import json

BASE_URL = "http://localhost:8000"

# 登录
login_response = requests.post(f"{BASE_URL}/login", json={"username": "admin", "password": "1"})
token = login_response.json()["data"]["token"]
headers = {"Authorization": f"Bearer {token}"}
print("✅ 登录成功")

# 查询数据
query_data = {
    "DevSerial": "A1B2C3D4",
    "SlaveAddr": 1,
    "ModbusType": 4,
    "DataAddrs": [0, 1]
}
query_response = requests.post(f"{BASE_URL}/dataquery", json=query_data, headers=headers)
print(f"\n✅ 查询结果：")
print(json.dumps(query_response.json(), indent=2, ensure_ascii=False))
