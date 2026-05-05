
import requests
import json

BASE_URL = 'http://127.0.0.1:8000'

# Step 1: Login
login_url = f"{BASE_URL}/login"
login_payload = {"username": "admin", "password": "1"}
login_resp = requests.post(login_url, json=login_payload)
token = login_resp.json().get('data', {}).get('token')
headers = {"Authorization": f"Bearer {token}"}

# Step 2: Get All Variables using getvariables
print("=== Testing getvariables ===")
getvar_url = f"{BASE_URL}/getvariables"
getvar_resp = requests.post(getvar_url, headers=headers, json={})
print(f"Status: {getvar_resp.status_code}")
print(json.dumps(getvar_resp.json(), indent=2, ensure_ascii=False))

# Step 3: Let's also test getvarbydeviceid with different parameters
print("\n=== Testing getvarbydeviceid with different params ===")
test_params = [
    {"Devid": 30},
    {"deviceId": 30},
    {"device_id": 30},
    {"id": 30},
]

for params in test_params:
    getvar_resp = requests.post(getvar_url.replace('getvariables', 'getvarbydeviceid'), headers=headers, json=params)
    print(f"\nParams: {params}")
    print(f"Status: {getvar_resp.status_code}")
    print(json.dumps(getvar_resp.json(), indent=2, ensure_ascii=False))
