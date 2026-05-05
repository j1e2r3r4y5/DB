#!/usr/bin/env python3
import requests
import json

BASE_URL = 'http://127.0.0.1:8000'

def login():
    url = f'{BASE_URL}/login'
    payload = {'username': 'admin', 'password': '1'}
    response = requests.post(url, json=payload)
    result = response.json()
    return result['data']['token']

def getvariables(token):
    url = f'{BASE_URL}/getvariables'
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post(url, headers=headers, json={})
    result = response.json()
    return result['data']['variables'] if result.get('data') and result['data'].get('variables') else []

def build04FunctionCode(variableList):
    if not variableList or len(variableList) == 0:
        return bytes()
    
    # 1. 按站号+分区分组
    groupMap = {}
    for v in variableList:
        key = f'{v["modbusDevice"]}_{v["modbusType"]}'
        if key not in groupMap:
            groupMap[key] = []
        groupMap[key].append(v)
    
    # 2. 计算起始地址/长度
    instructions = []
    for group in groupMap.values():
        addrs = [int(v['modbusAddr']) for v in group if v.get('modbusAddr') is not None]
        if len(addrs) == 0:
            continue
        addrs.sort()
        minAddr = addrs[0]
        maxAddr = addrs[-1]
        length = maxAddr - minAddr + 1
        modbusDevice = int(group[0]['modbusDevice']) if group[0].get('modbusDevice') is not None else 1
        modbusType = int(group[0]['modbusType']) if group[0].get('modbusType') is not None else 0
        instructions.append({'device': modbusDevice, 'type': modbusType, 'addr': minAddr, 'len': length})
    
    if len(instructions) == 0:
        return bytes()
    
    # 3. 数据包拼接
    buffer = bytearray()
    buffer.append(0x04)  # 功能码
    
    dataCount = len(instructions)
    buffer.append((dataCount >> 8) & 0xFF)
    buffer.append(dataCount & 0xFF)
    
    for ins in instructions:
        buffer.append(ins['device'] & 0xFF)
        buffer.append(ins['type'] & 0xFF)
        buffer.append((ins['addr'] >> 8) & 0xFF)
        buffer.append(ins['addr'] & 0xFF)
        buffer.append((ins['len'] >> 8) & 0xFF)
        buffer.append(ins['len'] & 0xFF)
    
    return bytes(buffer)

def downpayload(token, serial, code):
    url = f'{BASE_URL}/payload'
    headers = {'Authorization': f'Bearer {token}'}
    payload = {'serial': serial, 'code': code}
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def main():
    print('=' * 60)
    print('📤 下发数据配置给模拟器')
    print('=' * 60)
    
    # 1. 登录
    token = login()
    print('✅ 登录成功')
    
    # 2. 获取变量
    variables = getvariables(token)
    print(f'📋 获取到 {len(variables)} 个变量')
    
    # 3. 过滤出我们刚添加的设备 30 的变量
    deviceVars = [v for v in variables if str(v.get('devID')) == '30']
    print(f'📌 设备 30 有 {len(deviceVars)} 个变量')
    
    for v in deviceVars:
        print(f'   - {v["varName"]}: 站号={v["modbusDevice"]}, 分区={v["modbusType"]}, 地址={v["modbusAddr"]}')
    
    # 4. 构建04功能码
    codeBytes = build04FunctionCode(deviceVars)
    hexCode = codeBytes.hex().upper()
    print(f'\n📡 生成的04功能码: {hexCode}')
    
    # 5. 下发配置
    result = downpayload(token, 'A1B2C3D4', hexCode)
    print(f'✅ 下发结果: {json.dumps(result, indent=2, ensure_ascii=False)}')
    
    print('\n' + '=' * 60)
    print('✨ 配置下发完成！')
    print('=' * 60)
    print('\n📋 接下来：')
    print('1. 等待模拟器轮询数据（约30秒）')
    print('2. 查看 InfluxDB 中的数据')
    print('3. 在前端"查看数据"页面验证所有变量')

if __name__ == '__main__':
    main()
