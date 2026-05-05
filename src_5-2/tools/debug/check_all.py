import requests
import json
import sys
import time
import pymysql

BASE_URL = "http://localhost:8000"

def print_header(text):
    print("\n" + "="*80)
    print(text)
    print("="*80)

def login():
    url = f"{BASE_URL}/login"
    data = {"username": "admin", "password": "1"}
    response = requests.post(url, json=data)
    return response.json()['data']['token']

def query_mysql_variables():
    try:
        connection = pymysql.connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            password='123456',
            database='device',
            charset='utf8mb4'
        )
        
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 查询所有变量
            print("\n--- MySQL variables 表中的所有变量 ---")
            cursor.execute("SELECT * FROM variables")
            all_vars = cursor.fetchall()
            print(f"共 {len(all_vars)} 个变量:")
            for v in all_vars:
                print(json.dumps(v, indent=2, ensure_ascii=False))
            
            # 查询设备表
            print("\n--- MySQL device 表 ---")
            cursor.execute("SELECT * FROM dev")
            devices = cursor.fetchall()
            print(f"共 {len(devices)} 个设备:")
            for d in devices:
                print(d)
            
            # 查询缓存表
            print("\n--- MySQL caching 表 ---")
            cursor.execute("SELECT * FROM caching")
            caches = cursor.fetchall()
            print(f"共 {len(caches)} 个缓存记录:")
            for c in caches:
                print(json.dumps(c, indent=2, ensure_ascii=False))
                
        connection.close()
    except Exception as e:
        print(f"MySQL 连接失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    print_header("开始完整问题诊断")
    
    print_header("1. 查询 API")
    token = login()
    print("登录成功")
    
    print_header("2. 查询 MySQL 数据库")
    query_mysql_variables()
    
    print_header("3. 查询 API 中的变量")
    url = f"{BASE_URL}/getvarbydeviceid"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"device_id": 28}
    response = requests.post(url, json=data, headers=headers)
    print("变量查询响应:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    print_header("诊断完成")

if __name__ == "__main__":
    main()
