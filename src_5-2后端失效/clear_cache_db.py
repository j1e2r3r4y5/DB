#!/usr/bin/env python3
"""
清空缓存表，让后端重新同步
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

def clear_cache(conn):
    """清空缓存表"""
    with conn.cursor() as cursor:
        # 清空caching表
        sql = "DELETE FROM caching WHERE dev_ID = 30"
        cursor.execute(sql)
        conn.commit()
        print(f"✅ 清空了dev_ID=30的缓存记录，共删除 {cursor.rowcount} 条")

def main():
    print("="*60)
    print("清空缓存表，让后端重新同步")
    print("="*60)
    
    conn = connect_db()
    if not conn:
        return
    
    clear_cache(conn)
    
    conn.close()
    print("\n✅ 缓存已清空，请等待后端自动同步或重启后端！")

if __name__ == '__main__':
    main()
