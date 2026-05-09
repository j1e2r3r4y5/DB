
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def login():
    """先登录获取token"""
    url = f"{BASE_URL}/login"
    payload = {
        "username": "admin",
        "password": "1"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            print("✅ 登录成功")
            print(f"登录响应: {json.dumps(data, indent=2)}")
            return data.get("data", {}).get("token")
        else:
            print(f"❌ 登录失败: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录异常: {e}")
        return None

def down_payload(token, serial, code):
    """下发配置"""
    url = f"{BASE_URL}/payload"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    payload = {
        "serial": serial,
        "code": code
    }
    print(f"📤 下发配置: serial={serial}, code={code}")
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("✅ 下发成功")
            print(f"响应: {response.text}")
            return True
        else:
            print(f"❌ 下发失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 下发异常: {e}")
        return False

if __name__ == "__main__":
    # 1. 先登录
    token = login()
    if not token:
        exit(1)
    
    # 2. 下发配置 - 使用你提供的正确配置
    # 04 00 01 01 04 00 00 00 02
    # 去掉空格后的十六进制字符串
    code = "040001010400000002"
    serial = "A1B2C3D4"
    
    print(f"\n{'='*50}")
    print(f"测试下发数据配置")
    print(f"{'='*50}")
    down_payload(token, serial, code)
    
    print("\n✅ 测试完成！")
    print("请查看后端和模拟器的日志...")
