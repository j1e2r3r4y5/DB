
import requests
import json

BASE_URL = 'http://127.0.0.1:8000'

# Step 1: Login
login_url = f"{BASE_URL}/login"
login_payload = {"username": "admin", "password": "1"}
login_resp = requests.post(login_url, json=login_payload)
print("Login Resp:", login_resp.status_code)
print(json.dumps(login_resp.json(), indent=2, ensure_ascii=False))
token = login_resp.json().get('data', {}).get('token')
print("Token:", token)

headers = {"Authorization": f"Bearer {token}"}

# Step 2: Get Device List
devlist_url = f"{BASE_URL}/get-devicelist"
devlist_resp = requests.post(devlist_url, headers=headers, json={})
print("\nDevice List Resp:", devlist_resp.status_code)
print(json.dumps(devlist_resp.json(), indent=2, ensure_ascii=False))

# Step 3: Get Variables by Device ID (30)
getvar_url = f"{BASE_URL}/getvarbydeviceid"
getvar_payload = {"Devid": 30}
getvar_resp = requests.post(getvar_url, headers=headers, json=getvar_payload)
print("\nVariables by Device ID Resp:", getvar_resp.status_code)
print(json.dumps(getvar_resp.json(), indent=2, ensure_ascii=False))

# Step 4: Downpayload (Config Down)
downpayload_url = f"{BASE_URL}/payload"
downpayload_payload = {"Devid": 30}
downpayload_resp = requests.post(downpayload_url, headers=headers, json=downpayload_payload)
print("\nConfig Down Resp:", downpayload_resp.status_code)
print(json.dumps(downpayload_resp.json(), indent=2, ensure_ascii=False))
