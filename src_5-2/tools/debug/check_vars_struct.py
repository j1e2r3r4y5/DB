#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def login():
    url = f"{BASE_URL}/login"
    data = {"username": "admin", "password": "1"}
    response = requests.post(url, json=data)
    result = response.json()
    return result['data']['token']

def get_device_list(token):
    url = f"{BASE_URL}/get-devicelist"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers)
    result = response.json()
    return result['data']['devicelist'] or []

def get_variables(token, dev_id):
    url = f"{BASE_URL}/getvarbydeviceid"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"device_id": dev_id}
    response = requests.post(url, json=data, headers=headers)
    result = response.json()
    print("getvariables 完整返回:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

token = login()
devices = get_device_list(token)
if devices:
    dev_id = devices[0]['id']
    variables = get_variables(token, dev_id)
