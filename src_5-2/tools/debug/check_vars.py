import requests
import json

BASE_URL = "http://localhost:8000"

def login():
    url = f"{BASE_URL}/login"
    data = {"username": "admin", "password": "1"}
    response = requests.post(url, json=data)
    print(f"Login status: {response.status_code}")
    result = response.json()
    print(f"Login result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    return result['data']['token']

def get_variables(token, device_id=28):
    url = f"{BASE_URL}/getvarbydeviceid"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"DeviceId": device_id}
    response = requests.post(url, json=data, headers=headers)
    print(f"\nGet variables status: {response.status_code}")
    result = response.json()
    print(f"Get variables result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    return result

def get_device_list(token):
    url = f"{BASE_URL}/get-devicelist"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers)
    print(f"\nGet device list status: {response.status_code}")
    result = response.json()
    print(f"Get device list result: {json.dumps(result, indent=2, ensure_ascii=False)}")
    return result

if __name__ == "__main__":
    token = login()
    print(f"\nGot token: {token[:50]}...")
    get_device_list(token)
    get_variables(token)
