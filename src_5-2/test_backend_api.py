
import requests
import json

# First, we need to login to get the token
login_url = "http://127.0.0.1:8000/login"
login_data = {"username": "admin", "password": "1"}
response = requests.post(login_url, json=login_data)
print(f"Login response: {response.status_code}")
response_json = response.json()
print(f"Login result: {json.dumps(response_json, indent=4)}")

token = response_json["data"]["token"]
print(f"Got token: {token}")

# Now call the payload API!
payload_url = "http://127.0.0.1:8000/payload"
payload_data = {"serial": "A1B2C3D4", "code": "040001010400000002"}
headers = {"Authorization": f"Bearer {token}"}
print(f"\nCalling payload API: {payload_url}")
print(f"Headers: {headers}")
print(f"Data: {payload_data}")

response = requests.post(payload_url, json=payload_data, headers=headers)
print(f"Payload response status: {response.status_code}")
print(f"Response: {response.text}")
print("Done!")

