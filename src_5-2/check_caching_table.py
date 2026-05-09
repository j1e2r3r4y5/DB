#!/usr/bin/env python3
"""
检查caching表
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

def check_caching(conn):
    """检查caching表"""
    with conn.cursor() as cursor:
        # 检查caching表结构
        print("\n📋 caching表字段:")
        sql = "DESCRIBE caching"
        cursor.execute(sql)
        columns = cursor.fetchall()
        for c in columns:
            print(f"  {c.get('Field')}")
        
        # 查询caching表
        print(f"\n📊 caching表数据:")
        sql = "SELECT * FROM caching WHERE dev_ID = 30"
        cursor.execute(sql)
        variables = cursor.fetchall()
        print(f"  共有 {len(variables)} 个变量")
        for v in variables:
            print(f"  变量{v.get('Var_name')}: modbus_type={v.get('modbus_type')}, modbus_addr={v.get('modbus_addr')}")

def main():
    print("="*60)
    print("检查caching表")
    print("="*60)
    
    conn = connect_db()
    if not conn:
        return
    
    check_caching(conn)
    
    conn.close()

if __name__ == '__main__':
    main()
