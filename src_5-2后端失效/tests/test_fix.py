import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_header(text):
    print("="*80)
    print(text)
    print("="*80)

def login():
    url = f"{BASE_URL}/login"
    data = {"username": "admin", "password": "1"}
    response = requests.post(url, json=data)
    print(f"Login status: {response.status_code}")
    res = response.json()
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return res['data']['token']

def get_device_list(token):
    url = f"{BASE_URL}/get-devicelist"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(url, headers=headers)
    res = response.json()
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return res['data']['devicelist']

def get_variables(token, device_id):
    url = f"{BASE_URL}/getvarbydeviceid"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"device_id": device_id}
    response = requests.post(url, json=data, headers=headers)
    res = response.json()
    print(f"变量列表：{json.dumps(res, indent=2, ensure_ascii=False)}")
    return res['data']['variables']

def send_config(token, dev_serial, start_addr, reg_count):
    url = f"{BASE_URL}/payload"
    headers = {"Authorization": f"Bearer {token}"}
    
    # 构造 payload
    # 0400010104 + start_addr (2 bytes) + count (2 bytes)
    payload_bytes = bytes([
        0x04,
        0x00, 0x01,  # one group
        0x01,        # slave 1
        0x04,        # modbus type 4 (input register)
    ])
    # 加上起始地址
    payload_bytes += start_addr.to_bytes(2, byteorder='big')
    # 加上数量
    payload_bytes += reg_count.to_bytes(2, byteorder='big')
    
    data = {
        "serial": dev_serial,
        "code": payload_bytes.hex().upper()
    }
    
    print(f"下发配置 payload：{payload_bytes.hex()}")
    print(f"发送的数据：{json.dumps(data)}")
    response = requests.post(url, json=data, headers=headers)
    print(f"下发配置 status：{response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"Response text：{response.text}")
    return response

def query_data(token, dev_serial, slave_addr, modbus_type, addr_list):
    url = f"{BASE_URL}/dataquery"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "DevSerial": dev_serial,
        "SlaveAddr": slave_addr,
        "ModbusType": modbus_type,
        "DataAddrs": addr_list
    }
    response = requests.post(url, json=data, headers=headers)
    print(f"数据查询 status：{response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    return response.json()

def main():
    print_header("系统修复验证测试")
    
    print_header("1. 登录")
    token = login()
    print(f"\n获得 Token：{token[:50]}...\n")
    
    print_header("2. 获取设备列表")
    devices = get_device_list(token)
    target_dev = devices[0]
    dev_id = target_dev['id']
    dev_serial = target_dev['serial']
    print(f"目标设备 ID：{dev_id}，序列号：{dev_serial}\n")
    
    print_header("3. 获取变量列表")
    variables = get_variables(token, dev_id)
    
    print_header("4. 下发配置（温度地址 0，湿度地址 1，共 2 个寄存器）")
    send_config(token, dev_serial, 0, 2)
    
    print_header("5. 等待数据上传（35 秒）")
    for i in range(35, 0, -5):
        print(f"等待 {i} 秒...")
        time.sleep(5)
    
    print_header("6. 查询数据")
    query_data(token, dev_serial, 1, 4, [0, 1])
    
    print_header("测试完成！")

if __name__ == "__main__":
    main()
