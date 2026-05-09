#!/usr/bin/env python3
"""
检查dev表结构
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

def check_table(conn):
    """检查表结构和数据"""
    with conn.cursor() as cursor:
        # 检查表结构
        sql = "DESCRIBE dev"
        cursor.execute(sql)
        columns = cursor.fetchall()
        print("\n📋 dev表字段:")
        for c in columns:
            print(f"  {c.get('Field')}")
        
        # 查询数据
        print("\n📊 dev表数据:")
        sql = "SELECT * FROM dev"
        cursor.execute(sql)
        rows = cursor.fetchall()
        for i, r in enumerate(rows):
            print(f"  第{i}行: {dict(r)}")

def main():
    print("="*60)
    print("检查dev表")
    print("="*60)
    
    conn = connect_db()
    if not conn:
        return
    
    check_table(conn)
    
    conn.close()

if __name__ == '__main__':
    main()
