#!/usr/bin/env python3
"""
手动同步变量表到缓存表，并设置Changeflag
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

def sync_variables_to_cache(conn):
    """同步变量到缓存表"""
    with conn.cursor() as cursor:
        # 1. 获取variables表中dev_ID=30的所有变量
        sql = "SELECT * FROM variables WHERE dev_ID = 30"
        cursor.execute(sql)
        variables = cursor.fetchall()
        print(f"📊 获取到 {len(variables)} 个变量")
        
        # 2. 清空缓存表中dev_ID=30的记录
        sql_del = "DELETE FROM caching WHERE dev_ID = 30"
        cursor.execute(sql_del)
        print(f"✅ 清空缓存表，删除了 {cursor.rowcount} 条记录")
        
        # 3. 把变量复制到缓存表
        for v in variables:
            # 构建插入语句
            columns = ', '.join(v.keys())
            placeholders = ', '.join(['%s'] * len(v))
            sql_ins = f"INSERT INTO caching ({columns}) VALUES ({placeholders})"
            cursor.execute(sql_ins, list(v.values()))
        
        conn.commit()
        print(f"✅ 同步了 {len(variables)} 个变量到缓存表")
        
        # 4. 设置Changeflag=1
        sql_update = "UPDATE dev SET Changeflag = 1 WHERE id = 30"
        cursor.execute(sql_update)
        conn.commit()
        print(f"✅ 设置设备的Changeflag=1")

def main():
    print("="*60)
    print("手动同步变量到缓存表")
    print("="*60)
    
    conn = connect_db()
    if not conn:
        return
    
    sync_variables_to_cache(conn)
    
    conn.close()
    print("\n✅ 同步完成！现在刷新前端应该能看到正确的变量配置了！")

if __name__ == '__main__':
    main()
