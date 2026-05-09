#!/usr/bin/env python3
"""
检查数据库中的设备信息
"""

import pymysql
from pymysql.cursors import DictCursor

# 数据库配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '123456',
    'db': 'device',
    'charset': 'utf8mb4',
    'cursorclass': DictCursor
}

def connect_db():
    """连接数据库"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        print("✅ 数据库连接成功")
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None

def check_devices(conn):
    """检查设备信息"""
    with conn.cursor() as cursor:
        # 获取所有设备
        sql = "SELECT * FROM dev"
        cursor.execute(sql)
        devices = cursor.fetchall()
        print(f"📊 共有 {len(devices)} 个设备")
        for d in devices:
            print(f"  设备ID: {d.get('id')}, 序列号: {d.get('Devserial')}")

def main():
    print("="*60)
    print("检查设备信息")
    print("="*60)
    
    conn = connect_db()
    if not conn:
        return
    
    check_devices(conn)
    
    conn.close()

if __name__ == '__main__':
    main()
