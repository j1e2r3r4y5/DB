#!/usr/bin/env python3
"""
检查variables表详细信息
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

def check_variables(conn):
    """检查variables表"""
    with conn.cursor() as cursor:
        # 检查variables表
        sql = "DESCRIBE variables"
        cursor.execute(sql)
        columns = cursor.fetchall()
        print("\n📋 variables表字段:")
        for c in columns:
            print(f"  {c.get('Field')}")
        
        # 查询variables表数据
        print("\n📊 variables表数据:")
        sql = "SELECT * FROM variables WHERE dev_ID = 30"
        cursor.execute(sql)
        variables = cursor.fetchall()
        for v in variables:
            var_name = v.get('Var_name')
            print(f"  变量{var_name}: ID={v.get('Id')}, DevID={v.get('dev_ID')}")

def main():
    print("="*60)
    print("检查variables表")
    print("="*60)
    
    conn = connect_db()
    if not conn:
        return
    
    check_variables(conn)
    
    conn.close()

if __name__ == '__main__':
    main()
