#!/usr/bin/env python3
"""
检查caching表中变量2,3,4,6,7,8的配置
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
    """检查caching表"""
    with conn.cursor() as cursor:
        sql = "SELECT * FROM caching WHERE dev_ID = 30 AND Var_name IN ('2','3','4','6','7','8')"
        cursor.execute(sql)
        variables = cursor.fetchall()
        print(f"\n📊 查询到 {len(variables)} 个变量")
        for v in variables:
            print("\n" + "="*80)
            for k, val in v.items():
                print(f"{k}: {val}")

def main():
    print("="*60)
    print("检查caching表中变量2,3,4,6,7,8的配置")
    print("="*60)
    
    conn = connect_db()
    if not conn:
        return
    
    check_variables(conn)
    
    conn.close()

if __name__ == '__main__':
    main()
