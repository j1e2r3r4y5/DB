#!/usr/bin/env python3
"""
连接MySQL数据库查看和更新变量配置
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

def check_table_structure(conn):
    """查看表结构"""
    with conn.cursor() as cursor:
        sql = "DESCRIBE variables"
        cursor.execute(sql)
        columns = cursor.fetchall()
        print("\n📋 variables 表结构:")
        print("="*80)
        for col in columns:
            print(f"{col.get('Field'):<30} {col.get('Type')}")
        print("="*80)

def get_variables(conn):
    """获取所有变量"""
    with conn.cursor() as cursor:
        sql = "SELECT * FROM variables"
        cursor.execute(sql)
        variables = cursor.fetchall()
        print(f"\n📊 当前共有 {len(variables)} 个变量:")
        if variables:
            # 打印第一条数据的键
            print("\n🔑 字段名:")
            first = variables[0]
            print(", ".join(first.keys()))
            
            print("\n📊 详细数据:")
            for idx, v in enumerate(variables):
                print(f"\n变量 #{idx+1}:")
                for k, val in v.items():
                    print(f"  {k}: {val}")

def main():
    print("="*60)
    print("检查和更新数据库变量配置")
    print("="*60)
    
    conn = connect_db()
    if not conn:
        return
    
    check_table_structure(conn)
    get_variables(conn)
    
    conn.close()

if __name__ == '__main__':
    main()
