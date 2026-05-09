#!/usr/bin/env python3
"""
测试后端 API 发送空配置的功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def login():
    url = f"{BASE_URL}/login"
    data = {"username": "admin", "password": "1"}
    response = requests.post(url, json=data)
    print(f"Login status: {response.status_code}")
    res = response.json()
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return res['data']['token']

def test_send_empty_config(token):
    print("=" * 80)
    print("测试后端 API 发送空配置")
    print("=" * 80)
    
    url = f"{BASE_URL}/sendcod/data-config"
    headers = {"Authorization": f"Bearer {token}"}
    
    data = {
        "devSerial": "A1B2C3D4",
        "entries": []
    }
    
    print(f"\n发送请求到：{url}")
    print(f"请求数据：{json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"\n响应状态码：{response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"响应内容：{json.dumps(result, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应内容：{response.text}")
            print("\n✅ 请求发送成功！")
            print("现在检查模拟器终端，看看有没有收到 040000 的空配置！")
        else:
            print(f"\n❌ 请求失败！状态码：{response.status_code}")
            print(f"响应内容：{response.text}")
            
    except Exception as e:
        print(f"\n❌ 发送请求异常：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    token = login()
    time.sleep(1)
    test_send_empty_config(token)
