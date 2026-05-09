#!/usr/bin/env python3
"""
强制清空并重新同步caching表
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

def clear_and_resync(conn):
    """清空并重新同步caching表"""
    with conn.cursor() as cursor:
        # 1. 清空caching表
        print("\n📝 清空caching表...")
        sql = "DELETE FROM caching WHERE dev_ID = 30"
        cursor.execute(sql)
        print(f"   已删除 {cursor.rowcount} 条记录")
        
        # 2. 从variables表复制
        print("\n📝 从variables表复制到caching表...")
        sql = """
        INSERT INTO caching 
        (dev_ID, Var_name, Data_type, modbus_type, modbus_device, modbus_addr, 
         data_len, string_len, Decimal_digits, scale, offset, reg_count, 
         byte_order, unit, Changeflag)
        SELECT 
            dev_ID, Var_name, Data_type, modbus_type, modbus_device, modbus_addr,
            data_len, string_len, Decimal_digits, scale, offset, reg_count,
            byte_order, unit, 1 AS Changeflag
        FROM variables 
        WHERE dev_ID = 30
        """
        cursor.execute(sql)
        print(f"   已插入 {cursor.rowcount} 条记录")
        
        # 3. 验证
        print("\n✅ 验证caching表数据...")
        sql = "SELECT Var_name, modbus_type, modbus_addr FROM caching WHERE dev_ID = 30 ORDER BY CAST(Var_name AS UNSIGNED)"
        cursor.execute(sql)
        variables = cursor.fetchall()
        for v in variables:
            print(f"   变量{v['Var_name']}: type={v['modbus_type']}, addr={v['modbus_addr']}")
        
        conn.commit()
        print("\n✅ 完成！")

def main():
    print("="*60)
    print("强制清空并重新同步caching表")
    print("="*60)
    
    conn = connect_db()
    if not conn:
        return
    
    clear_and_resync(conn)
    
    conn.close()

if __name__ == '__main__':
    main()
