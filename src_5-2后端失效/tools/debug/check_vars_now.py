
import requests
import json

BASE_URL = "http://localhost:8000"

# Step 1: Login
login_url = f"{BASE_URL}/api/v1/login"
login_payload = {"username": "admin", "password": "1"}
login_resp = requests.post(login_url, json=login_payload)
print("Login Response:", login_resp.status_code)
print(login_resp.text)

login_data = login_resp.json()
token = login_data.get("data", {}).get("token")
print("Token:", token)

# Step 2: Get Variables
headers = {"Authorization": f"Bearer {token}"}
var_url = f"{BASE_URL}/api/v1/getvariables"
var_resp = requests.post(var_url, headers=headers, json={})
print("\nVariables Response:", var_resp.status_code)
print(json.dumps(var_resp.json(), indent=2, ensure_ascii=False))
